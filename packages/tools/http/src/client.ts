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

export function validateAllowList(): { isValid: boolean; error?: string } {
  const raw = process.env.ALLOW_HTTP_HOSTS?.trim();
  if (!raw) {
    return { isValid: false, error: 'ALLOW_HTTP_HOSTS is empty - all external HTTP requests will be blocked' };
  }

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return { isValid: false, error: 'ALLOW_HTTP_HOSTS JSON must be an array' };
    }
    if (parsed.length === 0) {
      return { isValid: false, error: 'ALLOW_HTTP_HOSTS array is empty - all external HTTP requests will be blocked' };
    }
    // Validate each host pattern
    for (const host of parsed) {
      if (typeof host !== 'string' || !host.trim()) {
        return { isValid: false, error: `Invalid host pattern: ${JSON.stringify(host)}` };
      }
    }
    return { isValid: true };
  } catch (error) {
    // Try comma-separated fallback
    const hosts = raw.split(',').map(s => s.trim()).filter(Boolean);
    if (hosts.length === 0) {
      return { isValid: false, error: 'ALLOW_HTTP_HOSTS is empty - all external HTTP requests will be blocked' };
    }
    return { isValid: true };
  }
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
    // Log blocked request for security monitoring
    console.warn(`[SECURITY] Blocked HTTP request to disallowed host: ${u.hostname} (${method} ${url})`);
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
