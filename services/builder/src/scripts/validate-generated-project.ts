#!/usr/bin/env ts-node-esm
import path from "node:path";
import fs from "fs-extra";

async function validateGeneratedProject(projectDir: string): Promise<{ valid: boolean; errors: string[] }> {
  const errors: string[] = [];

  try {
    // Check required files exist
    const requiredFiles = [
      "package.json",
      "tsconfig.json", 
      "src/mastra/index.ts",
      "README.md",
      ".env.example"
    ];

    for (const file of requiredFiles) {
      const filePath = path.join(projectDir, file);
      if (!(await fs.pathExists(filePath))) {
        errors.push(`Missing required file: ${file}`);
      }
    }

    // Validate package.json structure
    const pkgPath = path.join(projectDir, "package.json");
    if (await fs.pathExists(pkgPath)) {
      try {
        const pkg = await fs.readJson(pkgPath);
        if (!pkg.name) errors.push("package.json missing name field");
        if (!pkg.scripts?.build) errors.push("package.json missing build script"); 
        if (!pkg.scripts?.dev) errors.push("package.json missing dev script");
        if (!pkg.dependencies?.["@mastra/core"]) errors.push("package.json missing @mastra/core dependency");
        if (!pkg.devDependencies?.["typescript"]) errors.push("package.json missing typescript devDependency");
      } catch (e) {
        errors.push("Invalid package.json format");
      }
    }

    // Validate tsconfig.json structure  
    const tsconfigPath = path.join(projectDir, "tsconfig.json");
    if (await fs.pathExists(tsconfigPath)) {
      try {
        const tsconfig = await fs.readJson(tsconfigPath);
        if (!tsconfig.compilerOptions) errors.push("tsconfig.json missing compilerOptions");
        if (!tsconfig.include) errors.push("tsconfig.json missing include");
      } catch (e) {
        errors.push("Invalid tsconfig.json format");
      }
    }

    // Validate main entry point
    const entryPath = path.join(projectDir, "src/mastra/index.ts");
    if (await fs.pathExists(entryPath)) {
      const content = await fs.readFile(entryPath, "utf8");
      if (!content.includes("@mastra/core")) {
        errors.push("Entry point does not import @mastra/core");
      }
      if (!content.includes("export default")) {
        errors.push("Entry point does not export default Mastra instance");
      }
    }

    return { valid: errors.length === 0, errors };
  } catch (error) {
    errors.push(`Validation failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    return { valid: false, errors };
  }
}

async function main() {
  const projectDir = process.argv[2];
  if (!projectDir) {
    console.error("Usage: validate-generated-project <project-directory>");
    process.exit(1);
  }

  const result = await validateGeneratedProject(path.resolve(projectDir));
  
  if (result.valid) {
    console.log("✅ Generated project validation passed");
    console.log("Project structure meets Mastra requirements");
    process.exit(0);
  } else {
    console.error("❌ Generated project validation failed:");
    result.errors.forEach(err => console.error(`  - ${err}`));
    process.exit(1);
  }
}

main().catch(err => {
  console.error("Validation script error:", err);
  process.exit(1);
});
