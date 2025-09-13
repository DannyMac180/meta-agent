import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the SpecDraftService used by builder route with in-memory store
const memoryStore: any[] = [];

vi.mock("../app/utils/specDraft.server", () => {
  class MockService {
    userId: string;
    constructor(userId: string) { this.userId = userId; }
    async saveDraft(input: any) {
      if (input.id) {
        const idx = memoryStore.findIndex((d) => d.id === input.id);
        if (idx >= 0) {
          const updated = { ...memoryStore[idx], title: input.title, spec: input.payload, updatedAt: new Date().toISOString() };
          memoryStore[idx] = updated;
          return { id: updated.id, title: updated.title, isDraft: true, status: "DRAFT", payload: updated.spec, createdAt: updated.createdAt || new Date().toISOString(), updatedAt: updated.updatedAt };
        }
      }
      const created = { id: input.id || `draft-${memoryStore.length + 1}` , title: input.title, spec: input.payload, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
      memoryStore.push(created);
      return { id: created.id, title: created.title, isDraft: true, status: "DRAFT", payload: created.spec, createdAt: created.createdAt, updatedAt: created.updatedAt };
    }
    async getDraft(id: string) {
      const found = memoryStore.find((d) => d.id === id);
      return found ? { id: found.id, title: found.title, isDraft: true, status: "DRAFT", payload: found.spec, createdAt: found.createdAt, updatedAt: found.updatedAt } : null;
    }
  }
  return { createSpecDraftService: (userId: string) => new MockService(userId) };
});

// Import route handlers after mocks
import { action as builderAction } from "../app/routes/builder.$draftId";
import { loader as catalogLoader } from "../app/routes/catalog.drafts";
import { InterviewRunner, genericAgentInterview } from "@metaagent/interview";

beforeEach(() => {
  memoryStore.length = 0;
});

describe("E2E: interview → autosave → catalog", () => {
  it("runs interview, autosaves via builder action, and appears in catalog list", async () => {
    // 1) Run a short interview to produce a payload
    const runner = new InterviewRunner(genericAgentInterview);
    const initialState: any = { answers: {}, currentNodeId: "agent-name", specDraft: { id: "draft-1", title: "Untitled", payload: {} }, visitedNodes: [] };
    let state = initialState;
    state = runner.runNode(state, "my-agent").updatedState; // meta.name
    state = runner.runNode(state, "Helpful agent description").updatedState; // meta.description
    state = runner.runNode(state, "Do X with Y and Z").updatedState; // prompt.template

    // 2) Autosave through builder route action
    const body = { id: state.specDraft.id, title: "My Agent", templateId: "generic-agent", payload: state.specDraft.payload, isDraft: true, status: "DRAFT" };
    const req = new Request(`http://localhost/builder/${state.specDraft.id}`, { method: "POST", body: JSON.stringify(body) });
    Object.defineProperty(req, "headers", { value: new Headers({ "Content-Type": "application/json" }) });
    const saveRes: Response = await builderAction({ params: { draftId: state.specDraft.id }, request: req } as any);
    expect(saveRes.status).toBe(200);

    // 3) Catalog loader fetches drafts via API - mock fetch to return memoryStore
    const draftsPayload = memoryStore.map(d => ({ id: d.id, name: d.title, title: d.title, spec: d.spec, createdAt: d.createdAt, updatedAt: d.updatedAt }));
    (global as any).fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => draftsPayload });

    const catalogReq = new Request("http://localhost/catalog/drafts");
    const catRes: Response = await catalogLoader({ request: catalogReq } as any);
    expect(catRes.status).toBe(200);
    const data = await catRes.json();
    expect(Array.isArray(data.drafts)).toBe(true);
    expect(data.drafts.some((d: any) => d.name === "My Agent")).toBe(true);
  });
});
