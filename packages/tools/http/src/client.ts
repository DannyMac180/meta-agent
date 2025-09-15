type Method = 'GET' | 'POST' | 'PUT' | 'DELETE';

export interface SafeFetchOptions {
  url: string;
  method?: Method;
  headers?: Record<string, string>;
  body?: unknown;
  timeoutMs?: number;
}

export interface SafeFetchResponse {
  status: number;
  headers: Record<string, string>;
  body: string;
}

const DEFAULT_TIMEOUT_MS = 30000;

function parseAllowList(): string[] {
  const raw = process.env.ALLOW_HTTP_HOSTS?.trim();
  if (!raw) return [];
  try {
    // Prefer JSON array
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return parsed.map(String);
  } catch (_) {
    // Fallback: comma-separated string
    return raw.split(',').map(s => s.trim()).filter(Boolean);
  }
  return [];
}

function hostMatches(pattern: string, host: string): boolean {
  if (!pattern) return false;
  if (pattern === host) return true;
  if (pattern.startsWith('*.')) {
    const suffix = pattern.slice(1); // remove leading '*'
    return host.endsWith(suffix) && host.split('.').length >= pattern.split('.').length;
  }
  return false;
}

function isHostAllowed(host: string, allow: string[]): boolean {
  return allow.some(p => hostMatches(p, host));
}

export async function safeFetch(opts: SafeFetchOptions): Promise<SafeFetchResponse> {
  const { url, method = 'GET', headers = {}, body, timeoutMs = DEFAULT_TIMEOUT_MS } = opts;

  const u = new URL(url);
  const allow = parseAllowList();
  if (!isHostAllowed(u.hostname, allow)) {
    throw new Error(`Blocked host: ${u.hostname}`);
  }

  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(new Error('Request timed out')), timeoutMs);

  const init: RequestInit = {
    method,
    headers: { ...headers },
    signal: controller.signal,
  };

  if (body !== undefined && method !== 'GET') {
    if (typeof body === 'string' || body instanceof Uint8Array) {
      (init as any).body = body as any;
    } else {
      (init as any).body = JSON.stringify(body);
      if (!init.headers) init.headers = {};
      if (!('content-type' in Object.fromEntries(Object.entries(init.headers).map(([k,v]) => [k.toLowerCase(), v])))) {
        (init.headers as Record<string,string>)['content-type'] = 'application/json';
      }
    }
  }

  let res: Response | null = null;
  try {
    res = await fetch(u.toString(), init);
  } finally {
    clearTimeout(t);
  }

  const text = await res.text();
  const headersRecord: Record<string, string> = {};
  res.headers.forEach((value, key) => {
    headersRecord[key] = value;
  });

  return {
    status: res.status,
    headers: headersRecord,
    body: text,
  };
}
