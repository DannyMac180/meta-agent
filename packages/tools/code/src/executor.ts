import { spawn } from "child_process";
import { randomUUID } from "crypto";
import type { CodeToolInput, CodeExecutionResult, DockerExecutionOptions, ContainerInfo } from "./types.js";

/**
 * Docker-based code executor with security and resource isolation
 */
export class CodeExecutor {
  private runningContainers = new Map<string, ContainerInfo>();
  private readonly imageTag: string;
  
  constructor(imageTag: string = "metaagent-code-sandbox:latest") {
    this.imageTag = imageTag;
    
    // Cleanup containers on process exit
    process.on("SIGTERM", () => this.cleanup());
    process.on("SIGINT", () => this.cleanup());
    process.on("exit", () => this.cleanup());
  }

  async execute(input: CodeToolInput): Promise<CodeExecutionResult> {
    const containerId = `code-${randomUUID()}`;
    const startTime = Date.now();
    
    try {
      // Validate package names for security
      if (input.packages?.length) {
        this.validatePackages(input.packages);
      }

      const options: DockerExecutionOptions = {
        imageTag: this.imageTag,
        timeoutMs: input.timeoutMs || 8000,
        memMb: input.memMb || 256,
        network: input.network || false,
        allowedPackages: input.packages
      };

      return await this.runInContainer(containerId, input, options);
      
    } catch (error) {
      return {
        success: false,
        stdout: "",
        stderr: error instanceof Error ? error.message : "Unknown error",
        executionTimeMs: Date.now() - startTime,
        error: error instanceof Error ? error.message : "Unknown error"
      };
    } finally {
      // Cleanup container
      await this.removeContainer(containerId);
    }
  }

  private validatePackages(packages: string[]): void {
    const suspiciousPackages = [
      "child_process", "fs", "net", "http", "https", "os", "process",
      "cluster", "worker_threads", "dgram", "dns", "tls", "crypto"
    ];
    
    for (const pkg of packages) {
      // Basic validation - alphanumeric, hyphens, underscores, dots, @ and / for scoped packages
      if (!/^[@a-z0-9\-_.\/]+$/i.test(pkg)) {
        throw new Error(`Invalid package name: ${pkg}`);
      }
      
      // Block suspicious core modules
      if (suspiciousPackages.includes(pkg)) {
        throw new Error(`Package not allowed: ${pkg}`);
      }
      
      // Block relative paths and shell commands
      if (pkg.includes("..") || pkg.includes(";") || pkg.includes("|")) {
        throw new Error(`Invalid package name format: ${pkg}`);
      }
    }
  }

  private async runInContainer(
    containerId: string, 
    input: CodeToolInput, 
    options: DockerExecutionOptions
  ): Promise<CodeExecutionResult> {
    
    const containerInfo: ContainerInfo = {
      containerId,
      startedAt: new Date(),
      timeoutMs: options.timeoutMs
    };
    
    this.runningContainers.set(containerId, containerInfo);

    return new Promise((resolve, reject) => {
      const dockerArgs = this.buildDockerArgs(containerId, options);
      
      const dockerProcess = spawn("docker", dockerArgs, {
        stdio: ["pipe", "pipe", "pipe"]
      });

      let stdout = "";
      let stderr = "";
      let resolved = false;

      // Send input to container
      const containerInput = {
        code: input.code,
        packages: input.packages || [],
        timeoutMs: options.timeoutMs
      };
      
      dockerProcess.stdin.write(JSON.stringify(containerInput));
      dockerProcess.stdin.end();

      // Collect output
      dockerProcess.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      dockerProcess.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      // Handle process completion
      dockerProcess.on("close", (code) => {
        if (resolved) return;
        resolved = true;

        this.runningContainers.delete(containerId);

        if (code === 0 && stdout) {
          try {
            // Parse result from container
            const result = JSON.parse(stdout);
            resolve({
              ...result,
              truncated: {
                stdout: result.stdout?.length >= 50000,
                stderr: result.stderr?.length >= 25000
              }
            });
          } catch (parseError) {
            resolve({
              success: false,
              stdout,
              stderr: stderr || "Failed to parse container output",
              executionTimeMs: Date.now() - containerInfo.startedAt.getTime(),
              error: "Container output parsing failed"
            });
          }
        } else {
          resolve({
            success: false,
            stdout,
            stderr: stderr || `Docker process exited with code ${code}`,
            executionTimeMs: Date.now() - containerInfo.startedAt.getTime(),
            error: `Container execution failed (exit code: ${code})`
          });
        }
      });

      dockerProcess.on("error", (error) => {
        if (resolved) return;
        resolved = true;

        this.runningContainers.delete(containerId);
        reject(new Error(`Docker execution failed: ${error.message}`));
      });

      // Timeout handler
      const timeoutHandle = setTimeout(async () => {
        if (resolved) return;
        resolved = true;

        this.runningContainers.delete(containerId);
        
        // Kill the container
        await this.killContainer(containerId);
        
        resolve({
          success: false,
          stdout,
          stderr: stderr + "\nExecution timed out",
          executionTimeMs: options.timeoutMs,
          error: "Execution timeout"
        });
      }, options.timeoutMs + 5000); // Extra 5s for Docker overhead

      dockerProcess.on("close", () => {
        clearTimeout(timeoutHandle);
      });
    });
  }

  private buildDockerArgs(containerId: string, options: DockerExecutionOptions): string[] {
    const args = [
      "run",
      "--rm",
      "--name", containerId,
      "--memory", `${options.memMb}m`,
      "--memory-swap", `${options.memMb}m`, // No swap
      "--cpus", "0.5",
      "--pids-limit", "32",
      "--ulimit", "nofile=256:256",
      "--ulimit", "nproc=32:32",
      "--cap-drop", "ALL",
      "--read-only",
      "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",
      "--tmpfs", "/app:rw,noexec,nosuid,size=50m",
      "--user", "1001:1001",
      "--interactive"
    ];

    // Network isolation
    if (!options.network) {
      args.push("--network", "none");
    }

    // Environment variables
    args.push(
      "--env", `TIMEOUT_MS=${options.timeoutMs}`,
      "--env", `MEMORY_LIMIT_MB=${options.memMb}`,
      "--env", "NODE_ENV=sandbox"
    );

    // Image
    args.push(options.imageTag);

    return args;
  }

  private async killContainer(containerId: string): Promise<void> {
    try {
      await this.runCommand("docker", ["kill", containerId]);
    } catch (error) {
      // Container might already be stopped
    }
  }

  private async removeContainer(containerId: string): Promise<void> {
    try {
      await this.runCommand("docker", ["rm", "-f", containerId]);
    } catch (error) {
      // Container might already be removed
    }
  }

  private async runCommand(command: string, args: string[]): Promise<void> {
    return new Promise((resolve, reject) => {
      const process = spawn(command, args, { stdio: "ignore" });
      
      process.on("close", (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Command failed with code ${code}`));
        }
      });
      
      process.on("error", reject);
    });
  }

  private async cleanup(): Promise<void> {
    const promises = Array.from(this.runningContainers.keys()).map(containerId =>
      this.removeContainer(containerId).catch(() => {}) // Ignore errors during cleanup
    );
    
    await Promise.all(promises);
    this.runningContainers.clear();
  }

  /**
   * Get information about currently running containers
   */
  getRunningContainers(): ContainerInfo[] {
    return Array.from(this.runningContainers.values());
  }

  /**
   * Kill all running containers (for testing/cleanup)
   */
  async killAllContainers(): Promise<void> {
    const promises = Array.from(this.runningContainers.keys()).map(containerId =>
      this.killContainer(containerId)
    );
    
    await Promise.all(promises);
    await this.cleanup();
  }
}
