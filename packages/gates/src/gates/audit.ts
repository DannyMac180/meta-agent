import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';
import { Gate, GateContext, GateResult } from '../types.js';

const execAsync = promisify(exec);

export class AuditGate implements Gate {
  name = 'Security Audit';
  description = 'Runs npm/pnpm audit and Semgrep security scanning';

  async execute(context: GateContext): Promise<GateResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Run dependency audit
      const auditResult = await this.runDepAudit(context);
      errors.push(...auditResult.errors);
      warnings.push(...auditResult.warnings);

      // Run Semgrep if available
      const semgrepResult = await this.runSemgrep(context);
      errors.push(...semgrepResult.errors);
      warnings.push(...semgrepResult.warnings);

      const passed = errors.length === 0;
      
      return {
        gate: this.name,
        passed,
        duration: Date.now() - startTime,
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
        metadata: {
          auditChecks: ['dep-audit', 'semgrep'],
          depAuditRan: auditResult.ran,
          semgrepRan: semgrepResult.ran,
        },
      };

    } catch (error: any) {
      errors.push(`Security audit failed: ${error.message}`);
      
      return {
        gate: this.name,
        passed: false,
        duration: Date.now() - startTime,
        errors,
      };
    }
  }

  private async runDepAudit(context: GateContext): Promise<{ errors: string[], warnings: string[], ran: boolean }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      const lockPnpm = path.join(context.projectPath, 'pnpm-lock.yaml');
      const lockNpm = path.join(context.projectPath, 'package-lock.json');
      const lockYarn = path.join(context.projectPath, 'yarn.lock');

      let command = '';
      if (await exists(lockPnpm)) command = 'pnpm audit --audit-level=moderate --json';
      else if (await exists(lockNpm)) command = 'npm audit --json';
      else if (await exists(lockYarn)) command = 'yarn npm audit --json'; // yarn v3 proxy to npm
      else command = 'npm audit --json';

      const { stdout } = await execAsync(command, {
        cwd: context.projectPath,
        timeout: 120000,
        maxBuffer: 20 * 1024 * 1024,
        env: { ...process.env, CI: 'true' },
      });

      if (stdout.trim()) {
        try {
          const auditData = JSON.parse(stdout);

          if (auditData.advisories) {
            // npm audit legacy format
            for (const [, advisory] of Object.entries(auditData.advisories as any)) {
              const adv = advisory as any;
              const severity = adv.severity;
              const message = `${adv.title} (${adv.module_name}@${adv.vulnerable_versions})`;
              if (severity === 'critical' || severity === 'high') errors.push(`${severity.toUpperCase()}: ${message}`);
              else if (severity === 'moderate') warnings.push(`${severity.toUpperCase()}: ${message}`);
            }
          } else if (auditData.vulnerabilities) {
            // pnpm audit format
            for (const [packageName, vuln] of Object.entries(auditData.vulnerabilities as any)) {
              const v = vuln as any;
              const sev = v.severity || v.severityLevel;
              const message = `${packageName}: ${v.title || 'Security vulnerability'}`;
              if (sev === 'critical' || sev === 'high') errors.push(`${String(sev).toUpperCase()}: ${message}`);
              else if (sev === 'moderate') warnings.push(`${String(sev).toUpperCase()}: ${message}`);
            }
          }
        } catch (parseError) {
          warnings.push(`Could not parse audit output: ${parseError}`);
        }
      }

      return { errors, warnings, ran: true };

    } catch (error: any) {
      if (error.killed && error.signal === 'SIGTERM') {
        errors.push('Dependency audit timed out');
      } else if (error.code === 1) {
        try {
          const auditData = JSON.parse(error.stdout || '{}');
          if (auditData.advisories) {
            for (const [, advisory] of Object.entries(auditData.advisories as any)) {
              const adv = advisory as any;
              const severity = adv.severity;
              const message = `${adv.title} (${adv.module_name})`;
              if (severity === 'critical' || severity === 'high') errors.push(`${severity.toUpperCase()}: ${message}`);
            }
          }
        } catch {
          errors.push('Dependency audit found issues but output could not be parsed');
        }
      } else if (error.code === 'ENOBUFS') {
        warnings.push('Audit output too large (ENOBUFS); consider increasing buffer or limiting scope');
      } else {
        warnings.push(`Dependency audit could not run: ${error.message}`);
      }

      return { errors, warnings, ran: false };
    }
  }

  private async runSemgrep(context: GateContext): Promise<{ errors: string[], warnings: string[], ran: boolean }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Check if semgrep is available
      await execAsync('which semgrep', { timeout: 5000 });

      // Run semgrep with basic security rules
      const { stdout } = await execAsync('semgrep --config=auto --json --quiet', {
        cwd: context.projectPath,
        timeout: 180000,
        maxBuffer: 20 * 1024 * 1024,
      });

      if (stdout.trim()) {
        try {
          const semgrepData = JSON.parse(stdout);

          if (semgrepData.results) {
            for (const result of semgrepData.results) {
              const severity = result.extra?.severity || 'INFO';
              const message = `${result.path}:${result.start.line} - ${result.message} (${result.check_id})`;

              if (severity === 'ERROR' || severity === 'CRITICAL') {
                errors.push(`SEMGREP ${severity}: ${message}`);
              } else if (severity === 'WARNING') {
                warnings.push(`SEMGREP ${severity}: ${message}`);
              }
            }
          }
        } catch (parseError) {
          warnings.push(`Could not parse Semgrep output: ${parseError}`);
        }
      }

      return { errors, warnings, ran: true };

    } catch (error: any) {
      if (error.message?.includes('which semgrep') || error.code === 127) {
        return { errors: [], warnings: ['Semgrep not available, skipping static analysis'], ran: false };
      } else if (error.killed && error.signal === 'SIGTERM') {
        errors.push('Semgrep timed out');
      } else if (error.code === 'ENOBUFS') {
        warnings.push('Semgrep output too large (ENOBUFS)');
      } else {
        warnings.push(`Semgrep analysis failed: ${error.message}`);
      }

      return { errors, warnings, ran: false };
    }
  }
}

async function exists(p: string): Promise<boolean> {
  try { await fs.access(p); return true; } catch { return false; }
}
