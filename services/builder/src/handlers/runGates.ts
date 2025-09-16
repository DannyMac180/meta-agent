import { createDefaultGateRunner, GateContext, GateRunResult } from "@metaagent/gates";
import { db, gateResults, gateRuns } from "@metaagent/db";
import fs from "fs-extra";
import path from "path";

export async function runGatesOnProject(projectPath: string): Promise<GateRunResult> {
  // Read package.json for context
  let packageJson: any = {};
  try {
    const packageJsonPath = path.join(projectPath, 'package.json');
    const packageJsonContent = await fs.readFile(packageJsonPath, 'utf-8');
    packageJson = JSON.parse(packageJsonContent);
  } catch (error) {
    // package.json not found or invalid, continue with empty object
  }

  const context: GateContext = {
    projectPath,
    packageJson,
    tempDir: projectPath, // Use project path as temp dir for now
  };

  const runner = createDefaultGateRunner();
  return runner.run(context);
}

export async function runGatesOnZip(zipPath: string, tempDir: string, draftId?: string, buildId?: string): Promise<GateRunResult> {
  // Extract zip to temp directory
  const extractPath = path.join(tempDir, `extracted-${Date.now()}`);
  await fs.ensureDir(extractPath);

  try {
    // Use JSZip to extract the zip file
    const JSZip = await import('jszip');
    const zipData = await fs.readFile(zipPath);
    const zip = await JSZip.default.loadAsync(zipData);

    // Extract all files
    for (const [relativePath, file] of Object.entries(zip.files)) {
      if (!file.dir) {
        const fullPath = path.join(extractPath, relativePath);
        await fs.ensureDir(path.dirname(fullPath));
        const content = await file.async('nodebuffer');
        await fs.writeFile(fullPath, content);
      }
    }

    // Run gates on extracted project
    const result = await runGatesOnProject(extractPath);

    // Store results in database if draftId and buildId are provided
    if (draftId && buildId) {
      await storeGateResults(result, draftId, buildId);
    }

    return result;
  } finally {
    // Clean up extracted files
    try {
      await fs.remove(extractPath);
    } catch (error) {
      console.warn(`Failed to clean up temp directory ${extractPath}:`, error);
    }
  }
}

async function storeGateResults(result: GateRunResult, draftId: string, buildId: string): Promise<void> {
  try {
    // Store overall gate run result
    await db.insert(gateRuns).values({
      draftId,
      buildId,
      success: result.success,
      totalDurationMs: result.totalDuration,
      failedGate: result.failedGate || null,
    });

    // Store individual gate results
    for (const gateResult of result.results) {
      await db.insert(gateResults).values({
        draftId,
        buildId,
        gateName: gateResult.gate,
        passed: gateResult.passed,
        durationMs: gateResult.duration,
        errors: gateResult.errors || null,
        warnings: gateResult.warnings || null,
        metadata: gateResult.metadata || null,
      });
    }
  } catch (error) {
    console.error('Failed to store gate results in database:', error);
    // Don't throw here - we don't want to fail the build just because we couldn't store the results
  }
}
