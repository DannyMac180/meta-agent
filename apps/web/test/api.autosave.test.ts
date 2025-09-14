import { describe, it, expect } from "vitest";

import { action } from "../app/routes/api.autosave";

describe("api.autosave action", () => {
  it("returns 202 for autosave enqueue", async () => {
    const body = { id: "draft-1", title: "Draft", payload: { x: 1 }, isDraft: true, status: "DRAFT" };
    const req = new Request("http://localhost/api/autosave", { method: "POST", body: JSON.stringify(body) });
    Object.defineProperty(req, "headers", { value: new Headers({ "Content-Type": "application/json" }) });

    const res: Response = await action({ request: req } as any);
    expect(res.status).toBe(202);
  });

  it("rejects non-POST", async () => {
    const req = new Request("http://localhost/api/autosave", { method: "GET" });
    const res: Response = await action({ request: req } as any);
    expect(res.status).toBe(405);
  });
});
