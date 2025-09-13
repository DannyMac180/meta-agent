import type { AgentSpec } from "./agent";

export enum SpecStatus {
  DRAFT = "DRAFT",
  PUBLISHED = "PUBLISHED"
}

export type SpecDraft = {
  id: string;
  title: string;
  isDraft: boolean;
  status: SpecStatus;
  payload: Partial<AgentSpec>;
  createdAt: string;
  updatedAt: string;
};
