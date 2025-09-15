import { describe, test, expect } from 'vitest';
import { 
  HTTP_TOOL_DEF,
  WEBSEARCH_TOOL_DEF, 
  VECTOR_TOOL_DEF,
  toOpenAIFunction,
  ALL_TOOL_DEFINITIONS
} from '../src/tools/definitions';

describe('Tool Definitions', () => {
  describe('HTTP Tool', () => {
    test('should have correct structure', () => {
      expect(HTTP_TOOL_DEF.name).toBe('http');
      expect(HTTP_TOOL_DEF.description).toBeDefined();
      expect(HTTP_TOOL_DEF.inputSchema).toBeDefined();
      expect(HTTP_TOOL_DEF.outputSchema).toBeDefined();
    });

    test('should validate valid input', () => {
      const validInput = {
        url: 'https://example.com',
        method: 'GET' as const,
      };
      
      const result = HTTP_TOOL_DEF.inputSchema.safeParse(validInput);
      expect(result.success).toBe(true);
    });

    test('should reject invalid URL', () => {
      const invalidInput = {
        url: 'not-a-url',
        method: 'GET' as const,
      };
      
      const result = HTTP_TOOL_DEF.inputSchema.safeParse(invalidInput);
      expect(result.success).toBe(false);
    });

    test('should validate valid output', () => {
      const validOutput = {
        status: 200,
        headers: { 'content-type': 'application/json' },
        body: '{"success": true}',
      };
      
      const result = HTTP_TOOL_DEF.outputSchema.safeParse(validOutput);
      expect(result.success).toBe(true);
    });
  });

  describe('Web Search Tool', () => {
    test('should have correct structure', () => {
      expect(WEBSEARCH_TOOL_DEF.name).toBe('webSearch');
      expect(WEBSEARCH_TOOL_DEF.description).toBeDefined();
      expect(WEBSEARCH_TOOL_DEF.inputSchema).toBeDefined();
      expect(WEBSEARCH_TOOL_DEF.outputSchema).toBeDefined();
    });

    test('should validate valid input', () => {
      const validInput = {
        query: 'test query',
        numResults: 10,
      };
      
      const result = WEBSEARCH_TOOL_DEF.inputSchema.safeParse(validInput);
      expect(result.success).toBe(true);
    });

    test('should use default numResults', () => {
      const inputWithDefaults = {
        query: 'test query',
      };
      
      const result = WEBSEARCH_TOOL_DEF.inputSchema.parse(inputWithDefaults);
      expect(result.numResults).toBe(5);
    });

    test('should validate valid output', () => {
      const validOutput = {
        results: [
          {
            title: 'Test Result',
            url: 'https://example.com',
            snippet: 'This is a test snippet',
          },
        ],
      };
      
      const result = WEBSEARCH_TOOL_DEF.outputSchema.safeParse(validOutput);
      expect(result.success).toBe(true);
    });
  });

  describe('Vector Tool', () => {
    test('should have correct structure', () => {
      expect(VECTOR_TOOL_DEF.name).toBe('vector');
      expect(VECTOR_TOOL_DEF.description).toBeDefined();
      expect(VECTOR_TOOL_DEF.inputSchema).toBeDefined();
      expect(VECTOR_TOOL_DEF.outputSchema).toBeDefined();
    });

    test('should validate valid input', () => {
      const validInput = {
        query: 'semantic search query',
        k: 3,
      };
      
      const result = VECTOR_TOOL_DEF.inputSchema.safeParse(validInput);
      expect(result.success).toBe(true);
    });

    test('should use default k value', () => {
      const inputWithDefaults = {
        query: 'semantic search query',
      };
      
      const result = VECTOR_TOOL_DEF.inputSchema.parse(inputWithDefaults);
      expect(result.k).toBe(5);
    });

    test('should validate valid output', () => {
      const validOutput = {
        results: [
          {
            id: 'doc-1',
            text: 'Document content',
            score: 0.95,
            meta: { source: 'test' },
          },
        ],
      };
      
      const result = VECTOR_TOOL_DEF.outputSchema.safeParse(validOutput);
      expect(result.success).toBe(true);
    });
  });

  describe('OpenAI Function Conversion', () => {
    test('should convert HTTP tool to OpenAI function format', () => {
      const openAIFunc = toOpenAIFunction(HTTP_TOOL_DEF);
      
      expect(openAIFunc.name).toBe('http');
      expect(openAIFunc.description).toBeDefined();
      expect(openAIFunc.parameters).toBeDefined();
      expect(openAIFunc.parameters.type).toBe('object');
      expect(openAIFunc.parameters.properties).toBeDefined();
    });

    test('should convert all tools without throwing', () => {
      expect(() => {
        ALL_TOOL_DEFINITIONS.forEach(tool => toOpenAIFunction(tool));
      }).not.toThrow();
    });
  });

  describe('All Tool Definitions', () => {
    test('should export all three tools', () => {
      expect(ALL_TOOL_DEFINITIONS).toHaveLength(3);
      expect(ALL_TOOL_DEFINITIONS.map(t => t.name)).toEqual(['http', 'webSearch', 'vector']);
    });

    test('each tool should have required fields', () => {
      ALL_TOOL_DEFINITIONS.forEach(tool => {
        expect(tool.name).toBeDefined();
        expect(tool.description).toBeDefined();
        expect(tool.inputSchema).toBeDefined();
        expect(tool.outputSchema).toBeDefined();
      });
    });
  });
});
