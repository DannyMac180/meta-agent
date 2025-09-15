import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as db from '@metaagent/db';
import { embedText, upsertDocument, querySimilar } from '../src/client';

const ORIGINAL_ENV = { ...process.env } as Record<string, string | undefined>;

function setAllow(list: string[]) {
  process.env.ALLOW_HTTP_HOSTS = JSON.stringify(list);
}

describe('Vector Tool', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.assign(process.env, ORIGINAL_ENV);
    process.env.OPENAI_API_KEY = 'test-key';
    setAllow(['api.openai.com']);
  });
  afterEach(() => {
    vi.restoreAllMocks();
    Object.assign(process.env, ORIGINAL_ENV);
  });

  it('calls OpenAI embeddings and returns numeric vector', async () => {
    const fakeEmbedding = { data: [{ embedding: [0.1, 0.2, 0.3] }] };
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(fakeEmbedding), { status: 200, headers: { 'content-type': 'application/json' } }) as any
    );
    const vec = await embedText('hello');
    expect(vec).toEqual([0.1, 0.2, 0.3]);
  });

  it('upserts document with embedding and then queries similar (SQL path mocked)', async () => {
    // Mock two embedding calls with fresh Response bodies
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify({ data: [{ embedding: [0.1, 0.2] }] }), { status: 200 }) as any)
      .mockResolvedValueOnce(new Response(JSON.stringify({ data: [{ embedding: [0.1, 0.2] }] }), { status: 200 }) as any);

    const connectMock = vi.spyOn(db.pool, 'connect').mockResolvedValue({
      query: vi
        .fn()
        // first call: insert
        .mockResolvedValueOnce({ rows: [ { id: 'doc1' } ] } as any)
        // second call: select similar
        .mockResolvedValueOnce({ rows: [ { id: 'doc1', text: 'hello doc', score: 0.99, meta: { s: 'x' } } ] } as any),
      release: vi.fn(),
    } as any);

    const id = await upsertDocument({ text: 'hello doc', meta: { s: 'x' } });
    expect(typeof id).toBe('string');

    const res = await querySimilar('hello', 1);
    expect(res).toHaveLength(1);
    expect(res[0].id).toBe('doc1');

    expect(connectMock).toHaveBeenCalled();
  });
});
