import 'dotenv/config';
import { vectorTool } from '@metaagent/tools-vector/dist/tool.js';

async function main() {
  const query = process.argv.slice(2).join(' ').trim();
  if (!query) {
    console.error('Usage: pnpm query <text>');
    process.exit(1);
  }
  const { results } = await vectorTool({ query });
  console.table(results.map(r => ({ id: r.id, score: Number(r.score.toFixed(4)), text: r.text.slice(0, 120) })));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
