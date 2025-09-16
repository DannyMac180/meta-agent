// Re-export tool definitions from spec
export { 
  HTTP_TOOL_DEF,
  WEBSEARCH_TOOL_DEF,
  VECTOR_TOOL_DEF,
  ALL_TOOL_DEFINITIONS,
  toOpenAIFunction
} from '@metaagent/spec';

// TODO: Re-export code tool after workspace dependency resolution
// export { codeTool, codeToolDefinition, CodeTool } from '@metaagent/tools-code';

export const hello = () => "metaagent monorepo ready!";
