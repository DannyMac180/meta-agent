import { z } from "zod";

const pathSchema = z.string().min(1, "path is required");

const StringNotEmptyAssertionSchema = z.object({
  kind: z.literal("string-not-empty"),
  path: pathSchema,
  message: z.string().optional(),
});

const StringContainsAssertionSchema = z.object({
  kind: z.literal("string-contains"),
  path: pathSchema,
  value: z.string(),
  caseSensitive: z.boolean().optional(),
  message: z.string().optional(),
});

const NumberGteAssertionSchema = z.object({
  kind: z.literal("number-gte"),
  path: pathSchema,
  value: z.number(),
  message: z.string().optional(),
});

const NumberLteAssertionSchema = z.object({
  kind: z.literal("number-lte"),
  path: pathSchema,
  value: z.number(),
  message: z.string().optional(),
});

const ArrayMinLengthAssertionSchema = z.object({
  kind: z.literal("array-min-length"),
  path: pathSchema,
  min: z.number().int().min(0),
  message: z.string().optional(),
});

const EqualsAssertionSchema = z.object({
  kind: z.literal("equals"),
  path: pathSchema,
  value: z.union([z.string(), z.number(), z.boolean()]),
  message: z.string().optional(),
});

export const AcceptanceEvalAssertionSchema = z.discriminatedUnion("kind", [
  StringNotEmptyAssertionSchema,
  StringContainsAssertionSchema,
  NumberGteAssertionSchema,
  NumberLteAssertionSchema,
  ArrayMinLengthAssertionSchema,
  EqualsAssertionSchema,
]);

export const AcceptanceEvalSchema = z.object({
  id: z.string().min(1, "id is required"),
  title: z.string().min(1, "title is required"),
  description: z.string().optional(),
  assertions: z.array(AcceptanceEvalAssertionSchema).min(1, "at least one assertion required"),
});

export const AcceptanceEvalArraySchema = z.array(AcceptanceEvalSchema).min(1);

export type AcceptanceEvalInput = z.input<typeof AcceptanceEvalSchema>;
export type AcceptanceEvalOutput = z.output<typeof AcceptanceEvalSchema>;
export type AcceptanceEvalAssertionInput = z.input<typeof AcceptanceEvalAssertionSchema>;
export type AcceptanceEvalAssertionOutput = z.output<typeof AcceptanceEvalAssertionSchema>;
