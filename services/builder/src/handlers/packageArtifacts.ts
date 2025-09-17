import fs from "fs-extra";
import path from "node:path";
import os from "node:os";
import { spawn } from "node:child_process";

export interface DockerPackageConfig {
  enabled: boolean;
  imageTag?: string;
}

export interface PackageArtifactsParams {
  projectDir: string;
  zipPath: string;
  buildId: string;
  draftId: string;
  docker?: DockerPackageConfig;
}

export interface PackageArtifactsOutput {
  zipPath: string;
  dockerTarPath?: string;
  imageTag?: string;
}

const DOCKERFILE_CONTENT = `# syntax=docker/dockerfile:1
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
CMD ["node", "dist/mastra/index.js"]
`;

function sanitizeForTagSegment(value: string): string {
  const cleaned = value
    .toLowerCase()
    .replace(/[^a-z0-9_.-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return cleaned || "app";
}

async function run(command: string, args: string[], options: { cwd?: string; env?: NodeJS.ProcessEnv } = {}) {
  return new Promise<void>((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      env: { ...process.env, ...options.env },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) return resolve();
      const err = new Error(`${command} ${args.join(" ")} exited with code ${code}\n${stderr}`);
      reject(err);
    });
  });
}

async function buildDockerImage(contextDir: string, dockerfilePath: string, imageTag: string) {
  if (process.env.MOCK_DOCKER_BUILD === "1") {
    return;
  }
  await run("docker", ["build", "-t", imageTag, "-f", dockerfilePath, "."], { cwd: contextDir });
}

async function saveDockerImage(imageTag: string, tarPath: string) {
  if (process.env.MOCK_DOCKER_BUILD === "1") {
    await fs.ensureDir(path.dirname(tarPath));
    await fs.writeJson(tarPath, { mock: true, imageTag, createdAt: new Date().toISOString() }, { spaces: 2 });
    return;
  }
  await run("docker", ["image", "save", imageTag, "-o", tarPath]);
}

async function removeDockerImage(imageTag: string) {
  if (process.env.MOCK_DOCKER_BUILD === "1") {
    return;
  }
  try {
    await run("docker", ["image", "rm", "-f", imageTag]);
  } catch (err) {
    // ignore cleanup failures
  }
}

export function defaultDockerTag(draftId: string, buildId: string): string {
  const repo = sanitizeForTagSegment(draftId);
  const tag = sanitizeForTagSegment(buildId);
  return `metaagent/${repo}:${tag}`;
}

export async function packageArtifacts(params: PackageArtifactsParams): Promise<PackageArtifactsOutput> {
  const { projectDir, zipPath, docker, buildId } = params;

  const outputs: PackageArtifactsOutput = { zipPath };

  if (docker?.enabled) {
    const imageTag = docker.imageTag && docker.imageTag.trim().length > 0 ? docker.imageTag : defaultDockerTag(params.draftId, buildId);
    const tmpRoot = path.join(path.resolve(projectDir, ".."), "docker-packaging");
    await fs.ensureDir(tmpRoot);
    const contextDir = await fs.mkdtemp(path.join(os.tmpdir(), "metaagent-docker-"));
    try {
      await fs.copy(projectDir, contextDir, { dereference: false, preserveTimestamps: true });
      const dockerfilePath = path.join(contextDir, "Dockerfile");
      await fs.writeFile(dockerfilePath, DOCKERFILE_CONTENT, "utf8");

      await buildDockerImage(contextDir, dockerfilePath, imageTag);

      const tarName = `${sanitizeForTagSegment(buildId)}-image.tar`;
      const tarPath = path.join(tmpRoot, tarName);
      await fs.ensureDir(path.dirname(tarPath));
      await saveDockerImage(imageTag, tarPath);
      outputs.dockerTarPath = tarPath;
      outputs.imageTag = imageTag;
    } finally {
      await removeDockerImage(imageTag);
      await fs.remove(contextDir);
    }
  }

  return outputs;
}
