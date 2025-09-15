import type { VariableType } from "../enums.js";

export type VariableSpec = {
  key: string; // kebab-case
  type: VariableType;
  description?: string;
  required?: boolean;
  // when type === 'enum'
  enumValues?: string[];
  // default value in string form (UI may coerce)
  default?: unknown;
};
