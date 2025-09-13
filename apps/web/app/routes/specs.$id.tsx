import { useState, useEffect, useRef } from "react";
import { json, redirect, type ActionFunctionArgs, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData, useSubmit, useNavigation } from "@remix-run/react";
import SpecEditor from "../components/SpecEditor";
import ValidationPanel from "../components/ValidationPanel";
import type { ValidationResult } from "../workers/validation-worker";

export async function loader({ params, request }: LoaderFunctionArgs) {
  const { id } = params;
  if (!id) {
    throw new Response("Draft ID required", { status: 400 });
  }

  // Fetch draft via API
  const response = await fetch(`${request.url.replace(/\/specs\/.*/, "")}/api/specs/drafts?id=${id}`);
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Response("Draft not found", { status: 404 });
    }
    throw new Response("Failed to load draft", { status: response.status });
  }

  const draft = await response.json();
  return json({ draft });
}

export async function action({ params, request }: ActionFunctionArgs) {
  const { id } = params;
  const formData = await request.formData();
  const intent = formData.get("intent");

  if (intent === "save") {
    const name = formData.get("name") as string;
    const spec = JSON.parse(formData.get("spec") as string);
    const tags = JSON.parse(formData.get("tags") as string || "[]");

    // Update via API
    const response = await fetch(`${request.url.replace(/\/specs\/.*/, "")}/api/specs/drafts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, name, spec, tags })
    });

    if (response.ok) {
      const draft = await response.json();
      return json({ draft, success: "Draft saved successfully" });
    } else {
      const error = await response.json();
      return json({ error: error.error }, { status: response.status });
    }
  }

  if (intent === "delete") {
    // Delete via API
    const response = await fetch(`${request.url.replace(/\/specs\/.*/, "")}/api/specs/drafts?id=${id}`, {
      method: "DELETE"
    });

    if (response.ok) {
      return redirect("/catalog/drafts");
    } else {
      const error = await response.json();
      return json({ error: error.error }, { status: response.status });
    }
  }

  return json({ error: "Invalid intent" }, { status: 400 });
}

export default function EditSpecRoute() {
  const { draft } = useLoaderData<typeof loader>();
  const submit = useSubmit();
  const navigation = useNavigation();
  
  const [spec, setSpec] = useState(() => 
    JSON.stringify(draft.spec, null, 2)
  );
  const [validationErrors, setValidationErrors] = useState<ValidationResult["errors"]>();
  const [metadata, setMetadata] = useState({
    name: draft.name,
    tags: draft.tags || []
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

  const handleDeleteDraft = () => {
    if (confirm("Are you sure you want to delete this draft? This action cannot be undone.")) {
      const formData = new FormData();
      formData.append("intent", "delete");
      submit(formData, { method: "post" });
    }
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
          <span className="draft-id">ID: {draft.id}</span>
          {isDirty && <span className="dirty-indicator">●</span>}
        </div>
        
        <div className="spec-actions">
          <button onClick={handleImport} disabled={isImporting}>
            {isImporting ? "Importing..." : "Import"}
          </button>
          <button onClick={handleExport}>Export</button>
          <button 
            onClick={handleDeleteDraft}
            className="delete-button"
            disabled={isSaving}
          >
            Delete
          </button>
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
