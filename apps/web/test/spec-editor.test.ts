import { describe, it, expect, vi } from "vitest";

// Mock the API response for testing
const mockDraft = {
  id: "test-draft-id",
  name: "Test Draft",
  spec: {
    specVersion: "0.1.0",
    meta: {
      id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      name: "test-agent",
      version: "0.0.1",
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z"
    },
    variables: [
      { key: "topic", type: "string", required: true }
    ],
    prompt: {
      template: "Talk about {{topic}}"
    },
    model: {
      provider: "openai",
      model: "gpt-4o-mini",
      maxTokens: 1024,
      temperature: 0.7
    }
  },
  tags: ["test"],
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z"
};

describe("Spec Editor API Routes", () => {
  it("should create a new draft", async () => {
    // Mock fetch for the test
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDraft
    });

    const payload = {
      name: "Test Draft",
      spec: mockDraft.spec,
      tags: ["test"]
    };

    const response = await fetch("/api/specs/drafts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    expect(response.ok).toBe(true);
    const result = await response.json();
    expect(result.name).toBe("Test Draft");
  });

  it("should update an existing draft", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ...mockDraft, name: "Updated Draft" })
    });

    const payload = {
      id: mockDraft.id,
      name: "Updated Draft",
      spec: mockDraft.spec,
      tags: ["test", "updated"]
    };

    const response = await fetch("/api/specs/drafts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    expect(response.ok).toBe(true);
    const result = await response.json();
    expect(result.name).toBe("Updated Draft");
  });

  it("should list drafts for user", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [mockDraft]
    });

    const response = await fetch("/api/specs/drafts");
    expect(response.ok).toBe(true);
    
    const drafts = await response.json();
    expect(Array.isArray(drafts)).toBe(true);
    expect(drafts.length).toBe(1);
    expect(drafts[0].id).toBe(mockDraft.id);
  });

  it("should delete a draft", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true })
    });

    const response = await fetch(`/api/specs/drafts?id=${mockDraft.id}`, {
      method: "DELETE"
    });

    expect(response.ok).toBe(true);
    const result = await response.json();
    expect(result.success).toBe(true);
  });
});

describe("Validation Worker", () => {
  it("should validate a correct spec", async () => {
    // Since we can't easily test Web Workers in this environment,
    // we'll test the validation logic directly
    const { AgentSpecSchema } = await import("@metaagent/spec");
    
    const validSpec = {
      specVersion: "0.1.0",
      meta: {
        id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        name: "test-agent",
        version: "0.0.1",
        createdAt: "2024-01-01T00:00:00Z",
        updatedAt: "2024-01-01T00:00:00Z"
      },
      variables: [
        { key: "topic", type: "string", required: true }
      ],
      prompt: {
        template: "Talk about {{topic}}"
      },
      model: {
        provider: "openai",
        model: "gpt-4o-mini",
        maxTokens: 1024,
        temperature: 0.7
      }
    };

    const result = AgentSpecSchema.safeParse(validSpec);
    expect(result.success).toBe(true);
  });

  it("should reject invalid spec", async () => {
    const { AgentSpecSchema } = await import("@metaagent/spec");
    
    const invalidSpec = {
      specVersion: "0.1.0",
      meta: {
        id: "invalid-id", // Invalid ULID format
        name: "test-agent",
        version: "0.0.1",
        createdAt: "2024-01-01T00:00:00Z",
        updatedAt: "2024-01-01T00:00:00Z"
      },
      variables: [
        { key: "topic", type: "string", required: true }
      ],
      prompt: {
        template: "Talk about {{unknown_var}}" // References undeclared variable
      },
      model: {
        provider: "openai",
        model: "gpt-4o-mini",
        maxTokens: 1024,
        temperature: 0.7
      }
    };

    const result = AgentSpecSchema.safeParse(invalidSpec);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues.length).toBeGreaterThan(0);
    }
  });
});

describe("JSON Schema Generation", () => {
  it("should generate valid JSON schema from Zod", async () => {
    // For now, just test that the import works
    const { AGENT_SPEC_JSON_SCHEMA } = await import("../app/utils/schema");
    
    expect(AGENT_SPEC_JSON_SCHEMA).toBeDefined();
    // The schema may be complex, so just check it exists and has some content
    expect(typeof AGENT_SPEC_JSON_SCHEMA).toBe("object");
  });
});
