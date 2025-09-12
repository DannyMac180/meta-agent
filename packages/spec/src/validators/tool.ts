import { z } from "zod";
import { ToolKindEnum } from "../enums";

export const ToolSpecSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("http"), allowDomains: z.array(z.string().url()) }),
  z.object({ kind: z.literal("web-search"), provider: z.string().optional() }),
  z.object({ kind: z.literal("vector"), index: z.string().min(1) }),
  z.object({ kind: z.literal("code-interpreter"), timeoutSec: z.number().int().min(1).max(300).optional(), sandbox: z.enum(["node18"]).optional() }),
]);

export const AnyToolKind = z.enum(ToolKindEnum);

export type ToolSpecInput = z.input<typeof ToolSpecSchema>;
export type ToolSpecOutput = z.output<typeof ToolSpecSchema>;
