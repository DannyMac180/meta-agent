import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { webSearchTool } from '../src/tool';
import { searchWeb } from '../src/client';

const ORIGINAL_ENV = { ...process.env } as Record<string, string | undefined>;

function setAllow(list: string[]) {
  process.env.ALLOW_HTTP_HOSTS = JSON.stringify(list);
}

describe('WebSearch Tool', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.assign(process.env, ORIGINAL_ENV);
    process.env.SERPER_API_KEY = 'test-key';
  });

  afterEach(() => {
    vi.restoreAllMocks();
    Object.assign(process.env, ORIGINAL_ENV);
  });

  it('maps serper results to normalized format', async () => {
    setAllow(['google.serper.dev']);

    const serperResponse = {
      organic: [
        { title: 'Result 1', link: 'https://example.com/1', snippet: 'Snippet 1' },
        { title: 'Result 2', link: 'https://example.com/2', snippet: 'Snippet 2' },
      ],
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(serperResponse), { status: 200, headers: { 'content-type': 'application/json' } }) as any
    );

    const res = await webSearchTool({ query: 'hello world', numResults: 2 });
    expect(res.results).toHaveLength(2);
    expect(res.results[0]).toEqual({ title: 'Result 1', url: 'https://example.com/1', snippet: 'Snippet 1' });

    // Verify headers contained API key
    const lastCall = fetchMock.mock.calls[0];
    const init = lastCall[1] as RequestInit;
    expect((init.headers as Record<string, string>)['X-API-KEY']).toBe('test-key');
  });

  it('uses default numResults and enforces allow-list', async () => {
    // No allow means blocked
    process.env.ALLOW_HTTP_HOSTS = JSON.stringify([]);

    await expect(webSearchTool({ query: 'blocked' })).rejects.toThrow('Blocked host');

    // Allow and test default count
    setAllow(['google.serper.dev']);
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ organic: new Array(10).fill(0).map((_, i) => ({ title: `T${i}`, link: `https://e/${i}`, snippet: `S${i}` })) }), { status: 200 }) as any
    );

    const res = await webSearchTool({ query: 'ok' });
    expect(res.results).toHaveLength(5);
  });
});
