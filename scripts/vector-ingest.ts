import 'dotenv/config';
import { upsertDocument } from '@metaagent/tools-vector/dist/client.js';
import fs from 'node:fs/promises';
import path from 'node:path';

async function main() {
  const file = process.argv[2];
  if (!file) {
    console.error('Usage: pnpm ingest <file>');
    process.exit(1);
  }
  const p = path.resolve(process.cwd(), file);
  const text = await fs.readFile(p, 'utf8');
  const id = await upsertDocument({ text, meta: { source: p } });
  console.log('stored id', id);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
