import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';
import { Gate, GateContext, GateResult } from '../types.js';

const execAsync = promisify(exec);

// Allowlist of acceptable licenses
const ALLOWED_LICENSES = new Set([
  'MIT',
  'Apache-2.0',
  'BSD-2-Clause',
  'BSD-3-Clause',
  'ISC',
  'CC0-1.0',
  'Unlicense',
  'WTFPL',
  'Public Domain',
  '0BSD',
]);

// Known problematic licenses that should be blocked
const BLOCKED_LICENSES = new Set([
  'GPL-2.0',
  'GPL-3.0',
  'AGPL-1.0',
  'AGPL-3.0',
  'LGPL-2.0',
  'LGPL-2.1',
  'LGPL-3.0',
  'CPAL-1.0',
  'EPL-1.0',
  'EPL-2.0',
  'MPL-1.1',
  'MPL-2.0',
]);

export class LicenseGate implements Gate {
  name = 'License Scan';
  description = 'Scans dependencies for license compliance';

  async execute(context: GateContext): Promise<GateResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Method 1: Try using license-checker if available
      const licenseCheckerResult = await this.runLicenseChecker(context);
      
      if (licenseCheckerResult.ran) {
        errors.push(...licenseCheckerResult.errors);
        warnings.push(...licenseCheckerResult.warnings);
      } else {
        // Method 2: Fallback to manual package.json analysis
        const manualResult = await this.manualLicenseCheck(context);
        errors.push(...manualResult.errors);
        warnings.push(...manualResult.warnings);
      }

      const passed = errors.length === 0;
      
      return {
        gate: this.name,
        passed,
        duration: Date.now() - startTime,
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
        metadata: {
          allowedLicenses: Array.from(ALLOWED_LICENSES),
          blockedLicenses: Array.from(BLOCKED_LICENSES),
          method: licenseCheckerResult.ran ? 'license-checker' : 'manual',
        },
      };

    } catch (error: any) {
      errors.push(`License scan failed: ${error.message}`);
      
      return {
        gate: this.name,
        passed: false,
        duration: Date.now() - startTime,
        errors,
      };
    }
  }

  private async runLicenseChecker(context: GateContext): Promise<{ errors: string[], warnings: string[], ran: boolean }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Try to run license-checker
      const { stdout } = await execAsync('npx license-checker --json --excludePrivatePackages', {
        cwd: context.projectPath,
        timeout: 60000, // 1 minute timeout
      });

      if (stdout.trim()) {
        const licenses = JSON.parse(stdout);
        
        for (const [packageName, info] of Object.entries(licenses as any)) {
          const licenseInfo = info as any;
          const license = licenseInfo.licenses;
          
          if (!license || license === 'UNKNOWN') {
            warnings.push(`${packageName}: License unknown or not specified`);
            continue;
          }

          // Normalize license string (handle SPDX expressions)
          const normalizedLicense = this.normalizeLicense(license);
          
          if (BLOCKED_LICENSES.has(normalizedLicense)) {
            errors.push(`${packageName}: Uses blocked license ${license}`);
          } else if (!ALLOWED_LICENSES.has(normalizedLicense)) {
            // Unknown license, treat as warning for now
            warnings.push(`${packageName}: Uses unrecognized license ${license} - please review`);
          }
        }
      }

      return { errors, warnings, ran: true };

    } catch (error: any) {
      if (error.code === 127 || error.message?.includes('license-checker')) {
        // license-checker not available
        return { errors: [], warnings: [], ran: false };
      } else {
        warnings.push(`License checker failed: ${error.message}`);
        return { errors: [], warnings, ran: false };
      }
    }
  }

  private async manualLicenseCheck(context: GateContext): Promise<{ errors: string[], warnings: string[] }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Read package.json to get dependencies
      const packageJsonPath = path.join(context.projectPath, 'package.json');
      const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf-8'));
      
      const dependencies = {
        ...packageJson.dependencies,
        ...packageJson.devDependencies,
        ...packageJson.peerDependencies,
      };

      // Check each dependency's package.json for license info
      const nodeModulesPath = path.join(context.projectPath, 'node_modules');
      
      for (const [depName] of Object.entries(dependencies)) {
        try {
          const depPackageJsonPath = path.join(nodeModulesPath, depName, 'package.json');
          const depPackageJson = JSON.parse(await fs.readFile(depPackageJsonPath, 'utf-8'));
          
          const license = depPackageJson.license;
          
          if (!license) {
            warnings.push(`${depName}: No license specified in package.json`);
            continue;
          }

          const normalizedLicense = this.normalizeLicense(license);
          
          if (BLOCKED_LICENSES.has(normalizedLicense)) {
            errors.push(`${depName}: Uses blocked license ${license}`);
          } else if (!ALLOWED_LICENSES.has(normalizedLicense)) {
            warnings.push(`${depName}: Uses unrecognized license ${license} - please review`);
          }
          
        } catch (fileError) {
          // Package not found in node_modules, might be a peer dep or not installed
          warnings.push(`${depName}: Could not read package.json to check license`);
        }
      }

      return { errors, warnings };

    } catch (error: any) {
      warnings.push(`Manual license check failed: ${error.message}`);
      return { errors: [], warnings };
    }
  }

  private normalizeLicense(license: string): string {
    if (!license) return '';
    
    // Handle common variations and SPDX expressions
    const normalized = license.toUpperCase().trim();
    
    // Handle some common variations
    if (normalized.includes('MIT')) return 'MIT';
    if (normalized.includes('APACHE-2.0') || normalized.includes('APACHE 2.0')) return 'Apache-2.0';
    if (normalized.includes('BSD-3-CLAUSE') || normalized.includes('BSD 3-CLAUSE')) return 'BSD-3-Clause';
    if (normalized.includes('BSD-2-CLAUSE') || normalized.includes('BSD 2-CLAUSE')) return 'BSD-2-Clause';
    if (normalized.includes('ISC')) return 'ISC';
    if (normalized.includes('GPL-2.0')) return 'GPL-2.0';
    if (normalized.includes('GPL-3.0')) return 'GPL-3.0';
    
    // Return as-is for exact matching
    return normalized;
  }
}
