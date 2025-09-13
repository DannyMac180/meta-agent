import type { SpecDraftOutput } from "@metaagent/spec";

export type InterviewNode =
  | {
      type: "question";
      id: string;
      prompt: string;
      field: string; // maps to spec field path like "meta.name"
      inputType: "text" | "textarea" | "select" | "number";
      options?: string[]; // for select type
      validate?: (value: any) => boolean;
      required?: boolean;
    }
  | {
      type: "branch";
      id: string;
      condition: (answers: Record<string, any>) => boolean;
      next: string;
    }
  | {
      type: "end";
      id: "end";
    };

export interface InterviewScript {
  id: string;
  name: string;
  nodes: Record<string, InterviewNode>;
  startNodeId: string;
}

export interface InterviewState {
  answers: Record<string, any>;
  currentNodeId: string;
  specDraft: SpecDraftOutput;
  visitedNodes: string[];
}

export interface InterviewEvent {
  type: "node_visited" | "answer_changed" | "interview_completed";
  nodeId: string;
  timestamp: number;
  data?: any;
}

export interface RunNodeResult {
  nextNodeId: string | null;
  updatedState: InterviewState;
  events: InterviewEvent[];
}
