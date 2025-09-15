// Re-export tool definitions from spec
export { 
  HTTP_TOOL_DEF,
  WEBSEARCH_TOOL_DEF,
  VECTOR_TOOL_DEF,
  ALL_TOOL_DEFINITIONS,
  toOpenAIFunction
} from '@metaagent/spec';

export const hello = () => "metaagent monorepo ready!";
