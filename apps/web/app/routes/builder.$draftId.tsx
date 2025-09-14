import { json, redirect, type LoaderFunctionArgs, type ActionFunctionArgs } from "@remix-run/node";
import { useLoaderData, useNavigate, useSearchParams } from "@remix-run/react";
import { useState } from "react";
import { requireUserId } from "../utils/session.server";
import { createSpecDraftService } from "../utils/specDraft.server";
import TemplatePicker from "../components/TemplatePicker";
import InterviewPanel from "../components/InterviewPanel";
import SpecPanel from "../components/SpecPanel";
import { templates } from "@metaagent/templates";
import { genericAgentInterview } from "@metaagent/interview";

export async function loader({ params, request }: LoaderFunctionArgs) {
  const userId = await requireUserId(request);
  const service = createSpecDraftService(userId);
  const draftId = params.draftId;

  if (!draftId) {
    return redirect("/builder");
  }

  const draft = await service.getDraft(draftId);
  if (!draft) {
    // If invalid id, start a new draft
    return redirect("/builder");
  }

  return json({ draft });
}

export async function action({ params, request }: ActionFunctionArgs) {
  const userId = await requireUserId(request);
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

  const [interviewState, setInterviewState] = useState<any>(initialState);
  const [focusPath, setFocusPath] = useState<(string | number)[]>();

  const handleAutosave = async (state: any) => {
    await fetch("/api/autosave", {
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
          <InterviewPanel 
            script={script!} 
            initialState={initialState as any} 
            onAutosave={handleAutosave} 
            onStateChange={setInterviewState}
            focusFieldPath={focusPath}
          />
        </div>
        <div className="builder-right">
          <SpecPanel 
            payload={interviewState?.specDraft?.payload}
            onErrorPathClick={setFocusPath}
          />
        </div>
      </div>
    </div>
  );
}
