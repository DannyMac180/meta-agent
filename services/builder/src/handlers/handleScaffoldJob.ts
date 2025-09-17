import { db, specDrafts, builderArtifacts, setAppUser } from "@metaagent/db";
import type { BuilderArtifact } from "@metaagent/db";
import { and, eq, inArray } from "drizzle-orm";
import fs from "fs-extra";
import path from "node:path";
import { artifactKey, putObjectStream } from "@metaagent/object-storage";
import { scaffoldProject } from "./scaffoldProject.js";
import { runGatesOnZip } from "./runGates.js";
import { packageArtifacts, defaultDockerTag } from "./packageArtifacts.js";
import type { BuilderPackagedArtifact, BuilderScaffoldJob, BuilderScaffoldResult } from "@metaagent/queue";

const ZIP_STEP = "package:zip";
const DOCKER_STEP = "package:docker";

function mapRow(row: BuilderArtifact): BuilderPackagedArtifact {
  return {
    artifactId: row.id,
    bucket: row.bucket,
    key: row.objectKey,
    sizeBytes: row.sizeBytes ?? undefined,
    etag: row.etag ?? undefined,
    step: row.step as BuilderPackagedArtifact["step"],
  };
}

interface UploadParams {
  job: BuilderScaffoldJob;
  buildId: string;
  bucket: string;
  step: string;
  filePath: string;
  contentType: string;
  filename?: string;
}

async function saveArtifact(params: UploadParams): Promise<BuilderPackagedArtifact> {
  const { job, buildId, bucket, step, filePath, contentType } = params;
  const filename = params.filename ?? path.basename(filePath);
  const key = artifactKey({ userId: job.userId, draftId: job.draftId, buildId, filename });

  const stat = await fs.stat(filePath);
  const body = await fs.readFile(filePath);
  const { etag } = await putObjectStream({ bucket, key, body, contentType });

  await db
    .delete(builderArtifacts)
    .where(and(eq(builderArtifacts.draftId, job.draftId), eq(builderArtifacts.buildId, buildId), eq(builderArtifacts.step, step)));

  const [inserted] = await db
    .insert(builderArtifacts)
    .values({
      draftId: job.draftId,
      buildId,
      step,
      bucket,
      objectKey: key,
      sizeBytes: stat.size,
      etag: etag ?? null,
    })
    .returning();

  return mapRow(inserted);
}

export async function handleBuilderScaffold(job: BuilderScaffoldJob): Promise<BuilderScaffoldResult> {
  const bucket = process.env.BUILDER_BUCKET || "metaagent-artifacts";
  const buildId = job.buildId ?? `b-${Date.now()}`;
  const includeZip = job.package?.includeZip ?? true;
  const dockerEnabled = Boolean(job.package?.docker?.enabled);
  const dockerImageTag = dockerEnabled
    ? job.package?.docker?.imageTag ?? defaultDockerTag(job.draftId, buildId)
    : undefined;

  await setAppUser(job.userId);

  const draftRows = await db
    .select()
    .from(specDrafts)
    .where(and(eq(specDrafts.id, job.draftId), eq(specDrafts.ownerUserId, job.userId)))
    .limit(1);
  const draft = draftRows[0];
  if (!draft) throw new Error(`Draft not found: ${job.draftId}`);

  const stepsToCheck: string[] = [];
  if (includeZip) stepsToCheck.push(ZIP_STEP);
  if (dockerEnabled) stepsToCheck.push(DOCKER_STEP);

  if (stepsToCheck.length > 0) {
    const existingRows = await db
      .select()
      .from(builderArtifacts)
      .where(
        and(
          eq(builderArtifacts.draftId, job.draftId),
          eq(builderArtifacts.buildId, buildId),
          inArray(builderArtifacts.step, stepsToCheck)
        )
      );

    const existingArtifacts = existingRows.map(mapRow);
    const existingZip = existingArtifacts.find((a) => a.step === ZIP_STEP);
    const existingDocker = existingArtifacts.find((a) => a.step === DOCKER_STEP);

    if ((includeZip ? Boolean(existingZip) : true) && (!dockerEnabled || existingDocker)) {
      const artifacts: BuilderPackagedArtifact[] = [];
      if (existingZip) artifacts.push(existingZip);
      if (existingDocker) artifacts.push(existingDocker);
      return {
        zip: existingZip,
        docker: existingDocker,
        artifacts,
      };
    }
  }

  const templateId = draft.templateId ?? "chatbot";
  const { outDir, zipPath } = await scaffoldProject({
    templateId,
    draft: { title: draft.title, payload: draft.spec },
    buildId,
  });

  console.log(`Running quality gates on scaffolded project: ${zipPath}`);
  const tempDir = path.dirname(zipPath);
  const gateResults = await runGatesOnZip(zipPath, tempDir, job.draftId, buildId);

  if (!gateResults.success) {
    console.log(`Quality gates failed for draft ${job.draftId}:`, gateResults);
    throw new Error(
      `Quality gates failed at ${gateResults.failedGate}: ${
        gateResults.results.find((r: any) => !r.passed)?.errors?.join(', ') || 'Unknown error'
      }`
    );
  }

  console.log(`Quality gates passed for draft ${job.draftId} in ${gateResults.totalDuration}ms`);

  const packagingResult = await packageArtifacts({
    projectDir: outDir,
    zipPath,
    buildId,
    draftId: job.draftId,
    docker: dockerEnabled ? { enabled: true, imageTag: dockerImageTag } : undefined,
  });

  const artifacts: BuilderPackagedArtifact[] = [];
  let zipArtifact: BuilderPackagedArtifact | undefined;
  let dockerArtifact: BuilderPackagedArtifact | undefined;

  if (includeZip) {
    zipArtifact = await saveArtifact({
      job,
      buildId,
      bucket,
      step: ZIP_STEP,
      filePath: packagingResult.zipPath,
      contentType: "application/zip",
    });
    artifacts.push(zipArtifact);
  }

  if (dockerEnabled && packagingResult.dockerTarPath) {
    dockerArtifact = await saveArtifact({
      job,
      buildId,
      bucket,
      step: DOCKER_STEP,
      filePath: packagingResult.dockerTarPath,
      contentType: "application/x-tar",
    });
    artifacts.push(dockerArtifact);
    await fs.remove(packagingResult.dockerTarPath).catch(() => undefined);
  }

  return {
    zip: zipArtifact,
    docker: dockerArtifact,
    artifacts,
  };
}
