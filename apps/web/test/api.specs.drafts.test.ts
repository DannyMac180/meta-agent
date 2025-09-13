import { describe, it, expect, beforeEach, vi } from "vitest";

// In-memory store for drafts used by this test's db mock
let store: any[] = [];

vi.mock("@metaagent/db", () => {
  const makeSelect = (result: any[] = []) => ({
    from: () => ({
      where: () => ({
        orderBy: () => result,
        limit: () => result,
      }),
    }),
  });

  const makeUpdate = (updated: any[] = []) => ({
    set: () => ({
      where: () => ({ returning: () => updated }),
    }),
  });

  const makeInsert = (created: any[] = []) => ({
    values: () => ({ returning: () => created }),
  });

  const makeDelete = (deleted: any[] = []) => ({
    where: () => ({ returning: () => deleted, rowCount: deleted.length }),
  });

  // Default mocks delegate to current store snapshot
  const db = {
    select: () => makeSelect([...store]),
    update: () => makeUpdate([...store]),
    insert: () => makeInsert([...store]),
    delete: () => makeDelete([...store]),
  } as any;

  return {
    db,
    specDrafts: {},
    setAppUser: vi.fn(),
  };
});

// Import after mocks
import { loader, action } from "../app/routes/api.specs.drafts";

const userId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

const baseDraft = {
  id: "draft-1",
  ownerUserId: userId,
  name: "My Draft",
  title: "My Draft",
  spec: { meta: { id: userId, name: "agent", version: "0.0.1", createdAt: "2024-01-01T00:00:00Z", updatedAt: "2024-01-01T00:00:00Z" }, prompt: { template: "Hello" }, model: { provider: "openai", model: "gpt-4o-mini", maxTokens: 128, temperature: 0.7 }, variables: [] },
  tags: ["t1"],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

beforeEach(() => {
  store = [ { ...baseDraft } ];
});

describe("api.specs.drafts loader", () => {
  it("lists drafts for user", async () => {
    const req = new Request("http://localhost/api/specs/drafts");
    const res: Response = await loader({ request: req } as any);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data[0].id).toBe("draft-1");
  });

  it("gets single draft by id", async () => {
    const req = new Request("http://localhost/api/specs/drafts?id=draft-1");
    const res: Response = await loader({ request: req } as any);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.id).toBe("draft-1");
  });
});

describe("api.specs.drafts action", () => {
  it("creates a new draft", async () => {
    // Arrange insert to push into store and return created
    const newDraft = { ...baseDraft, id: "draft-2", name: "New Draft", title: "New Draft" };
    // Override insert mock for this call
    const { db } = await import("@metaagent/db");
    db.insert = () => ({ values: (vals: any) => { const created = { ...newDraft, ...vals }; store.push(created); return { returning: () => [created] }; } });

    const body = { name: "New Draft", spec: {}, tags: [] }; // empty spec allowed for drafts
    const req = new Request("http://localhost/api/specs/drafts", { method: "POST", body: JSON.stringify(body) });
    Object.defineProperty(req, "headers", { value: new Headers({ "Content-Type": "application/json" }) });

    const res: Response = await action({ request: req } as any);
    expect(res.status).toBe(201);
    const data = await res.json();
    expect(data.name ?? data.title).toBe("New Draft");
  });

  it("rejects invalid update spec", async () => {
    const body = { id: "draft-1", name: "Bad", spec: {}, tags: [] };
    const req = new Request("http://localhost/api/specs/drafts", { method: "POST", body: JSON.stringify(body) });
    Object.defineProperty(req, "headers", { value: new Headers({ "Content-Type": "application/json" }) });

    const res: Response = await action({ request: req } as any);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Invalid spec");
  });

  it("deletes a draft", async () => {
    const { db } = await import("@metaagent/db");
    db.delete = () => ({ where: () => ({ returning: () => [{ id: "draft-1" }], rowCount: 1 }) });

    const req = new Request("http://localhost/api/specs/drafts?id=draft-1", { method: "DELETE" });
    const res: Response = await action({ request: req } as any);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
  });
});
