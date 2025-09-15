import { z } from "zod";

// Tool definition interface as specified in the oracle plan
export interface ToolDefinition {
  name: 'http' | 'webSearch' | 'vector';
  description: string;
  inputSchema: z.ZodTypeAny;
  outputSchema: z.ZodTypeAny;
}

// HTTP Tool Definition
export const HTTP_INPUT_SCHEMA = z.object({
  url: z.string().url(),
  method: z.enum(['GET', 'POST', 'PUT', 'DELETE']).default('GET'),
  headers: z.record(z.string(), z.string()).optional(),
  body: z.unknown().optional(),
});

export const HTTP_OUTPUT_SCHEMA = z.object({
  status: z.number().int(),
  headers: z.record(z.string(), z.string()),
  body: z.string(),
});

export const HTTP_TOOL_DEF: ToolDefinition = {
  name: 'http',
  description: 'Make HTTP requests to allow-listed domains',
  inputSchema: HTTP_INPUT_SCHEMA,
  outputSchema: HTTP_OUTPUT_SCHEMA,
};

// Web Search Tool Definition
export const WEBSEARCH_INPUT_SCHEMA = z.object({
  query: z.string().min(1),
  numResults: z.number().int().min(1).max(20).default(5),
});

export const WEBSEARCH_OUTPUT_SCHEMA = z.object({
  results: z.array(z.object({
    title: z.string(),
    url: z.string().url(),
    snippet: z.string(),
  })),
});

export const WEBSEARCH_TOOL_DEF: ToolDefinition = {
  name: 'webSearch',
  description: 'Search the web using Serper.dev API',
  inputSchema: WEBSEARCH_INPUT_SCHEMA,
  outputSchema: WEBSEARCH_OUTPUT_SCHEMA,
};

// Vector Tool Definition
export const VECTOR_INPUT_SCHEMA = z.object({
  query: z.string().min(1),
  k: z.number().int().min(1).max(50).default(5),
});

export const VECTOR_OUTPUT_SCHEMA = z.object({
  results: z.array(z.object({
    id: z.string(),
    text: z.string(),
    score: z.number(),
    meta: z.record(z.string(), z.unknown()).optional(),
  })),
});

export const VECTOR_TOOL_DEF: ToolDefinition = {
  name: 'vector',
  description: 'Query vector database using semantic similarity',
  inputSchema: VECTOR_INPUT_SCHEMA,
  outputSchema: VECTOR_OUTPUT_SCHEMA,
};

// Export all tool definitions
export const ALL_TOOL_DEFINITIONS = [
  HTTP_TOOL_DEF,
  WEBSEARCH_TOOL_DEF,
  VECTOR_TOOL_DEF,
] as const;

// Helper to convert to OpenAI function format
export function toOpenAIFunction(toolDef: ToolDefinition) {
  // For now, return a simplified version - will implement proper schema conversion later
  const baseParams = {
    type: 'object' as const,
    properties: {} as Record<string, any>,
    required: [] as string[],
  };

  // Basic parameter definitions based on tool type
  if (toolDef.name === 'http') {
    baseParams.properties = {
      url: { type: 'string', format: 'uri' },
      method: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE'] },
      headers: { type: 'object' },
      body: {}
    };
    baseParams.required = ['url'];
  } else if (toolDef.name === 'webSearch') {
    baseParams.properties = {
      query: { type: 'string' },
      numResults: { type: 'number', minimum: 1, maximum: 20, default: 5 }
    };
    baseParams.required = ['query'];
  } else if (toolDef.name === 'vector') {
    baseParams.properties = {
      query: { type: 'string' },
      k: { type: 'number', minimum: 1, maximum: 50, default: 5 }
    };
    baseParams.required = ['query'];
  }

  return {
    name: toolDef.name,
    description: toolDef.description,
    parameters: baseParams,
  };
}
