import { querySimilar } from './client.js';

export interface VectorQueryArgs {
  query: string;
  k?: number;
}

export interface VectorQueryResult {
  results: Array<{ id: string; text: string; score: number; meta?: any }>
}

export async function vectorTool(args: VectorQueryArgs): Promise<VectorQueryResult> {
  const { query, k = 5 } = args;
  const results = await querySimilar(query, k);
  return { results };
}
