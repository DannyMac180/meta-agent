import { db, specDrafts, setAppUser } from "@metaagent/db";
import { and, eq } from "drizzle-orm";
import type { DraftAutosaveData, DraftAutosaveResult } from "@metaagent/queue";

export async function handleDraftAutosave({ userId, draft }: DraftAutosaveData): Promise<DraftAutosaveResult> {
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
}
