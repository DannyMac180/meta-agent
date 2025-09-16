import { z } from 'zod';

export const GateResultSchema = z.object({
  gate: z.string(),
  passed: z.boolean(),
  duration: z.number(),
  errors: z.array(z.string()).optional(),
  warnings: z.array(z.string()).optional(),
  metadata: z.record(z.string(), z.any()).optional(),
});

export const GateContextSchema = z.object({
  projectPath: z.string(),
  packageJson: z.any(),
  tempDir: z.string(),
});

export const GateRunResultSchema = z.object({
  success: z.boolean(),
  results: z.array(GateResultSchema),
  totalDuration: z.number(),
  failedGate: z.string().optional(),
});

export type GateResult = z.infer<typeof GateResultSchema>;
export type GateContext = z.infer<typeof GateContextSchema>;
export type GateRunResult = z.infer<typeof GateRunResultSchema>;

export interface Gate {
  name: string;
  description: string;
  execute(context: GateContext): Promise<GateResult>;
}

export enum GateType {
  TSC = 'tsc',
  ESLINT = 'eslint',
  VITEST = 'vitest',
  AUDIT = 'audit',
  LICENSE = 'license',
}
