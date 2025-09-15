import { safeFetch, type SafeFetchResponse } from './client';

export interface HttpToolArgs {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: unknown;
}

export async function httpTool(args: HttpToolArgs): Promise<SafeFetchResponse> {
  const res = await safeFetch(args);
  // Truncate large bodies to 100 KB
  const MAX = 100 * 1024;
  const body = res.body.length > MAX ? res.body.slice(0, MAX) : res.body;
  return { status: res.status, headers: res.headers, body };
}
