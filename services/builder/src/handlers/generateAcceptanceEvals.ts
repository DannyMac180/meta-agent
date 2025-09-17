import path from "node:path";
import fs from "fs-extra";
import type { AcceptanceEval, AcceptanceEvalAssertion } from "@metaagent/spec";
import { AcceptanceEvalArraySchema } from "@metaagent/spec";
import templates from "@metaagent/templates";

interface GenerateAcceptanceEvalsInput {
  projectDir: string;
  templateId: string;
  draft: {
    title?: string;
    payload?: unknown;
  };
}

const HELPERS_FILENAME = "_helpers.ts";
const SPEC_SNAPSHOT_FILENAME = "specSnapshot.ts";

export async function generateAcceptanceEvals(input: GenerateAcceptanceEvalsInput): Promise<void> {
  const evalDir = path.join(input.projectDir, "tests", "evals");
  await fs.ensureDir(evalDir);

  const specPayload = (input.draft?.payload ?? {}) as Record<string, unknown>;

  const specAcceptance = AcceptanceEvalArraySchema.safeParse((specPayload as any).acceptanceEvals);
  const templateAcceptance = findTemplateAcceptance(input.templateId);

  const acceptanceEvals: AcceptanceEval[] =
    specAcceptance.success && specAcceptance.data.length > 0
      ? specAcceptance.data
      : templateAcceptance;

  if (acceptanceEvals.length === 0) {
    await ensureHelpers(evalDir);
    await writeSpecSnapshot(evalDir, specPayload);
    return;
  }

  await ensureHelpers(evalDir);
  await writeSpecSnapshot(evalDir, specPayload);

  for (const evalDef of acceptanceEvals) {
    const fileName = createEvalFileName(evalDef.id);
    const filePath = path.join(evalDir, fileName);
    const content = buildEvalTestFile(evalDef);
    await fs.writeFile(filePath, content, "utf8");
  }
}

function findTemplateAcceptance(templateId: string): AcceptanceEval[] {
  const template = templates.find((tpl) => tpl.id === templateId);
  if (!template?.acceptanceEvals || template.acceptanceEvals.length === 0) {
    return [];
  }
  const result = AcceptanceEvalArraySchema.safeParse(template.acceptanceEvals);
  return result.success ? result.data : [];
}

function createEvalFileName(id: string): string {
  const safeId = id
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${safeId || "acceptance"}.test.ts`;
}

async function ensureHelpers(evalDir: string): Promise<void> {
  const helpersPath = path.join(evalDir, HELPERS_FILENAME);
  const content = `export function getValueAtPath(obj: unknown, path: string): unknown {\n  if (!path) return obj;\n  return path.split('.').reduce<unknown>((acc, key) => {\n    if (acc == null) return undefined;\n    if (Array.isArray(acc)) {\n      const index = Number.parseInt(key, 10);\n      if (Number.isNaN(index)) return undefined;\n      return acc[index];\n    }\n    return (acc as Record<string, unknown>)[key];\n  }, obj);\n}\n`;
  await fs.writeFile(helpersPath, content, "utf8");
}

async function writeSpecSnapshot(evalDir: string, payload: Record<string, unknown>): Promise<void> {
  const specSnapshotPath = path.join(evalDir, SPEC_SNAPSHOT_FILENAME);
  const serialized = JSON.stringify(payload ?? {}, null, 2);
  const content = `export const specSnapshot = ${serialized} as const;\n`;
  await fs.writeFile(specSnapshotPath, content, "utf8");
}

function buildEvalTestFile(evalDef: AcceptanceEval): string {
  const lines: string[] = [
    "import { describe, it, expect } from 'vitest';",
    "import { specSnapshot } from './specSnapshot';",
    "import { getValueAtPath } from './_helpers';",
    "",
    `describe(${JSON.stringify(`Acceptance: ${evalDef.title}`)}, () => {`,
  ];

  evalDef.assertions.forEach((assertion) => {
    lines.push(buildAssertionBlock(assertion));
  });

  lines.push("});", "");
  return lines.join("\n");
}

function buildAssertionBlock(assertion: AcceptanceEvalAssertion): string {
  const description = JSON.stringify(assertion.message ?? defaultAssertionMessage(assertion));
  const pathLiteral = JSON.stringify(assertion.path);
  const lines: string[] = [
    `  it(${description}, () => {`,
    `    const value = getValueAtPath(specSnapshot, ${pathLiteral});`,
  ];

  switch (assertion.kind) {
    case "string-not-empty":
      lines.push(
        "    expect(typeof value).toBe('string');",
        "    expect(String(value).trim().length).toBeGreaterThan(0);",
      );
      break;
    case "string-contains": {
      const needle = JSON.stringify(assertion.caseSensitive ? assertion.value : assertion.value.toLowerCase());
      if (assertion.caseSensitive) {
        lines.push("    expect(typeof value).toBe('string');", `    expect(String(value)).toContain(${needle});`);
      } else {
        lines.push(
          "    expect(typeof value).toBe('string');",
          "    const haystack = String(value).toLowerCase();",
          `    expect(haystack).toContain(${needle});`,
        );
      }
      break;
    }
    case "number-gte":
      lines.push(
        "    expect(typeof value).toBe('number');",
        `    expect(value as number).toBeGreaterThanOrEqual(${assertion.value});`,
      );
      break;
    case "number-lte":
      lines.push(
        "    expect(typeof value).toBe('number');",
        `    expect(value as number).toBeLessThanOrEqual(${assertion.value});`,
      );
      break;
    case "array-min-length":
      lines.push(
        "    expect(Array.isArray(value)).toBe(true);",
        `    expect((value as unknown[]).length).toBeGreaterThanOrEqual(${assertion.min});`,
      );
      break;
    case "equals":
      lines.push(`    expect(value).toEqual(${JSON.stringify(assertion.value)});`);
      break;
    default:
      lines.push("    throw new Error('Unsupported assertion kind encountered');");
      break;
  }

  lines.push("  });");
  return lines.join("\n");
}

function defaultAssertionMessage(assertion: AcceptanceEvalAssertion): string {
  switch (assertion.kind) {
    case "string-not-empty":
      return `Value at ${assertion.path} should be a non-empty string.`;
    case "string-contains":
      return `Value at ${assertion.path} should contain ${assertion.value}.`;
    case "number-gte":
      return `Value at ${assertion.path} should be at least ${assertion.value}.`;
    case "number-lte":
      return `Value at ${assertion.path} should be at most ${assertion.value}.`;
    case "array-min-length":
      return `Array at ${assertion.path} should have at least ${assertion.min} item(s).`;
    case "equals":
      return `Value at ${assertion.path} should equal ${assertion.value}.`;
    default:
      return `Assertion should pass.`;
  }
}
