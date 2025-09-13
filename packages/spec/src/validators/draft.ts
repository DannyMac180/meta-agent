import { z } from "zod";
import { ulid, isoDateString } from "../_utils/refinements";
import { AgentSpecSchema } from "./agent";

export const SpecStatusEnum = ["DRAFT", "PUBLISHED"] as const;

export const SpecDraftSchema = z.object({
  id: ulid(),
  title: z.string().min(1, "Title is required"),
  isDraft: z.boolean().default(true),
  status: z.enum(SpecStatusEnum).default("DRAFT"),
  payload: AgentSpecSchema.partial(),
  createdAt: isoDateString(),
  updatedAt: isoDateString(),
});

export type SpecDraftInput = z.input<typeof SpecDraftSchema>;
export type SpecDraftOutput = z.output<typeof SpecDraftSchema>;
