import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createServer } from '../src/index';

const ORIGINAL_ENV = { ...process.env } as Record<string, string | undefined>;

function setAllow(list: string[]) {
  process.env.ALLOW_HTTP_HOSTS = JSON.stringify(list);
}

describe('Runner tools endpoint', () => {
  beforeEach(() => {
    Object.assign(process.env, ORIGINAL_ENV);
    setAllow(['api.openai.com', 'google.serper.dev']);
    process.env.SERPER_API_KEY = 'test-serper';
    process.env.OPENAI_API_KEY = 'test-openai';
  });
  afterEach(() => {
    vi.restoreAllMocks();
    Object.assign(process.env, ORIGINAL_ENV);
  });

  it('performs a simple RAG round-trip via /tools/vector (mocked)', async () => {
    // Mock embeddings (twice: for upsert and query)
    vi.spyOn(globalThis, 'fetch')
      .mockImplementationOnce(async () => new Response(JSON.stringify({ data: [{ embedding: [0.1, 0.2] }] }), { status: 200 }) as any);

    // Mock DB interactions by monkey-patching pool.connect
    const { pool } = await import('@metaagent/db');
    vi.spyOn(pool, 'connect').mockResolvedValue({
      query: vi.fn().mockResolvedValueOnce({ rows: [ { id: 'doc1', text: 'Answer about AGENTS.md', score: 0.93, meta: { source: 'AGENTS.md' } } ] } as any),
      release: vi.fn(),
    } as any);

    const app = createServer();

    // Seed a doc (simulate upsert): call vector tool is only query; we directly assume a doc exists via mocked select
    const res = await app.inject({
      method: 'POST',
      url: '/tools/vector',
      payload: { query: 'What is quickstart?', k: 1 },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json() as any;
    expect(body.results).toHaveLength(1);
    expect(body.results[0].text).toContain('AGENTS.md');
  });
});
