import { eq, and, desc } from 'drizzle-orm';
import { db, specDrafts, setAppUser } from '@metaagent/db';
import type { SpecDraftOutput } from '@metaagent/spec';
import { createDraftSpec, isDraftSpec } from '@metaagent/spec';

export interface SaveDraftInput {
  id?: string;
  templateId?: string;
  title: string;
  payload: any;
  isDraft?: boolean;
  status?: 'DRAFT' | 'PUBLISHED';
}

export interface SpecDraftRecord {
  id: string;
  ownerUserId: string;
  templateId: string | null;
  title: string;
  spec: any;
  isDraft: boolean | null;
  status: string | null;
  tags: string[] | null;
  createdAt: Date | null;
  updatedAt: Date | null;
}

export class SpecDraftService {
  constructor(private userId: string) {}

  async saveDraft(input: SaveDraftInput): Promise<SpecDraftOutput> {
    await setAppUser(this.userId);

    // If ID provided, try to update existing draft
    if (input.id) {
      const existing = await db
        .select()
        .from(specDrafts)
        .where(
          and(
            eq(specDrafts.id, input.id),
            eq(specDrafts.ownerUserId, this.userId)
          )
        )
        .limit(1);

      if (existing.length > 0) {
        const [updated] = await db
          .update(specDrafts)
          .set({
            title: input.title,
            spec: input.payload,
            templateId: input.templateId,
            isDraft: input.isDraft ?? true,
            status: input.status ?? 'DRAFT',
            updatedAt: new Date(),
          })
          .where(eq(specDrafts.id, input.id))
          .returning();

        return this.recordToSpecDraft(updated);
      }
    }

    // Create new draft
    const [created] = await db
      .insert(specDrafts)
      .values({
        ownerUserId: this.userId,
        templateId: input.templateId,
        title: input.title,
        name: input.title, // backwards compatibility
        spec: input.payload,
        isDraft: input.isDraft ?? true,
        status: input.status ?? 'DRAFT',
        tags: [],
      })
      .returning();

    return this.recordToSpecDraft(created);
  }

  async getDraft(draftId: string): Promise<SpecDraftOutput | null> {
    await setAppUser(this.userId);

    const [record] = await db
      .select()
      .from(specDrafts)
      .where(
        and(
          eq(specDrafts.id, draftId),
          eq(specDrafts.ownerUserId, this.userId)
        )
      )
      .limit(1);

    return record ? this.recordToSpecDraft(record) : null;
  }

  async listDrafts(options: {
    limit?: number;
    offset?: number;
    status?: 'DRAFT' | 'PUBLISHED';
  } = {}): Promise<SpecDraftOutput[]> {
    await setAppUser(this.userId);

    const { limit = 50, offset = 0, status } = options;

    let query = db
      .select()
      .from(specDrafts)
      .where(eq(specDrafts.ownerUserId, this.userId))
      .orderBy(desc(specDrafts.updatedAt))
      .limit(limit)
      .offset(offset);

    if (status) {
      query = query.where(
        and(
          eq(specDrafts.ownerUserId, this.userId),
          eq(specDrafts.status, status)
        )
      );
    }

    const records = await query;
    return records.map(record => this.recordToSpecDraft(record));
  }

  async deleteDraft(draftId: string): Promise<boolean> {
    await setAppUser(this.userId);

    const result = await db
      .delete(specDrafts)
      .where(
        and(
          eq(specDrafts.id, draftId),
          eq(specDrafts.ownerUserId, this.userId)
        )
      );

    return result.rowCount > 0;
  }

  private recordToSpecDraft(record: SpecDraftRecord): SpecDraftOutput {
    return {
      id: record.id,
      title: record.title,
      isDraft: record.isDraft ?? true,
      status: (record.status as 'DRAFT' | 'PUBLISHED') ?? 'DRAFT',
      payload: record.spec || {},
      createdAt: record.createdAt?.toISOString() ?? new Date().toISOString(),
      updatedAt: record.updatedAt?.toISOString() ?? new Date().toISOString(),
    };
  }
}

// Helper function to create service instance
export function createSpecDraftService(userId: string): SpecDraftService {
  return new SpecDraftService(userId);
}
