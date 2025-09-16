import { z } from "zod";
import { CodeExecutor } from "./executor.js";
import { CodeToolInputSchema, type CodeToolInput, type CodeExecutionResult } from "./types.js";

/**
 * Containerized JavaScript code interpreter tool
 * Executes JavaScript code in an isolated Docker container with resource limits
 */
export class CodeTool {
  private executor: CodeExecutor;
  private readonly allowedPackages: Set<string>;

  constructor(options?: {
    imageTag?: string;
    allowedPackages?: string[];
  }) {
    this.executor = new CodeExecutor(options?.imageTag);
    this.allowedPackages = new Set(options?.allowedPackages || [
      // Default allowed packages
      "lodash", "moment", "uuid", "axios", "cheerio", "csv-parser",
      "date-fns", "ramda", "validator", "colors", "chalk", "debug"
    ]);
  }

  /**
   * Execute JavaScript code in a secure container
   */
  async execute(input: unknown): Promise<CodeExecutionResult> {
    try {
      // Validate input
      const validatedInput = CodeToolInputSchema.parse(input);
      
      // Validate packages against allow-list
      if (validatedInput.packages?.length) {
        const disallowedPackages = validatedInput.packages.filter(
          pkg => !this.allowedPackages.has(pkg)
        );
        
        if (disallowedPackages.length > 0) {
          return {
            success: false,
            stdout: "",
            stderr: `Disallowed packages: ${disallowedPackages.join(", ")}`,
            executionTimeMs: 0,
            error: "Package validation failed"
          };
        }
      }

      return await this.executor.execute(validatedInput);
      
    } catch (error) {
      if (error instanceof z.ZodError) {
        return {
          success: false,
          stdout: "",
          stderr: `Input validation failed: ${error.issues.map((e: any) => e.message).join(", ")}`,
          executionTimeMs: 0,
          error: "Invalid input"
        };
      }
      
      return {
        success: false,
        stdout: "",
        stderr: error instanceof Error ? error.message : "Unknown error",
        executionTimeMs: 0,
        error: error instanceof Error ? error.message : "Unknown error"
      };
    }
  }

  /**
   * Add packages to the allow-list
   */
  addAllowedPackages(packages: string[]): void {
    packages.forEach(pkg => this.allowedPackages.add(pkg));
  }

  /**
   * Remove packages from the allow-list
   */
  removeAllowedPackages(packages: string[]): void {
    packages.forEach(pkg => this.allowedPackages.delete(pkg));
  }

  /**
   * Get current allowed packages
   */
  getAllowedPackages(): string[] {
    return Array.from(this.allowedPackages);
  }

  /**
   * Get information about running containers
   */
  getRunningContainers() {
    return this.executor.getRunningContainers();
  }

  /**
   * Kill all running containers (for cleanup)
   */
  async cleanup(): Promise<void> {
    await this.executor.killAllContainers();
  }
}

/**
 * Default code tool instance
 */
export const codeTool = new CodeTool();

/**
 * Tool definition for Mastra framework
 */
export const codeToolDefinition = {
  name: "code_interpreter",
  description: "Execute JavaScript code in a secure, isolated container with optional npm packages",
  schema: CodeToolInputSchema,
  run: async (input: CodeToolInput) => {
    return await codeTool.execute(input);
  }
};
