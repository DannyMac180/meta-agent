import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "fs-extra";
import JSZip from "jszip";
import Handlebars from "handlebars";

export interface ScaffoldInput {
  templateId: "chatbot" | "web-automation" | "api-copilot" | string;
  draft: any; // validated spec draft payload expected
  outDir?: string; // optional override; default tmp dir
  buildId?: string;
}

export interface ScaffoldResult {
  outDir: string;
  zipPath: string;
}

function repoRootDir() {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  // services/builder/src/handlers -> repo root is ../../..
  return path.resolve(__dirname, "../../../..");
}

function templateFilesDir(templateId: string) {
  return path.join(repoRootDir(), "packages", "templates", "files", templateId);
}

function registerHelpers() {
  Handlebars.registerHelper("default", function (this: any, value: any, def: any) {
    return value != null && value !== "" ? value : def;
  });
  Handlebars.registerHelper("upper", function (this: any, value: any) {
    return typeof value === "string" ? value.toUpperCase() : value;
  });
  Handlebars.registerHelper("json", function (this: any, value: any) {
    return new Handlebars.SafeString(JSON.stringify(value ?? null));
  });
  Handlebars.registerHelper("slugify", function (this: any, value: any) {
    return String(value ?? "")
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  });
}

async function renderString(input: string, context: any) {
  const tpl = Handlebars.compile(input, { noEscape: true });
  return tpl(context);
}

async function copyAndRenderDir(src: string, dest: string, context: any) {
  const entries = await fs.readdir(src);
  await fs.ensureDir(dest);
  for (const name of entries) {
    const srcPath = path.join(src, name);
    const stat = await fs.stat(srcPath);
    // Support templated filenames
    const renderedName = await renderString(name, context);
    const destPath = path.join(dest, renderedName);
    if (stat.isDirectory()) {
      await copyAndRenderDir(srcPath, destPath, context);
    } else {
      const content = await fs.readFile(srcPath, "utf8");
      const rendered = await renderString(content, context);
      await fs.ensureDir(path.dirname(destPath));
      await fs.writeFile(destPath, rendered, "utf8");
    }
  }
}

async function validateDirectory(root: string) {
  const required = [
    "package.json",
    path.join("src", "mastra", "index.ts"),
  ];
  for (const rel of required) {
    const full = path.join(root, rel);
    if (!(await fs.pathExists(full))) {
      throw new Error(`Validation failed: missing ${rel}`);
    }
  }
  // Basic package.json checks
  const pkg = await fs.readJson(path.join(root, "package.json"));
  if (!pkg.name) throw new Error("Validation failed: package.json missing name");
  if (!pkg.scripts?.build) throw new Error("Validation failed: package.json missing build script");
}

async function zipDirectory(srcDir: string, outZip: string) {
  const zip = new JSZip();
  async function addDir(dir: string, rel = "") {
    const entries = await fs.readdir(dir);
    for (const e of entries) {
      const full = path.join(dir, e);
      const stat = await fs.stat(full);
      const relPath = path.posix.join(rel, e);
      if (stat.isDirectory()) await addDir(full, relPath);
      else zip.file(relPath, await fs.readFile(full));
    }
  }
  await addDir(srcDir);
  const content = await zip.generateAsync({ type: "nodebuffer" });
  await fs.ensureDir(path.dirname(outZip));
  await fs.writeFile(outZip, content);
}

export async function scaffoldProject(input: ScaffoldInput): Promise<ScaffoldResult> {
  registerHelpers();
  const srcDir = templateFilesDir(input.templateId);
  if (!(await fs.pathExists(srcDir))) {
    throw new Error(`Template files not found for '${input.templateId}' at ${srcDir}`);
  }

  const tmpOut = input.outDir ?? path.join(repoRootDir(), "services", "builder", "dist", "tmp-scaffold", `${input.templateId}-${Date.now()}`);
  const context = {
    ...input.draft?.payload,
    title: input.draft?.title ?? "Untitled Agent",
    buildId: input.buildId,
    templateId: input.templateId,
    mastraVersion: "latest",
    createdAt: new Date().toISOString(),
  };

  await copyAndRenderDir(srcDir, tmpOut, context);
  await validateDirectory(tmpOut);

  const outZip = `${tmpOut}.zip`;
  await zipDirectory(tmpOut, outZip);

  return { outDir: tmpOut, zipPath: outZip };
}
