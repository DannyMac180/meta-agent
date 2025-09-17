import { describe, it, expect, afterEach } from 'vitest';
import fs from 'fs-extra';
import os from 'node:os';
import path from 'node:path';
import { generateAcceptanceEvals } from '../src/handlers/generateAcceptanceEvals.js';

let tempDirs: string[] = [];

afterEach(async () => {
  for (const dir of tempDirs) {
    await fs.remove(dir);
  }
  tempDirs = [];
});

describe('generateAcceptanceEvals', () => {
  it('creates eval tests from spec acceptance definitions', async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'acceptance-evals-'));
    tempDirs.push(tmpDir);

    const evalDefinition = {
      id: 'custom-check',
      title: 'Custom acceptance check',
      assertions: [
        { kind: 'string-not-empty', path: 'prompt.template' },
        { kind: 'equals', path: 'meta.name', value: 'custom-agent' },
      ],
    };

    await generateAcceptanceEvals({
      projectDir: tmpDir,
      templateId: 'chatbot',
      draft: {
        payload: {
          prompt: { template: 'Hello world' },
          meta: { name: 'custom-agent' },
          acceptanceEvals: [evalDefinition],
        },
      },
    });

    const evalDir = path.join(tmpDir, 'tests', 'evals');
    const files = await fs.readdir(evalDir);
    expect(files).toContain('custom-check.test.ts');
    expect(files).toContain('_helpers.ts');
    expect(files).toContain('specSnapshot.ts');

    const testFileContent = await fs.readFile(path.join(evalDir, 'custom-check.test.ts'), 'utf8');
    expect(testFileContent).toContain('Acceptance: Custom acceptance check');
    expect(testFileContent).toContain('expect(value).toEqual("custom-agent")');

    const snapshotContent = await fs.readFile(path.join(evalDir, 'specSnapshot.ts'), 'utf8');
    expect(snapshotContent).toContain('custom-agent');
  });
});
