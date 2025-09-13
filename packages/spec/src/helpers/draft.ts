import { v4 as uuid } from "uuid";
import { SpecDraftSchema, type SpecDraftOutput } from "../validators/draft";
import { SpecStatus } from "../types/draft";

export interface CreateDraftSpecInput {
  title?: string;
  payload?: Partial<any>;
  templateId?: string;
}

export function createDraftSpec(input: CreateDraftSpecInput = {}): SpecDraftOutput {
  const now = new Date().toISOString();
  
  const draft = {
    id: uuid(),
    title: input.title || "Untitled Agent",
    isDraft: true,
    status: "DRAFT" as const,
    payload: input.payload || {},
    createdAt: now,
    updatedAt: now,
  };

  return SpecDraftSchema.parse(draft);
}

export function updateDraftSpec(existing: SpecDraftOutput, updates: Partial<SpecDraftOutput>): SpecDraftOutput {
  const updated = {
    ...existing,
    ...updates,
    updatedAt: new Date().toISOString(),
  };

  return SpecDraftSchema.parse(updated);
}

export function isDraftSpec(obj: unknown): obj is SpecDraftOutput {
  const result = SpecDraftSchema.safeParse(obj);
  return result.success;
}
