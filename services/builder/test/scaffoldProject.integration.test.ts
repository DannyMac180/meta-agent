import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { GenericContainer, StartedTestContainer } from 'testcontainers';
import { scaffoldProject } from '../src/handlers/scaffoldProject.js';
import { createTestS3, putObjectStream, artifactKey } from '@metaagent/object-storage';
import { CreateBucketCommand } from '@aws-sdk/client-s3';
import fs from 'fs-extra';
import path from 'node:path';
import JSZip from 'jszip';

describe('ScaffoldProject Integration', () => {
  let minioContainer: StartedTestContainer;
  let minioEndpoint: string;
  let s3: ReturnType<typeof createTestS3>;
  const testBucket = 'test-bucket';

  beforeAll(async () => {
    // Start MinIO container
    minioContainer = await new GenericContainer('minio/minio:latest')
      .withCommand(['server', '/data'])
      .withEnvironment({
        'MINIO_ROOT_USER': 'minioadmin',
        'MINIO_ROOT_PASSWORD': 'minioadmin'
      })
      .withExposedPorts(9000)
      .start();

    const port = minioContainer.getMappedPort(9000);
    minioEndpoint = `http://localhost:${port}`;
    s3 = createTestS3(minioEndpoint);

    // Create test bucket
    await s3.send(new CreateBucketCommand({ Bucket: testBucket }));
  }, 30000);

  afterAll(async () => {
    if (minioContainer) {
      await minioContainer.stop();
    }
  });

  it('scaffolds chatbot template and produces valid zip', async () => {
    const draft = {
      title: 'Test Chatbot',
      payload: {
        specVersion: '0.1.0',
        meta: {
          id: 'test-123',
          name: 'test-chatbot',
          description: 'A test chatbot',
          version: '1.0.0',
        },
        variables: [],
        prompt: {
          template: 'You are a helpful test assistant.',
        },
        model: {
          provider: 'openai',
          model: 'gpt-4',
        },
      },
    };

    const result = await scaffoldProject({
      templateId: 'chatbot',
      draft,
      buildId: 'test-build-123',
    });

    expect(result.outDir).toBeDefined();
    expect(result.zipPath).toBeDefined();
    expect(await fs.pathExists(result.outDir)).toBe(true);
    expect(await fs.pathExists(result.zipPath)).toBe(true);

    // Check zip contents
    const zipBuffer = await fs.readFile(result.zipPath);
    const zip = await JSZip.loadAsync(zipBuffer);

    // Required files should exist
    expect(zip.file('package.json')).toBeTruthy();
    expect(zip.file('tsconfig.json')).toBeTruthy();
    expect(zip.file('src/mastra/index.ts')).toBeTruthy();
    expect(zip.file('README.md')).toBeTruthy();
    expect(zip.file('.env.example')).toBeTruthy();

    // Check package.json has correct placeholders filled
    const pkgContent = await zip.file('package.json')!.async('string');
    const pkg = JSON.parse(pkgContent);
    expect(pkg.name).toBe('test-chatbot');
    expect(pkg.version).toBe('1.0.0');

    // Check README has title
    const readmeContent = await zip.file('README.md')!.async('string');
    expect(readmeContent).toContain('# Test Chatbot');
    expect(readmeContent).toContain('A test chatbot');
  });

  it('uploads zip to S3/MinIO and validates key structure', async () => {
    const userId = 'user-123';
    const draftId = 'draft-456';
    const buildId = 'build-789';
    const filename = 'test-project.zip';

    // Create a test zip
    const zip = new JSZip();
    zip.file('package.json', JSON.stringify({ name: 'test', version: '1.0.0' }));
    const zipBuffer = await zip.generateAsync({ type: 'nodebuffer' });

    const key = artifactKey({ userId, draftId, buildId, filename });
    expect(key).toBe(`scaffolds/${userId}/${draftId}/${buildId}/${filename}`);

    const result = await putObjectStream({
      s3,
      bucket: testBucket,
      key,
      body: zipBuffer,
      contentType: 'application/zip',
    });

    expect(result.etag).toBeDefined();
  });

  it('validates placeholder injection with complex spec', async () => {
    const draft = {
      title: 'Complex Agent',
      payload: {
        specVersion: '0.1.0',
        meta: {
          id: 'complex-123',
          name: 'complex-agent',
          description: 'A complex test agent with variables',
          version: '2.5.1',
        },
        variables: [
          {
            key: 'api-key',
            name: 'API Key',
            description: 'The API key for external service',
            required: true,
          },
          {
            key: 'max-retries',
            name: 'Max Retries',
            description: 'Maximum number of retries',
            required: false,
          },
        ],
      },
    };

    const result = await scaffoldProject({
      templateId: 'api-copilot',
      draft,
      buildId: 'complex-build',
    });

    const zipBuffer = await fs.readFile(result.zipPath);
    const zip = await JSZip.loadAsync(zipBuffer);

    // Check package.json placeholders
    const pkgContent = await zip.file('package.json')!.async('string');
    const pkg = JSON.parse(pkgContent);
    expect(pkg.name).toBe('complex-agent');
    expect(pkg.version).toBe('2.5.1');

    // Check README mentions variables
    const readmeContent = await zip.file('README.md')!.async('string');
    expect(readmeContent).toContain('Complex Agent');
    expect(readmeContent).toContain('A complex test agent with variables');
    expect(readmeContent).toContain('API Key (api-key)');
  });

  it('handles missing values with defaults', async () => {
    const draft = {
      title: 'Minimal Agent',
      payload: {
        specVersion: '0.1.0',
        meta: {
          id: 'minimal-123',
          name: 'minimal-agent',
          // description missing - should use default
          // version missing - should use default
        },
      },
    };

    const result = await scaffoldProject({
      templateId: 'chatbot',
      draft,
      buildId: 'minimal-build',
    });

    const zipBuffer = await fs.readFile(result.zipPath);
    const zip = await JSZip.loadAsync(zipBuffer);

    const pkgContent = await zip.file('package.json')!.async('string');
    const pkg = JSON.parse(pkgContent);
    expect(pkg.name).toBe('minimal-agent');
    expect(pkg.version).toBe('1.0.0'); // default

    const readmeContent = await zip.file('README.md')!.async('string');
    expect(readmeContent).toContain('A friendly chatbot assistant'); // default
  });
});
