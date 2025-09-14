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

export interface DraftAutosaveData {
  userId: string;
  draft: {
    id?: string;
    templateId?: string;
    title: string;
    payload: any;
    isDraft?: boolean;
    status?: 'DRAFT' | 'PUBLISHED';
  };
}

export interface DraftAutosaveResult {
  id: string;
  updatedAt: string;
}
