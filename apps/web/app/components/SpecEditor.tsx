import { useEffect, useRef, useState, useCallback } from "react";
import Editor from "@monaco-editor/react";
import type * as monaco from "monaco-editor";
import { parseTree, findNodeAtLocation } from "jsonc-parser";
import * as yaml from "js-yaml";
import * as prettier from "prettier";
import { AGENT_SPEC_JSON_SCHEMA } from "../utils/schema";
import type { ValidationResult } from "../workers/validation-worker";

interface SpecEditorProps {
  value: string;
  onChange: (value: string) => void;
  onValidationChange?: (errors: ValidationResult["errors"]) => void;
  readOnly?: boolean;
}

export default function SpecEditor({
  value,
  onChange,
  onValidationChange,
  readOnly = false
}: SpecEditorProps) {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const workerRef = useRef<Worker | null>(null);
  const validationTimeoutRef = useRef<NodeJS.Timeout>();
  const [isYaml, setIsYaml] = useState(false);

  // Initialize validation worker
  useEffect(() => {
    // Create worker with inline code to avoid module resolution issues
    const workerCode = `
import { AgentSpecSchema } from "@metaagent/spec";

self.addEventListener('message', (event) => {
  const { id, content } = event.data;
  
  try {
    let parsed;
    try {
      parsed = JSON.parse(content);
    } catch (parseError) {
      const result = {
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

    const validation = AgentSpecSchema.safeParse(parsed);
    
    if (validation.success) {
      const result = {
        id,
        isValid: true
      };
      self.postMessage(result);
    } else {
      const result = {
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
    const result = {
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
    `;
    
    const blob = new Blob([workerCode], { type: 'application/javascript' });
    workerRef.current = new Worker(URL.createObjectURL(blob));

    workerRef.current.onmessage = (event: MessageEvent<ValidationResult>) => {
      const result = event.data;
      updateValidationMarkers(result);
      onValidationChange?.(result.errors);
    };

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
    };
  }, [onValidationChange]);

  // Debounced validation
  const validateContent = useCallback((content: string) => {
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }

    validationTimeoutRef.current = setTimeout(() => {
      if (workerRef.current && content.trim()) {
        let jsonContent = content;
        
        // Convert YAML to JSON for validation if needed
        if (isYaml) {
          try {
            const parsed = yaml.load(content);
            jsonContent = JSON.stringify(parsed, null, 2);
          } catch (yamlError) {
            // Handle YAML parse error
            const result: ValidationResult = {
              id: "yaml-parse",
              isValid: false,
              errors: [{
                path: [],
                message: "Invalid YAML syntax",
                code: "invalid_yaml"
              }]
            };
            updateValidationMarkers(result);
            onValidationChange?.(result.errors);
            return;
          }
        }

        workerRef.current.postMessage({
          id: Date.now().toString(),
          content: jsonContent
        });
      }
    }, 300);
  }, [isYaml, onValidationChange]);

  // Update Monaco validation markers
  const updateValidationMarkers = useCallback((result: ValidationResult) => {
    if (!editorRef.current) return;

    const model = editorRef.current.getModel();
    if (!model) return;

    if (result.isValid || !result.errors) {
      // Clear all markers
      (window as any).monaco.editor.setModelMarkers(model, "validation", []);
      return;
    }

    // Convert Zod errors to Monaco markers
    const markers = result.errors.map(error => {
      let startLineNumber = 1;
      let startColumn = 1;
      let endLineNumber = 1;
      let endColumn = 1;

      if (error.path.length > 0 && !isYaml) {
        try {
          const tree = parseTree(model.getValue());
          const node = findNodeAtLocation(tree, error.path);
          if (node) {
            const startPos = model.getPositionAt(node.offset);
            const endPos = model.getPositionAt(node.offset + node.length);
            startLineNumber = startPos.lineNumber;
            startColumn = startPos.column;
            endLineNumber = endPos.lineNumber;
            endColumn = endPos.column;
          }
        } catch (parseError) {
          // Use first line if we can't parse
        }
      }

      return {
        startLineNumber,
        startColumn,
        endLineNumber,
        endColumn,
        message: error.message,
        severity: (window as any).monaco.MarkerSeverity.Error,
        source: "validation"
      };
    });

    (window as any).monaco.editor.setModelMarkers(model, "validation", markers);
  }, [isYaml]);

  // Handle Monaco editor mount
  const handleEditorDidMount = useCallback((editor: monaco.editor.IStandaloneCodeEditor) => {
    editorRef.current = editor;

    // Configure JSON language support with schema
    const uri = editor.getModel()?.uri.toString();
    if (uri && !isYaml && (window as any).monaco) {
      (window as any).monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
        validate: true,
        schemas: [{
          uri: "http://metaagent.com/agent-spec.json",
          fileMatch: [uri],
          schema: AGENT_SPEC_JSON_SCHEMA
        }]
      });
    }

    // Add keyboard shortcuts
    if ((window as any).monaco) {
      const monaco = (window as any).monaco;
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
        // Trigger save - parent component should handle this
        const saveEvent = new CustomEvent('editor-save');
        window.dispatchEvent(saveEvent);
      });

      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyF, () => {
        formatContent();
      });
    }

    // Initial validation
    validateContent(value);
  }, [isYaml, value, validateContent]);

  // Handle content change
  const handleEditorChange = useCallback((newValue: string | undefined) => {
    const content = newValue || "";
    onChange(content);
    validateContent(content);
  }, [onChange, validateContent]);

  // Format content
  const formatContent = useCallback(async () => {
    if (!editorRef.current) return;

    const content = editorRef.current.getValue();
    
    try {
      let formatted: string;
      
      if (isYaml) {
        // Parse and re-stringify YAML
        const parsed = yaml.load(content);
        formatted = yaml.dump(parsed, { indent: 2 });
      } else {
        // Use Prettier for JSON
        formatted = await prettier.format(content, {
          parser: "json",
          tabWidth: 2,
          semi: false
        });
      }
      
      editorRef.current.setValue(formatted);
    } catch (formatError) {
      console.warn("Failed to format content:", formatError);
    }
  }, [isYaml]);

  // Toggle between JSON and YAML
  const toggleFormat = useCallback(() => {
    if (!editorRef.current) return;

    const content = editorRef.current.getValue().trim();
    if (!content) {
      setIsYaml(!isYaml);
      return;
    }

    try {
      let converted: string;
      
      if (isYaml) {
        // YAML to JSON
        const parsed = yaml.load(content);
        converted = JSON.stringify(parsed, null, 2);
      } else {
        // JSON to YAML  
        const parsed = JSON.parse(content);
        converted = yaml.dump(parsed, { indent: 2 });
      }
      
      setIsYaml(!isYaml);
      editorRef.current.setValue(converted);
    } catch (conversionError) {
      console.warn("Failed to convert format:", conversionError);
    }
  }, [isYaml]);

  return (
    <div className="spec-editor">
      <div className="editor-toolbar">
        <button 
          onClick={toggleFormat}
          className="format-toggle"
          title={`Switch to ${isYaml ? 'JSON' : 'YAML'}`}
        >
          {isYaml ? 'JSON' : 'YAML'}
        </button>
        <button 
          onClick={formatContent}
          className="format-button"
          title="Format (Ctrl/Cmd+Shift+F)"
        >
          Format
        </button>
      </div>
      
      <Editor
        height="500px"
        language={isYaml ? "yaml" : "json"}
        value={value}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        options={{
          readOnly,
          minimap: { enabled: false },
          lineNumbers: "on",
          folding: true,
          wordWrap: "on",
          tabSize: 2,
          insertSpaces: true,
          automaticLayout: true,
          scrollBeyondLastLine: false,
          theme: "vs-dark"
        }}
      />
    </div>
  );
}
