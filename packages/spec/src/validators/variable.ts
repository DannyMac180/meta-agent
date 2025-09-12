import { z } from "zod";
import { VariableTypeEnum } from "../enums";
import { kebabCase } from "../_utils/refinements";

export const VariableSpecSchema = z
  .object({
    key: kebabCase(),
    type: z.enum(VariableTypeEnum),
    description: z.string().optional(),
    required: z.boolean().optional(),
    enumValues: z.array(z.string()).optional(),
    default: z.unknown().optional(),
  })
  .superRefine((val, ctx) => {
    if (val.type === "enum" && (!val.enumValues || val.enumValues.length === 0)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "enumValues required when type is 'enum'",
        path: ["enumValues"],
      });
    }
  });

export type VariableSpecInput = z.input<typeof VariableSpecSchema>;
export type VariableSpecOutput = z.output<typeof VariableSpecSchema>;
