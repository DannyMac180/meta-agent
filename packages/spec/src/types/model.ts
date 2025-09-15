import type { Provider } from "../enums.js";

export type ModelConfig = {
  provider: Provider;
  model: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
};
