import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';
import { Gate, GateContext, GateResult } from '../types.js';

const execAsync = promisify(exec);

export class TypeScriptGate implements Gate {
  name = 'TypeScript Compilation';
  description = 'Validates TypeScript compilation without emitting files';

  async execute(context: GateContext): Promise<GateResult> {
    const startTime = Date.now();
    const errors: string[] = [];

    try {
      // Check if tsconfig.json exists
      const tsconfigPath = path.join(context.projectPath, 'tsconfig.json');
      try {
        await fs.access(tsconfigPath);
      } catch {
        // No tsconfig.json found, skip TypeScript check
        return {
          gate: this.name,
          passed: true,
          duration: Date.now() - startTime,
          warnings: ['No tsconfig.json found, skipping TypeScript compilation check'],
        };
      }

      // Run TypeScript compiler in no-emit mode
      const { stdout, stderr } = await execAsync('npx tsc --noEmit', {
        cwd: context.projectPath,
        timeout: 60000,
        maxBuffer: 20 * 1024 * 1024,
        env: { ...process.env, CI: 'true' },
      });

      // TypeScript outputs errors to stdout, not stderr
      if (stdout.trim()) {
        const lines = stdout.trim().split('\n');
        errors.push(...lines.filter((line: string) => line.includes('error TS')));
      }

      if (stderr.trim()) {
        errors.push(`TypeScript compiler error: ${stderr.trim()}`);
      }

      const passed = errors.length === 0;
      
      return {
        gate: this.name,
        passed,
        duration: Date.now() - startTime,
        errors: errors.length > 0 ? errors : undefined,
        metadata: {
          command: 'npx tsc --noEmit',
          errorCount: errors.length,
        },
      };

    } catch (error: any) {
      // Handle execution errors (e.g., tsc not found, timeout)
      if (error.killed && error.signal === 'SIGTERM') {
        errors.push('TypeScript compilation timed out');
      } else if (error.code === 2) {
        // TypeScript compiler exit code 2 means compilation errors
        const output = error.stdout || '';
        if (output.trim()) {
          const lines = output.trim().split('\n');
          errors.push(...lines.filter((line: string) => line.includes('error TS')));
        }
      } else if (error.code === 'ENOBUFS') {
        errors.push('TypeScript compiler output too large (ENOBUFS)');
      } else {
        errors.push(`TypeScript compilation failed: ${error.message}`);
      }

      return {
        gate: this.name,
        passed: false,
        duration: Date.now() - startTime,
        errors,
        metadata: {
          command: 'npx tsc --noEmit',
          errorCode: error.code,
        },
      };
    }
  }
}
