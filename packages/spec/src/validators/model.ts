import { z } from "zod";
import { ProviderEnum } from "../enums.js";

export const ModelConfigSchema = z
  .object({
    provider: z.enum(ProviderEnum),
    model: z.string().min(1),
    temperature: z.number().min(0).max(2).optional(),
    maxTokens: z.number().int().positive().optional(),
    topP: z.number().min(0).max(1).optional(),
  })
  .superRefine((val, ctx) => {
    if (val.provider === "openai" && val.maxTokens && val.maxTokens > 16000) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "maxTokens exceeds provider limit (openai)", path: ["maxTokens"] });
    }
  });

export type ModelConfigInput = z.input<typeof ModelConfigSchema>;
export type ModelConfigOutput = z.output<typeof ModelConfigSchema>;
