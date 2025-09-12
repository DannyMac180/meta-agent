export const ProviderEnum = ["openai", "anthropic", "azure", "local"] as const;
export type Provider = typeof ProviderEnum[number];

export const VariableTypeEnum = ["string", "number", "boolean", "enum", "json"] as const;
export type VariableType = typeof VariableTypeEnum[number];

export const ToolKindEnum = ["http", "web-search", "vector", "code-interpreter"] as const;
export type ToolKind = typeof ToolKindEnum[number];

export const SpecVersionEnum = ["0.1.0"] as const;
export type SpecVersion = typeof SpecVersionEnum[number];
