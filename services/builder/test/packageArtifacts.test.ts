import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "fs-extra";
import path from "node:path";
import os from "node:os";
import { packageArtifacts, defaultDockerTag } from "../src/handlers/packageArtifacts.js";

describe("packageArtifacts", () => {
  let tempRoot: string;

  beforeEach(async () => {
    process.env.MOCK_DOCKER_BUILD = "1";
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "metaagent-package-"));
  });

  afterEach(async () => {
    delete process.env.MOCK_DOCKER_BUILD;
    await fs.remove(tempRoot);
  });

  async function setupProject() {
    const projectDir = path.join(tempRoot, "project");
    await fs.ensureDir(projectDir);
    await fs.writeJson(path.join(projectDir, "package.json"), {
      name: "test-agent",
      version: "1.0.0",
      scripts: { build: "echo build" },
    });
    await fs.writeFile(path.join(projectDir, "README.md"), "# Test Agent\n");
    const zipPath = path.join(tempRoot, "project.zip");
    await fs.writeFile(zipPath, "zip-content");
    return { projectDir, zipPath };
  }

  it("returns zip path when docker packaging disabled", async () => {
    const { projectDir, zipPath } = await setupProject();

    const result = await packageArtifacts({
      projectDir,
      zipPath,
      buildId: "build-123",
      draftId: "draft-123",
    });

    expect(result.zipPath).toBe(zipPath);
    expect(result.dockerTarPath).toBeUndefined();
    expect(result.imageTag).toBeUndefined();
  });

  it("creates docker tar archive when docker packaging enabled (mocked)", async () => {
    const { projectDir, zipPath } = await setupProject();

    const result = await packageArtifacts({
      projectDir,
      zipPath,
      buildId: "build-456",
      draftId: "Draft With Spaces",
      docker: { enabled: true },
    });

    expect(result.zipPath).toBe(zipPath);
    expect(result.dockerTarPath).toBeDefined();
    expect(result.imageTag).toBeDefined();
    expect(result.imageTag).toContain("metaagent/");
    expect(result.imageTag).toContain(":");
    expect(await fs.pathExists(result.dockerTarPath!)).toBe(true);
  });
});

describe("defaultDockerTag", () => {
  it("sanitizes repository and tag segments", () => {
    const tag = defaultDockerTag("User:ID With Spaces", "Build ID 123");
    expect(tag).toBe("metaagent/user-id-with-spaces:build-id-123");
  });
});
