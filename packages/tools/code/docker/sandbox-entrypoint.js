#!/usr/bin/env node

/**
 * Secure sandbox entrypoint for code execution
 * Handles stdin/stdout communication and enforces timeouts
 */

const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

const TIMEOUT_MS = parseInt(process.env.TIMEOUT_MS) || 8000;
const MEMORY_LIMIT_MB = parseInt(process.env.MEMORY_LIMIT_MB) || 256;

async function main() {
  try {
    // Read input from stdin
    const input = await readStdin();
    const { code, packages = [], timeoutMs = TIMEOUT_MS } = JSON.parse(input);

    // Install packages if specified
    if (packages.length > 0) {
      await installPackages(packages);
    }

    // Write code to temporary file
    const codeFile = path.join('/tmp', 'user-code.js');
    await fs.writeFile(codeFile, code, 'utf8');

    // Execute code with timeout
    const result = await executeCode(codeFile, timeoutMs);
    
    // Send result to stdout
    process.stdout.write(JSON.stringify(result));
    process.exit(0);
    
  } catch (error) {
    const errorResult = {
      success: false,
      error: error.message,
      stdout: '',
      stderr: error.stack || error.message,
      executionTimeMs: 0
    };
    
    process.stdout.write(JSON.stringify(errorResult));
    process.exit(1);
  }
}

async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => {
      data += chunk;
    });
    
    process.stdin.on('end', () => {
      resolve(data);
    });
    
    process.stdin.on('error', reject);
    
    // Timeout for stdin read
    setTimeout(() => {
      reject(new Error('Timeout reading stdin'));
    }, 5000);
  });
}

async function installPackages(packages) {
  // Validate package names (basic security check)
  for (const pkg of packages) {
    if (!/^[a-z0-9\-_.@/]+$/i.test(pkg)) {
      throw new Error(`Invalid package name: ${pkg}`);
    }
  }

  return new Promise((resolve, reject) => {
    const npm = spawn('npm', ['install', '--no-save', '--no-audit', '--no-fund', ...packages], {
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 30000,
      cwd: '/app'
    });

    let stdout = '';
    let stderr = '';

    npm.stdout.on('data', data => {
      stdout += data.toString();
    });

    npm.stderr.on('data', data => {
      stderr += data.toString();
    });

    npm.on('close', code => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(`Package installation failed: ${stderr}`));
      }
    });

    npm.on('error', reject);
  });
}

async function executeCode(codeFile, timeoutMs) {
  const startTime = Date.now();
  
  return new Promise((resolve, reject) => {
    const nodeProcess = spawn('node', [codeFile], {
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: timeoutMs,
      cwd: '/app',
      env: {
        ...process.env,
        NODE_ENV: 'sandbox'
      }
    });

    let stdout = '';
    let stderr = '';

    nodeProcess.stdout.on('data', data => {
      stdout += data.toString();
      // Limit output size
      if (stdout.length > 100000) {
        nodeProcess.kill('SIGKILL');
        reject(new Error('Output size limit exceeded'));
      }
    });

    nodeProcess.stderr.on('data', data => {
      stderr += data.toString();
      // Limit error output size
      if (stderr.length > 50000) {
        nodeProcess.kill('SIGKILL');
        reject(new Error('Error output size limit exceeded'));
      }
    });

    nodeProcess.on('close', code => {
      const executionTimeMs = Date.now() - startTime;
      
      resolve({
        success: code === 0,
        exitCode: code,
        stdout: stdout.slice(0, 50000), // Truncate output
        stderr: stderr.slice(0, 25000), // Truncate errors
        executionTimeMs
      });
    });

    nodeProcess.on('error', error => {
      const executionTimeMs = Date.now() - startTime;
      
      if (error.code === 'ETIMEDOUT') {
        resolve({
          success: false,
          error: 'Execution timeout',
          stdout: stdout.slice(0, 50000),
          stderr: 'Process killed due to timeout',
          executionTimeMs: timeoutMs
        });
      } else {
        reject(error);
      }
    });

    // Cleanup timeout
    setTimeout(() => {
      if (!nodeProcess.killed) {
        nodeProcess.kill('SIGKILL');
      }
    }, timeoutMs + 1000);
  });
}

// Handle process cleanup
process.on('SIGTERM', () => {
  process.exit(130);
});

process.on('SIGINT', () => {
  process.exit(130);
});

main().catch(error => {
  console.error('Entrypoint error:', error);
  process.exit(1);
});
