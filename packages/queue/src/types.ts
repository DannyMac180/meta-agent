export interface AgentExecData {
  runId: string;
  prompt: string;
  context?: unknown;
}

export interface AgentExecResult {
  runId: string;
  output: string;
  logs?: string[];
}
