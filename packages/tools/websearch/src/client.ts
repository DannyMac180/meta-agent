import { safeFetch } from '@metaagent/tools-http';

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export async function searchWeb(query: string, numResults: number = 5): Promise<SearchResult[]> {
  const apiKey = process.env.SERPER_API_KEY;
  if (!apiKey) throw new Error('SERPER_API_KEY is not set');

  const resp = await safeFetch({
    url: 'https://google.serper.dev/search',
    method: 'POST',
    headers: {
      'X-API-KEY': apiKey,
      'content-type': 'application/json',
      'accept': 'application/json',
    },
    body: { q: query, num: numResults },
  });

  if (resp.status >= 400) {
    throw new Error(`Web search failed: ${resp.status}`);
  }

  let json: any;
  try {
    json = JSON.parse(resp.body);
  } catch (e) {
    throw new Error('Invalid JSON from search provider');
  }

  const organic = Array.isArray(json.organic) ? json.organic : [];
  const results: SearchResult[] = organic.slice(0, numResults).map((item: any) => ({
    title: String(item.title ?? ''),
    url: String(item.link ?? item.url ?? ''),
    snippet: String(item.snippet ?? item.description ?? ''),
  }));

  return results;
}
