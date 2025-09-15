import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { safeFetch } from '../src/client';
import { httpTool } from '../src/tool';

const ORIGINAL_ENV = { ...process.env };

function setAllow(list: string[]) {
  process.env.ALLOW_HTTP_HOSTS = JSON.stringify(list);
}

describe('HTTP Tool', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.assign(process.env, ORIGINAL_ENV);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    Object.assign(process.env, ORIGINAL_ENV);
  });

  it('blocks disallowed host', async () => {
    setAllow(['allowed.example']);
    await expect(safeFetch({ url: 'https://disallowed.example/path' })).rejects.toThrow('Blocked host');
  });

  it('allows exact host', async () => {
    setAllow(['api.example.com']);

    const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('ok', { status: 200, headers: { 'content-type': 'text/plain' } }) as any
    );

    const res = await safeFetch({ url: 'https://api.example.com/data' });
    expect(mock).toHaveBeenCalled();
    expect(res.status).toBe(200);
    expect(res.body).toBe('ok');
    expect(res.headers['content-type']).toBe('text/plain');
  });

  it('supports wildcard allow list', async () => {
    setAllow(['*.example.com']);

    const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('ok', { status: 200 }) as any
    );

    const res = await safeFetch({ url: 'https://service.api.example.com/users' });
    expect(res.status).toBe(200);
    expect(res.body).toBe('ok');
  });

  it('sends JSON body and sets content-type if missing', async () => {
    setAllow(['api.example.com']);

    const mock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_input: any, init?: RequestInit) => {
      const body = init?.body as string;
      const headers = init?.headers as Record<string, string>;
      expect(headers['content-type'] || (headers as any)['Content-Type']).toBe('application/json');
      expect(body).toBe(JSON.stringify({ a: 1 }));
      return new Response('{}', { status: 201, headers: { 'content-type': 'application/json' } }) as any;
    });

    const res = await safeFetch({ url: 'https://api.example.com/create', method: 'POST', body: { a: 1 } });
    expect(res.status).toBe(201);
  });

  it('truncates large body in httpTool', async () => {
    setAllow(['api.example.com']);
    const large = 'x'.repeat(150 * 1024);
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(large, { status: 200 }) as any
    );

    const res = await httpTool({ url: 'https://api.example.com/huge' });
    expect(res.body.length).toBe(100 * 1024);
  });
});
