import { z } from "zod";
import { SpecVersionEnum } from "../enums.js";
import { isoDateString, kebabCase, ulid } from "../_utils/refinements.js";
import { PromptTemplateSchema } from "./prompt.js";
import { VariableSpecSchema } from "./variable.js";
import { ModelConfigSchema } from "./model.js";
import { ToolSpecSchema } from "./tool.js";
import { AcceptanceEvalArraySchema } from "./eval.js";

export const MetadataSchema = z.object({
  id: ulid(),
  name: kebabCase(),
  description: z.string().optional(),
  version: z.string().min(1),
  createdAt: isoDateString(),
  updatedAt: isoDateString(),
  tags: z.array(z.string()).optional(),
});

export const RuntimeLimitsSchema = z.object({
  timeoutSec: z.number().int().min(1).max(300).optional(),
  budgetUsd: z.number().min(0).optional(),
});

export const AgentSpecSchema = z
  .object({
    specVersion: z.enum(SpecVersionEnum),
    meta: MetadataSchema,
    variables: z.array(VariableSpecSchema),
    prompt: PromptTemplateSchema,
    model: ModelConfigSchema,
    tools: z.array(ToolSpecSchema).optional(),
    limits: RuntimeLimitsSchema.optional(),
    acceptanceEvals: AcceptanceEvalArraySchema.optional(),
  })
  .superRefine((val, ctx) => {
    // Ensure prompt references only declared variables
    const varKeys = new Set(val.variables.map((v) => v.key));
    const placeholderRegex = /{{\s*([a-z0-9-]+)\s*}}/g;
    const used = new Set<string>();
    for (const match of val.prompt.template.matchAll(placeholderRegex)) {
      used.add(match[1]);
    }
    for (const key of used) {
      if (!varKeys.has(key)) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, message: `undeclared variable: ${key}`, path: ["prompt", "template"] });
      }
    }
  });

export type AgentSpecInput = z.input<typeof AgentSpecSchema>;
export type AgentSpecOutput = z.output<typeof AgentSpecSchema>;
