import { z } from "zod";

export const CodeToolInputSchema = z.object({
  code: z.string().min(1, "Code cannot be empty").max(100000, "Code too large"),
  packages: z.array(z.string()).optional().default([]),
  timeoutMs: z.number().min(1000).max(300000).optional().default(8000),
  memMb: z.number().min(64).max(1024).optional().default(256),
  network: z.boolean().optional().default(false)
});

export type CodeToolInput = z.infer<typeof CodeToolInputSchema>;

export interface CodeExecutionResult {
  success: boolean;
  exitCode?: number;
  stdout: string;
  stderr: string;
  executionTimeMs: number;
  error?: string;
  truncated?: {
    stdout?: boolean;
    stderr?: boolean;
  };
}

export interface DockerExecutionOptions {
  imageTag: string;
  timeoutMs: number;
  memMb: number;
  network: boolean;
  allowedPackages?: string[];
}

export interface ContainerInfo {
  containerId: string;
  startedAt: Date;
  timeoutMs: number;
}
