import type { ToolKind } from "../enums";

export type ToolSpec =
  | { kind: "http"; allowDomains: string[] }
  | { kind: "web-search"; provider?: string }
  | { kind: "vector"; index: string }
  | { kind: "code-interpreter"; timeoutSec?: number; sandbox?: "node18" };

export type AnyToolSpec = { kind: ToolKind } & Record<string, unknown>;
