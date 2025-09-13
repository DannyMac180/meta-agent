import { json, type LoaderFunctionArgs, type ActionFunctionArgs } from "@remix-run/node";
import { useLoaderData, useNavigate, useSearchParams } from "@remix-run/react";
import { createSpecDraftService } from "../utils/specDraft.server";
import TemplatePicker from "../components/TemplatePicker";
import InterviewPanel from "../components/InterviewPanel";
import { templates } from "@metaagent/templates";
import { genericAgentInterview } from "@metaagent/interview";
import { createDraftSpec } from "@metaagent/spec";

function getUserId() { return "01ARZ3NDEKTSV4RRFFQ69G5FAV"; }

export async function loader({ params, request }: LoaderFunctionArgs) {
  const userId = getUserId();
  const service = createSpecDraftService(userId);
  const url = new URL(request.url);
  const draftId = params.draftId;

  let draft = draftId ? await service.getDraft(draftId) : null;
  if (!draft) {
    // create new draft
    draft = createDraftSpec({ title: "Untitled Agent" });
  }

  return json({ draft });
}

export async function action({ params, request }: ActionFunctionArgs) {
  const userId = getUserId();
  const service = createSpecDraftService(userId);
  const body = await request.json();

  const saved = await service.saveDraft(body);
  return json(saved);
}

export default function BuilderRoute() {
  const { draft } = useLoaderData<typeof loader>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const templateId = searchParams.get("template");

  const handleTemplateSelect = async (id: string) => {
    const template = templates.find((t) => t.id === id);
    if (!template) return;

    // Save draft with template's default spec
    const res = await fetch("/builder/" + draft.id, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: draft.id,
        title: draft.title,
        templateId: template.id,
        payload: template.defaultSpec.payload,
        isDraft: true,
        status: "DRAFT",
      }),
    });

    if (res.ok) {
      setSearchParams((prev) => {
        prev.set("template", template.id);
        return prev;
      });
    }
  };

  const script = templateId ? templates.find((t) => t.id === templateId)?.interview || genericAgentInterview : genericAgentInterview;
  const initialState = {
    answers: {},
    currentNodeId: (script as any).startNodeId || "agent-name",
    specDraft: draft,
    visitedNodes: [],
  };

  const handleAutosave = async (state: any) => {
    await fetch("/builder/" + draft.id, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: draft.id,
        title: draft.title,
        templateId: templateId ?? undefined,
        payload: state.specDraft.payload,
        isDraft: true,
        status: "DRAFT",
      }),
    });
  };

  return (
    <div className="builder-layout">
      <div className="builder-top">
        {!templateId && <TemplatePicker onSelect={handleTemplateSelect} />}
      </div>
      <div className="builder-content">
        <div className="builder-left">
          <InterviewPanel script={script!} initialState={initialState as any} onAutosave={handleAutosave} />
        </div>
        <div className="builder-right">
          {/* Spec panel JSON preview */}
          <pre style={{ maxHeight: 500, overflow: "auto", background: "#0b0b0e", color: "#ddd", padding: 12 }}>
            {JSON.stringify(initialState.specDraft.payload, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
