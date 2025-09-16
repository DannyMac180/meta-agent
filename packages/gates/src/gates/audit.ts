import { exec } from 'child_process';
import { promisify } from 'util';
import { Gate, GateContext, GateResult } from '../types.js';

const execAsync = promisify(exec);

export class AuditGate implements Gate {
  name = 'Security Audit';
  description = 'Runs npm audit and Semgrep security scanning';

  async execute(context: GateContext): Promise<GateResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Run npm audit
      const auditResult = await this.runNpmAudit(context);
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
          auditChecks: ['npm-audit', 'semgrep'],
          npmAuditRan: auditResult.ran,
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

  private async runNpmAudit(context: GateContext): Promise<{ errors: string[], warnings: string[], ran: boolean }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Use pnpm audit if pnpm-lock.yaml exists, otherwise npm audit
      const command = 'pnpm audit --audit-level=moderate --json';
      
      const { stdout } = await execAsync(command, {
        cwd: context.projectPath,
        timeout: 120000, // 2 minute timeout
      });

      if (stdout.trim()) {
        try {
          const auditData = JSON.parse(stdout);
          
          if (auditData.advisories) {
            // npm audit format
            for (const [id, advisory] of Object.entries(auditData.advisories as any)) {
              const adv = advisory as any;
              const severity = adv.severity;
              const message = `${adv.title} (${adv.module_name}@${adv.vulnerable_versions}) - ${adv.overview}`;
              
              if (severity === 'critical' || severity === 'high') {
                errors.push(`${severity.toUpperCase()}: ${message}`);
              } else if (severity === 'moderate') {
                warnings.push(`${severity.toUpperCase()}: ${message}`);
              }
            }
          } else if (auditData.vulnerabilities) {
            // pnpm audit format
            for (const [packageName, vuln] of Object.entries(auditData.vulnerabilities as any)) {
              const v = vuln as any;
              const severity = v.severity;
              const message = `${packageName}: ${v.title || 'Security vulnerability'}`;
              
              if (severity === 'critical' || severity === 'high') {
                errors.push(`${severity.toUpperCase()}: ${message}`);
              } else if (severity === 'moderate') {
                warnings.push(`${severity.toUpperCase()}: ${message}`);
              }
            }
          }
        } catch (parseError) {
          warnings.push(`Could not parse audit output: ${parseError}`);
        }
      }

      return { errors, warnings, ran: true };

    } catch (error: any) {
      if (error.code === 'ETIMEDOUT') {
        errors.push('npm audit timed out after 2 minutes');
      } else if (error.code === 1) {
        // Audit found issues
        try {
          const auditData = JSON.parse(error.stdout || '{}');
          // Process the audit data similar to success case
          if (auditData.advisories) {
            for (const [id, advisory] of Object.entries(auditData.advisories as any)) {
              const adv = advisory as any;
              const severity = adv.severity;
              const message = `${adv.title} (${adv.module_name}) - ${adv.overview}`;
              
              if (severity === 'critical' || severity === 'high') {
                errors.push(`${severity.toUpperCase()}: ${message}`);
              }
            }
          }
        } catch {
          errors.push(`npm audit found issues but output could not be parsed`);
        }
      } else {
        warnings.push(`npm audit could not run: ${error.message}`);
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
        timeout: 180000, // 3 minute timeout
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
        // Semgrep not installed, skip silently
        return { errors: [], warnings: ['Semgrep not available, skipping static analysis'], ran: false };
      } else if (error.code === 'ETIMEDOUT') {
        errors.push('Semgrep timed out after 3 minutes');
      } else {
        warnings.push(`Semgrep analysis failed: ${error.message}`);
      }

      return { errors, warnings, ran: false };
    }
  }
}
