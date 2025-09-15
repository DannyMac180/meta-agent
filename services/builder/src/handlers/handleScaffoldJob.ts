import { db, specDrafts, builderArtifacts, setAppUser } from "@metaagent/db";
import { and, eq } from "drizzle-orm";
import fs from "fs-extra";
import path from "node:path";
import { artifactKey, putObjectStream } from "@metaagent/object-storage";
import { scaffoldProject } from "./scaffoldProject.js";
import type { BuilderScaffoldJob, BuilderScaffoldResult } from "@metaagent/queue";

export async function handleBuilderScaffold(job: BuilderScaffoldJob): Promise<BuilderScaffoldResult> {
  const bucket = process.env.BUILDER_BUCKET || "metaagent-artifacts";
  const buildId = job.buildId ?? `b-${Date.now()}`;

  await setAppUser(job.userId);

  const draftRows = await db
    .select()
    .from(specDrafts)
    .where(and(eq(specDrafts.id, job.draftId), eq(specDrafts.ownerUserId, job.userId)))
    .limit(1);
  const draft = draftRows[0];
  if (!draft) throw new Error(`Draft not found: ${job.draftId}`);

  // Idempotency: return existing artifact for scaffold step if present
  const existingRows = await db
    .select()
    .from(builderArtifacts)
    .where(and(eq(builderArtifacts.draftId, job.draftId), eq(builderArtifacts.step, "scaffold")))
    .limit(1);
  const existing = existingRows[0];
  if (existing) {
    return {
      artifactId: existing.id,
      bucket: existing.bucket,
      key: (existing as any).objectKey,
      sizeBytes: (existing as any).sizeBytes as number | undefined,
      etag: (existing as any).etag as string | undefined,
    };
  }

  const templateId = draft.templateId ?? "chatbot";
  const { zipPath } = await scaffoldProject({
    templateId,
    draft: { title: draft.title, payload: draft.spec },
    buildId,
  });

  const key = artifactKey({ userId: job.userId, draftId: job.draftId, buildId, filename: path.basename(zipPath) });
  const stat = await fs.stat(zipPath);
  const body = await fs.readFile(zipPath);
  const { etag } = await putObjectStream({ bucket, key, body, contentType: "application/zip" });

  const inserted = await db
    .insert(builderArtifacts)
    .values({
      draftId: job.draftId,
      buildId,
      step: "scaffold",
      bucket,
      objectKey: key,
      sizeBytes: stat.size,
      etag: etag ?? null,
    })
    .returning();

  return {
    artifactId: inserted[0].id,
    bucket,
    key,
    sizeBytes: stat.size,
    etag: etag ?? undefined,
  };
}
