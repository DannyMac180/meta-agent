import type { SpecVersion } from "../enums.js";
import type { Metadata } from "./common";
import type { VariableSpec } from "./variable";
import type { PromptTemplate } from "./prompt";
import type { ModelConfig } from "./model";
import type { ToolSpec } from "./tool";
import type { AcceptanceEval } from "./eval";

export type RuntimeLimits = {
  timeoutSec?: number; // 1-300
  budgetUsd?: number; // >= 0
};

export type AgentSpec = {
  specVersion: SpecVersion;
  meta: Metadata;
  variables: VariableSpec[];
  prompt: PromptTemplate;
  model: ModelConfig;
  tools?: ToolSpec[];
  limits?: RuntimeLimits;
  acceptanceEvals?: AcceptanceEval[];
};
