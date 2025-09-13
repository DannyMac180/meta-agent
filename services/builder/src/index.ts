import Fastify from "fastify";
import dotenv from "dotenv";
import { logger } from "@metaagent/toolkit";
import { enqueueAgentExec, createDraftAutosaveWorker } from "@metaagent/queue";
import { db, specDrafts, setAppUser } from "@metaagent/db";
import { eq, and } from "drizzle-orm";

dotenv.config();

const app = Fastify({ logger });

app.get("/healthz", async () => ({ status: "ok" }));
app.get("/readyz", async () => ({ status: "ready" }));

app.post("/jobs/demo", async () => {
  const runId = `demo-${Date.now()}`;
  await enqueueAgentExec({ runId, prompt: "Hello from builder" });
  return { enqueued: true, runId };
});

// Start Draft Autosave Worker
createDraftAutosaveWorker(async ({ userId, draft }) => {
  await setAppUser(userId);
  const now = new Date();

  if (draft.id) {
    const updated = await db
      .update(specDrafts)
      .set({
        title: draft.title,
        name: draft.title,
        spec: draft.payload,
        templateId: draft.templateId ?? null,
        isDraft: draft.isDraft ?? true,
        status: draft.status ?? 'DRAFT',
        updatedAt: now,
      })
      .where(and(eq(specDrafts.id, draft.id), eq(specDrafts.ownerUserId, userId)))
      .returning();

    if (updated.length > 0) {
      return { id: updated[0].id, updatedAt: updated[0].updatedAt?.toISOString() ?? now.toISOString() };
    }
  }

  const created = await db
    .insert(specDrafts)
    .values({
      ownerUserId: userId,
      title: draft.title,
      name: draft.title,
      spec: draft.payload,
      templateId: draft.templateId ?? null,
      isDraft: draft.isDraft ?? true,
      status: draft.status ?? 'DRAFT',
      tags: [],
      createdAt: now,
      updatedAt: now,
    })
    .returning();

  return { id: created[0].id, updatedAt: created[0].updatedAt?.toISOString() ?? now.toISOString() };
});

const port = Number(process.env.BUILDER_PORT ?? 3101);
app.listen({ port, host: "0.0.0.0" }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});

