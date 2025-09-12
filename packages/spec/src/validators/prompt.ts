import { z } from "zod";

export const PromptTemplateSchema = z.object({
  template: z.string().min(1).max(8000),
});

export type PromptTemplateInput = z.input<typeof PromptTemplateSchema>;
export type PromptTemplateOutput = z.output<typeof PromptTemplateSchema>;
