import { pool } from '@metaagent/db';
import { safeFetch } from '@metaagent/tools-http';
import { ulid } from 'ulid';

export interface VectorDoc {
  id?: string;
  text: string;
  meta?: Record<string, any>;
}

export async function embedText(text: string): Promise<number[]> {
  const apiKey = process.env.OPENAI_API_KEY;
  const model = process.env.OPENAI_EMBEDDING_MODEL || 'text-embedding-3-small';
  if (!apiKey) throw new Error('OPENAI_API_KEY is not set');

  const resp = await safeFetch({
    url: 'https://api.openai.com/v1/embeddings',
    method: 'POST',
    headers: {
      'authorization': `Bearer ${apiKey}`,
      'content-type': 'application/json',
    },
    body: { model, input: text },
  });
  if (resp.status >= 400) throw new Error(`Embedding failed: ${resp.status}`);
  const json = JSON.parse(resp.body);
  const vec = json?.data?.[0]?.embedding;
  if (!Array.isArray(vec)) throw new Error('Invalid embedding response');
  return vec.map((v: any) => Number(v));
}

export async function upsertDocument(doc: VectorDoc): Promise<string> {
  const embedding = await embedText(doc.text);
  const client = await pool.connect();
  try {
    const vec = `[${embedding.join(',')}]`;
    const res = await client.query(
      `insert into documents (text, meta, embedding)
       values ($1, $2::jsonb, $3::vector)
       returning id::text`,
      [doc.text, doc.meta ?? null, vec]
    );
    return res.rows[0].id as string;
  } finally {
    client.release();
  }
}

export async function querySimilar(query: string, k: number = 5): Promise<Array<{ id: string; text: string; score: number; meta: any }>> {
  const q = await embedText(query);
  const vec = `[${q.join(',')}]`;
  const client = await pool.connect();
  try {
    const res = await client.query(
      `select id::text, text, meta, 1 - (embedding <=> $1::vector) as score
       from documents
       order by embedding <=> $1::vector asc
       limit $2`,
      [vec, k]
    );
    return res.rows.map(r => ({ id: r.id, text: r.text, score: Number(r.score), meta: r.meta }));
  } finally {
    client.release();
  }
}
