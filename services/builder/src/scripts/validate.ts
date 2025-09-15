#!/usr/bin/env ts-node-esm

// Validation stub for generated project zips
// This is a placeholder that will be replaced with real Mastra validation in Week 6

import fs from 'fs-extra';
import path from 'node:path';
import JSZip from 'jszip';

async function validateZip(zipPath: string): Promise<{ valid: boolean; errors: string[] }> {
  const errors: string[] = [];
  
  if (!await fs.pathExists(zipPath)) {
    errors.push(`Zip file not found: ${zipPath}`);
    return { valid: false, errors };
  }

  try {
    const buffer = await fs.readFile(zipPath);
    const zip = await JSZip.loadAsync(buffer);
    
    // Basic structure validation
    const requiredFiles = ['package.json', 'spec.json', 'src/index.ts', 'test/basic.test.ts'];
    for (const file of requiredFiles) {
      if (!zip.file(file)) {
        errors.push(`Missing required file: ${file}`);
      }
    }

    // Validate package.json structure
    const pkgFile = zip.file('package.json');
    if (pkgFile) {
      const pkgContent = await pkgFile.async('string');
      try {
        const pkg = JSON.parse(pkgContent);
        if (!pkg.name) errors.push('package.json missing name field');
        if (!pkg.scripts?.build) errors.push('package.json missing build script');
        if (!pkg.scripts?.test) errors.push('package.json missing test script');
      } catch (e) {
        errors.push('Invalid package.json format');
      }
    }

    // Validate spec.json structure
    const specFile = zip.file('spec.json');
    if (specFile) {
      const specContent = await specFile.async('string');
      try {
        const spec = JSON.parse(specContent);
        if (!spec.meta?.id) errors.push('spec.json missing meta.id');
        if (!spec.meta?.name) errors.push('spec.json missing meta.name');
      } catch (e) {
        errors.push('Invalid spec.json format');
      }
    }

  } catch (e) {
    errors.push(`Failed to read zip: ${e instanceof Error ? e.message : 'Unknown error'}`);
  }

  return { valid: errors.length === 0, errors };
}

async function main() {
  const zipPath = process.argv[2];
  if (!zipPath) {
    console.error('Usage: npx mastra validate <path-to-zip>');
    process.exit(1);
  }

  const result = await validateZip(path.resolve(zipPath));
  
  if (result.valid) {
    console.log('✅ Validation passed');
    process.exit(0);
  } else {
    console.error('❌ Validation failed:');
    result.errors.forEach(err => console.error(`  - ${err}`));
    process.exit(1);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
