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
      
      // Basic heuristic: rely on config or package.json scripts; skip deep file discovery to remain cross-platform
      const hasTestFiles = false;

      if (!hasConfig && !hasTestScript && !hasTestFiles) {
        return {
          gate: this.name,
          passed: true,
          duration: Date.now() - startTime,
          warnings: ['No test configuration or test files found, skipping test execution'],
        };
      }

      // Run tests
      const useVitest = hasConfig || (context.packageJson?.devDependencies && context.packageJson.devDependencies.vitest);
      const command = useVitest ? 'npx vitest run --reporter=json' : (hasTestScript ? 'npm test' : 'npx vitest run');
      const { stdout, stderr } = await execAsync(command, {
      cwd: context.projectPath,
      timeout: 300000,
        maxBuffer: 20 * 1024 * 1024,
        env: { ...process.env, CI: 'true' },
      });

      // Parse output for test results
      let testResults: any = {};

      if (command.includes('--reporter=json')) {
      try {
      testResults = JSON.parse(stdout);
      } catch {
      // Fallback to text parsing
          const failedTests = stdout.match(/FAIL.*$/gm) || [];
          const passedTests = stdout.match(/PASS.*$/gm) || [];
          testResults = {
            numFailedTests: failedTests.length,
            numPassedTests: passedTests.length,
            numTotalTests: failedTests.length + passedTests.length,
          };
      }
      } else {
      // Parse text output
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
      if (error.killed && error.signal === 'SIGTERM') {
        errors.push('Test execution timed out');
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
      } else if (error.code === 'ENOBUFS') {
        warnings.push('Test output too large (ENOBUFS)');
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
