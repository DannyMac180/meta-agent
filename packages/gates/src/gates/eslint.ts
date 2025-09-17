import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';
import { Gate, GateContext, GateResult } from '../types.js';

const execAsync = promisify(exec);

export class ESLintGate implements Gate {
  name = 'ESLint';
  description = 'Validates code quality and style using ESLint';

  async execute(context: GateContext): Promise<GateResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Check if ESLint config exists
      const configFiles = ['.eslintrc.js', '.eslintrc.json', '.eslintrc.yaml', '.eslintrc.yml', 'eslint.config.js'];
      let hasConfig = false;
      
      for (const configFile of configFiles) {
        try {
          await fs.access(path.join(context.projectPath, configFile));
          hasConfig = true;
          break;
        } catch {
          // Continue checking other config files
        }
      }

      // Also check package.json for eslintConfig
      if (!hasConfig && context.packageJson?.eslintConfig) {
        hasConfig = true;
      }

      if (!hasConfig) {
        return {
          gate: this.name,
          passed: true,
          duration: Date.now() - startTime,
          warnings: ['No ESLint configuration found, skipping lint check'],
        };
      }

      // Run ESLint with JSON format output
      const { stdout } = await execAsync('npx eslint . --format json --ext .ts,.js,.tsx,.jsx', {
        cwd: context.projectPath,
        timeout: 120000,
        maxBuffer: 20 * 1024 * 1024,
        env: { ...process.env, CI: 'true' },
      });

      if (stdout.trim()) {
        try {
          const results = JSON.parse(stdout);
          
          for (const fileResult of results) {
            for (const message of fileResult.messages) {
              const location = `${fileResult.filePath}:${message.line}:${message.column}`;
              const issue = `${location} - ${message.message} (${message.ruleId})`;
              
              if (message.severity === 2) { // Error
                errors.push(issue);
              } else if (message.severity === 1) { // Warning
                warnings.push(issue);
              }
            }
          }
        } catch (parseError) {
          errors.push(`Failed to parse ESLint output: ${parseError}`);
        }
      }

      const passed = errors.length === 0;
      
      return {
        gate: this.name,
        passed,
        duration: Date.now() - startTime,
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
        metadata: {
          command: 'npx eslint . --format json --ext .ts,.js,.tsx,.jsx',
          errorCount: errors.length,
          warningCount: warnings.length,
        },
      };

    } catch (error: any) {
    if (error.killed && error.signal === 'SIGTERM') {
    errors.push('ESLint timed out');
    } else if (error.code === 1) {
    // ESLint found issues, parse the output
    try {
    const results = JSON.parse(error.stdout || '[]');

    for (const fileResult of results) {
    for (const message of fileResult.messages) {
    const location = `${fileResult.filePath}:${message.line}:${message.column}`;
    const issue = `${location} - ${message.message} (${message.ruleId})`;

    if (message.severity === 2) {
    errors.push(issue);
    } else {
    warnings.push(issue);
    }
    }
    }
    } catch {
    errors.push(`ESLint found issues but output could not be parsed: ${error.stdout || error.message}`);
    }
    } else if (error.code === 'ENOBUFS') {
    errors.push('ESLint output too large (ENOBUFS)');
    } else {
        errors.push(`ESLint execution failed: ${error.message}`);
    }

    return {
    gate: this.name,
    passed: errors.length === 0,
    duration: Date.now() - startTime,
    errors: errors.length > 0 ? errors : undefined,
    warnings: warnings.length > 0 ? warnings : undefined,
    metadata: {
      command: 'npx eslint . --format json --ext .ts,.js,.tsx,.jsx',
        errorCode: error.code,
        },
      };
    }
  }
}
