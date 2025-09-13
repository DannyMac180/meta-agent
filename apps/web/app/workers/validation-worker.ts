// Validation worker to run Zod validation off the main thread
import { AgentSpecSchema } from "@metaagent/spec";

export interface ValidationMessage {
  id: string;
  content: string;
}

export interface ValidationResult {
  id: string;
  isValid: boolean;
  errors?: Array<{
    path: (string | number)[];
    message: string;
    code: string;
  }>;
}

self.addEventListener('message', (event: MessageEvent<ValidationMessage>) => {
  const { id, content } = event.data;
  
  try {
    // Parse JSON content
    let parsed;
    try {
      parsed = JSON.parse(content);
    } catch (parseError) {
      const result: ValidationResult = {
        id,
        isValid: false,
        errors: [{
          path: [],
          message: "Invalid JSON syntax",
          code: "invalid_json"
        }]
      };
      self.postMessage(result);
      return;
    }

    // Validate with Zod schema
    const validation = AgentSpecSchema.safeParse(parsed);
    
    if (validation.success) {
      const result: ValidationResult = {
        id,
        isValid: true
      };
      self.postMessage(result);
    } else {
      const result: ValidationResult = {
        id,
        isValid: false,
        errors: validation.error.issues.map(issue => ({
          path: issue.path,
          message: issue.message,
          code: issue.code
        }))
      };
      self.postMessage(result);
    }
  } catch (error) {
    const result: ValidationResult = {
      id,
      isValid: false,
      errors: [{
        path: [],
        message: error instanceof Error ? error.message : "Unknown validation error",
        code: "validation_error"
      }]
    };
    self.postMessage(result);
  }
});

export {};
