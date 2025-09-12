import type { Provider } from "../enums";

export type ModelConfig = {
  provider: Provider;
  model: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
};
