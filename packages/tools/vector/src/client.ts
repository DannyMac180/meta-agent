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
  const id = doc.id ?? ulid();
  const embedding = await embedText(doc.text);
  const client = await pool.connect();
  try {
    await client.query(
      `insert into documents (id, text, meta, embedding)
       values ($1::uuid, $2, $3::jsonb, $4)
       on conflict (id) do update set text = excluded.text, meta = excluded.meta, embedding = excluded.embedding`,
      [id, doc.text, doc.meta ?? null, embedding]
    );
  } finally {
    client.release();
  }
  return id;
}

export async function querySimilar(query: string, k: number = 5): Promise<Array<{ id: string; text: string; score: number; meta: any }>> {
  const qvec = await embedText(query);
  const client = await pool.connect();
  try {
    const res = await client.query(
      `select id::text, text, meta, 1 - (embedding <=> $1) as score
       from documents
       order by embedding <=> $1 asc
       limit $2`,
      [qvec, k]
    );
    return res.rows.map(r => ({ id: r.id, text: r.text, score: Number(r.score), meta: r.meta }));
  } finally {
    client.release();
  }
}
