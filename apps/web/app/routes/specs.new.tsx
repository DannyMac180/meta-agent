import { useState, useEffect, useRef } from "react";
import { json, redirect, type ActionFunctionArgs, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData, useSubmit, useNavigation } from "@remix-run/react";
import SpecEditor from "../components/SpecEditor";
import ValidationPanel from "../components/ValidationPanel";
import type { ValidationResult } from "../workers/validation-worker";

// Template specs
const TEMPLATES = {
  chatbot: {
    specVersion: "0.1.0" as const,
    meta: {
      id: "template-chatbot",
      name: "chatbot-agent",
      description: "A conversational chatbot agent",
      version: "0.0.1",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      tags: ["chatbot", "conversation"]
    },
    variables: [
      { key: "topic", type: "string" as const, required: true },
      { key: "tone", type: "enum" as const, enumValues: ["friendly", "professional", "casual"], required: false }
    ],
    prompt: {
      template: "You are a helpful chatbot. Discuss {{topic}} in a {{tone}} tone."
    },
    model: {
      provider: "openai" as const,
      model: "gpt-4o-mini",
      maxTokens: 1024,
      temperature: 0.7
    },
    tools: [],
    limits: {
      timeoutSec: 60,
      budgetUsd: 1.0
    }
  },
  "web-automation": {
    specVersion: "0.1.0" as const,
    meta: {
      id: "template-web-automation",
      name: "web-automation-agent", 
      description: "Agent for automating web tasks",
      version: "0.0.1",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      tags: ["automation", "web"]
    },
    variables: [
      { key: "target_url", type: "string" as const, required: true },
      { key: "action", type: "enum" as const, enumValues: ["scrape", "interact", "monitor"], required: true }
    ],
    prompt: {
      template: "Perform {{action}} on {{target_url}}. Be careful and precise."
    },
    model: {
      provider: "openai" as const,
      model: "gpt-4o",
      maxTokens: 2048,
      temperature: 0.1
    },
    tools: [
      { kind: "http" as const, allowDomains: ["https://*"] }
    ],
    limits: {
      timeoutSec: 120,
      budgetUsd: 2.0
    }
  },
  "api-copilot": {
    specVersion: "0.1.0" as const,
    meta: {
      id: "template-api-copilot",
      name: "api-copilot-agent",
      description: "AI assistant for API development and testing", 
      version: "0.0.1",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      tags: ["api", "development", "testing"]
    },
    variables: [
      { key: "api_spec", type: "string" as const, required: true },
      { key: "task", type: "enum" as const, enumValues: ["generate", "test", "document"], required: true }
    ],
    prompt: {
      template: "Help with {{task}} for the API: {{api_spec}}. Provide clear, actionable guidance."
    },
    model: {
      provider: "openai" as const,
      model: "gpt-4o",
      maxTokens: 4096,
      temperature: 0.2
    },
    tools: [
      { kind: "http" as const, allowDomains: ["https://api.example.com"] }
    ],
    limits: {
      timeoutSec: 180,
      budgetUsd: 3.0
    }
  }
};

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const template = url.searchParams.get("template") as keyof typeof TEMPLATES | null;
  
  return json({
    initialSpec: template && template in TEMPLATES ? TEMPLATES[template] : null,
    templateName: template
  });
}

export async function action({ request }: ActionFunctionArgs) {
  const formData = await request.formData();
  const intent = formData.get("intent");

  if (intent === "save") {
    const name = formData.get("name") as string;
    const spec = JSON.parse(formData.get("spec") as string);
    const tags = JSON.parse(formData.get("tags") as string || "[]");

    // Save via API
    const response = await fetch(`${request.url.replace(/\/specs\/new.*/, "")}/api/specs/drafts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, spec, tags })
    });

    if (response.ok) {
      const draft = await response.json();
      return redirect(`/specs/${draft.id}`);
    } else {
      const error = await response.json();
      return json({ error: error.error }, { status: response.status });
    }
  }

  return json({ error: "Invalid intent" }, { status: 400 });
}

export default function NewSpecRoute() {
  const { initialSpec, templateName } = useLoaderData<typeof loader>();
  const submit = useSubmit();
  const navigation = useNavigation();
  
  const [spec, setSpec] = useState(() => 
    initialSpec ? JSON.stringify(initialSpec, null, 2) : "{}"
  );
  const [validationErrors, setValidationErrors] = useState<ValidationResult["errors"]>();
  const [metadata, setMetadata] = useState({
    name: initialSpec?.meta?.name || "untitled-spec",
    tags: initialSpec?.meta?.tags || []
  });
  const [isDirty, setIsDirty] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Handle Cmd/Ctrl+S for save
    const handleSave = (e: Event) => {
      e.preventDefault();
      handleSaveSpec();
    };

    window.addEventListener('editor-save', handleSave);
    return () => window.removeEventListener('editor-save', handleSave);
  }, [spec, metadata, validationErrors]);

  const handleSpecChange = (newSpec: string) => {
    setSpec(newSpec);
    setIsDirty(true);
  };

  const handleValidationChange = (errors?: ValidationResult["errors"]) => {
    setValidationErrors(errors);
  };

  const handleSaveSpec = () => {
    if (validationErrors && validationErrors.length > 0) {
      alert("Cannot save spec with validation errors. Please fix them first.");
      return;
    }

    const formData = new FormData();
    formData.append("intent", "save");
    formData.append("name", metadata.name);
    formData.append("spec", spec);
    formData.append("tags", JSON.stringify(metadata.tags));

    submit(formData, { method: "post" });
  };

  const handleImport = () => {
    fileInputRef.current?.click();
  };

  const handleFileImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.size > 200 * 1024) { // 200KB limit
      alert("File too large (>200KB)");
      return;
    }

    setIsImporting(true);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        setSpec(content);
        setIsDirty(true);
        
        // Try to extract name from imported spec
        try {
          const parsed = JSON.parse(content);
          if (parsed.meta?.name) {
            setMetadata(prev => ({ ...prev, name: parsed.meta.name }));
          }
        } catch {
          // Ignore parse errors for metadata extraction
        }
      } catch (error) {
        alert("Failed to read file");
      } finally {
        setIsImporting(false);
      }
    };
    reader.readAsText(file);
  };

  const handleExport = () => {
    const blob = new Blob([spec], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${metadata.name}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const isValid = !validationErrors || validationErrors.length === 0;
  const isSaving = navigation.state === "submitting";

  return (
    <div className="spec-editor-page">
      <header className="spec-editor-header">
        <div className="spec-meta">
          <input
            type="text"
            value={metadata.name}
            onChange={(e) => {
              setMetadata(prev => ({ ...prev, name: e.target.value }));
              setIsDirty(true);
            }}
            className="spec-name-input"
            placeholder="Spec name"
          />
          {templateName && (
            <span className="template-badge">Template: {templateName}</span>
          )}
          {isDirty && <span className="dirty-indicator">●</span>}
        </div>
        
        <div className="spec-actions">
          <button onClick={handleImport} disabled={isImporting}>
            {isImporting ? "Importing..." : "Import"}
          </button>
          <button onClick={handleExport}>Export</button>
          <button 
            onClick={handleSaveSpec}
            disabled={!isValid || isSaving}
            className={isValid ? "save-button-valid" : "save-button-invalid"}
          >
            {isSaving ? "Saving..." : "Save Draft"}
          </button>
        </div>
      </header>

      <div className="spec-editor-content">
        <div className="spec-editor-main">
          <SpecEditor
            value={spec}
            onChange={handleSpecChange}
            onValidationChange={handleValidationChange}
          />
        </div>
        
        <div className="spec-editor-sidebar">
          <ValidationPanel
            errors={validationErrors}
            onErrorClick={(error) => {
              // Focus editor on error - basic implementation
              console.log("Focus error:", error);
            }}
          />
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".json,.yaml,.yml"
        style={{ display: "none" }}
        onChange={handleFileImport}
      />
    </div>
  );
}
