#!/usr/bin/env ts-node-esm
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'fs-extra';
import JSZip from 'jszip';
import { templates } from '@metaagent/templates';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface Args {
  template: string;
  out?: string;
  name?: string;
  description?: string;
}

function parseArgs(argv: string[]): Args {
  const args: Args = { template: '' } as Args;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--template' || a === '-t') args.template = argv[++i];
    else if (a === '--out' || a === '-o') args.out = argv[++i];
    else if (a === '--name' || a === '-n') args.name = argv[++i];
    else if (a === '--description' || a === '-d') args.description = argv[++i];
  }
  return args;
}

function findTemplate(id: string) {
  const t = templates.find(x => x.id === id);
  if (!t) {
    const ids = templates.map(x => x.id).join(', ');
    throw new Error(`Unknown template '${id}'. Available: ${ids}`);
  }
  return t;
}

async function createTree(opts: { id: string; outDir: string; name?: string; description?: string; }) {
  const t = findTemplate(opts.id);
  const spec = t.defaultSpec.payload;
  const projectName = opts.name || spec.meta.name || `${t.id}-project`;
  const description = opts.description || spec.meta.description || t.description;

  const root = opts.outDir;
  await fs.emptyDir(root);
  await fs.ensureDir(path.join(root, 'src'));
  await fs.ensureDir(path.join(root, 'test'));

  const pkg = {
    name: projectName,
    version: '1.0.0',
    private: true,
    type: 'module',
    scripts: {
      build: 'tsc -p .',
      start: 'node dist/index.js',
      test: 'vitest run'
    },
    dependencies: {},
    devDependencies: {
      typescript: '^5.3.3',
      vitest: '^2.0.5',
      '@types/node': '^20.14.10'
    }
  } as any;

  const tsconfig = {
    compilerOptions: {
      target: 'ES2022',
      module: 'ESNext',
      moduleResolution: 'Bundler',
      strict: true,
      outDir: 'dist',
      rootDir: 'src',
      esModuleInterop: true,
      skipLibCheck: true
    },
    include: ['src']
  };

  const readme = `# ${projectName}\n\n${description}\n\nTemplate: ${t.name}\n`;

  const agentTs = `export async function run(input: string) {\n  return { ok: true, echo: input };\n}\n`;

  await fs.writeJson(path.join(root, 'package.json'), pkg, { spaces: 2 });
  await fs.writeJson(path.join(root, 'tsconfig.json'), tsconfig, { spaces: 2 });
  await fs.writeFile(path.join(root, 'README.md'), readme);
  await fs.writeJson(path.join(root, 'spec.json'), spec, { spaces: 2 });
  await fs.writeFile(path.join(root, 'src', 'index.ts'), agentTs);
  await fs.writeFile(path.join(root, 'test', 'basic.test.ts'), `import { describe, it, expect } from 'vitest';\nimport { run } from '../src/index';\n\ndescribe('basic', () => {\n  it('echo', async () => {\n    const res = await run('hi');\n    expect(res.ok).toBe(true);\n  });\n});\n`);
}

async function zipDir(srcDir: string, outZip: string) {
  const zip = new JSZip();
  const addDir = async (dir: string, rel = '') => {
    const entries = await fs.readdir(dir);
    for (const e of entries) {
      const full = path.join(dir, e);
      const stat = await fs.stat(full);
      const relPath = path.posix.join(rel, e);
      if (stat.isDirectory()) await addDir(full, relPath);
      else zip.file(relPath, await fs.readFile(full));
    }
  };
  await addDir(srcDir);
  const content = await zip.generateAsync({ type: 'nodebuffer' });
  await fs.ensureDir(path.dirname(outZip));
  await fs.writeFile(outZip, content);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.template) {
    console.error('Usage: pnpm --filter @metaagent/builder scaffold -- --template <id> [--out <dir>] [--name <n>] [--description <d>]');
    process.exit(1);
  }
  const outDir = path.resolve(process.cwd(), args.out ?? `dist/scaffold-${args.template}-${Date.now()}`);
  await createTree({ id: args.template, outDir, name: args.name, description: args.description });
  const outZip = `${outDir}.zip`;
  await zipDir(outDir, outZip);
  console.log(JSON.stringify({ ok: true, outDir, outZip }, null, 2));
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
