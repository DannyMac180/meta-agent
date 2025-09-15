import { searchWeb } from './client';

export interface WebSearchArgs {
  query: string;
  numResults?: number;
}

export interface WebSearchResult {
  results: Array<{ title: string; url: string; snippet: string }>;
}

export async function webSearchTool(args: WebSearchArgs): Promise<WebSearchResult> {
  const { query, numResults = 5 } = args;
  const results = await searchWeb(query, numResults);
  return { results };
}
