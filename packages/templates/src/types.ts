import type { SpecDraftOutput, AcceptanceEval } from "@metaagent/spec";
import type { InterviewScript } from "@metaagent/interview";

export interface TemplateMeta {
  id: string;
  name: string;
  description: string;
  category: "chatbot" | "web-automation" | "api-copilot" | "general";
  defaultSpec: SpecDraftOutput;
  interview?: InterviewScript;
  tags?: string[];
  acceptanceEvals?: AcceptanceEval[];
}
