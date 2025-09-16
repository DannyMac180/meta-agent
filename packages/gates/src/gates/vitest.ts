import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';
import { Gate, GateContext, GateResult } from '../types.js';

const execAsync = promisify(exec);

export class VitestGate implements Gate {
  name = 'Vitest Tests';
  description = 'Runs test suite using Vitest';

  async execute(context: GateContext): Promise<GateResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Check if vitest config exists or test scripts are defined
      const configFiles = ['vitest.config.ts', 'vitest.config.js', 'vite.config.ts', 'vite.config.js'];
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

      // Check if there's a test script in package.json
      const hasTestScript = context.packageJson?.scripts?.test;
      
      // Check if there are any test files
      let hasTestFiles = false;
      try {
        const { stdout } = await execAsync('find . -name "*.test.*" -o -name "*.spec.*" -o -name "__tests__" -type f', {
          cwd: context.projectPath,
        });
        hasTestFiles = stdout.trim().length > 0;
      } catch {
        // Ignore find errors
      }

      if (!hasConfig && !hasTestScript && !hasTestFiles) {
        return {
          gate: this.name,
          passed: true,
          duration: Date.now() - startTime,
          warnings: ['No test configuration or test files found, skipping test execution'],
        };
      }

      // Run tests with Vitest
      const command = hasTestScript ? 'npm test' : 'npx vitest run';
      const { stdout, stderr } = await execAsync(command, {
        cwd: context.projectPath,
        timeout: 300000, // 5 minute timeout
        env: { ...process.env, CI: 'true' }, // Ensure non-interactive mode
      });

      // Parse output for test results
      let testResults: any = {};
      
      // Try to find JSON output or parse text output
      try {
        // Look for JSON in stdout
        const jsonMatch = stdout.match(/\{.*"testResults".*\}/s);
        if (jsonMatch) {
          testResults = JSON.parse(jsonMatch[0]);
        }
      } catch {
        // Fallback to parsing text output
        const failedTests = stdout.match(/FAIL.*$/gm) || [];
        const passedTests = stdout.match(/PASS.*$/gm) || [];
        
        testResults = {
          numFailedTests: failedTests.length,
          numPassedTests: passedTests.length,
          numTotalTests: failedTests.length + passedTests.length,
        };
      }

      // Extract error information
      if (testResults.numFailedTests > 0 || stdout.includes('FAILED')) {
        const failureLines = stdout.split('\n').filter((line: string) => 
          line.includes('FAIL') || 
          line.includes('×') || 
          line.includes('Error:') ||
          line.includes('Expected:') ||
          line.includes('Received:')
        );
        
        errors.push(...failureLines.slice(0, 10)); // Limit to first 10 error lines
        
        if (failureLines.length > 10) {
          errors.push(`... and ${failureLines.length - 10} more test failures`);
        }
      }

      if (stderr.trim()) {
        warnings.push(`Test stderr: ${stderr.trim()}`);
      }

      const passed = testResults.numFailedTests === 0 && !stdout.includes('FAILED');
      
      return {
        gate: this.name,
        passed,
        duration: Date.now() - startTime,
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
        metadata: {
          command,
          testResults: {
            passed: testResults.numPassedTests || 0,
            failed: testResults.numFailedTests || 0,
            total: testResults.numTotalTests || 0,
          },
        },
      };

    } catch (error: any) {
      if (error.code === 'ETIMEDOUT') {
        errors.push('Test execution timed out after 5 minutes');
      } else if (error.code === 1) {
        // Test failures
        const output = error.stdout || '';
        const failureLines = output.split('\n').filter((line: string) => 
          line.includes('FAIL') || 
          line.includes('×') || 
          line.includes('Error:')
        );
        
        if (failureLines.length > 0) {
          errors.push(...failureLines.slice(0, 5));
        } else {
          errors.push('Tests failed but no specific error information could be parsed');
        }
      } else {
        errors.push(`Test execution failed: ${error.message}`);
      }

      return {
        gate: this.name,
        passed: false,
        duration: Date.now() - startTime,
        errors,
        metadata: {
          command: 'npx vitest run',
          errorCode: error.code,
        },
      };
    }
  }
}
