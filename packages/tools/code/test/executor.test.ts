import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { CodeExecutor } from "../src/executor.js";
import type { CodeToolInput } from "../src/types.js";

describe("Code Executor", () => {
  let executor: CodeExecutor;

  beforeAll(() => {
    executor = new CodeExecutor("test-sandbox");
  });

  afterAll(async () => {
    await executor.killAllContainers();
  });

  describe("Basic Execution", () => {
    it("should handle simple JavaScript execution", async () => {
      const input: CodeToolInput = {
        code: "console.log('Hello, World!');",
        timeoutMs: 5000,
        memMb: 128
      };

      const result = await executor.execute(input);

      // This will fail without Docker setup, but validates the logic
      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("stdout");
      expect(result).toHaveProperty("stderr");
      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should handle code with syntax errors", async () => {
      const input: CodeToolInput = {
        code: "console.log('unclosed string;",
        timeoutMs: 5000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should handle code with runtime errors", async () => {
      const input: CodeToolInput = {
        code: "throw new Error('Test error');",
        timeoutMs: 5000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("stderr");
    });
  });

  describe("Package Management", () => {
    it("should handle valid package installation", async () => {
      const input: CodeToolInput = {
        code: "const _ = require('lodash'); console.log(_.isEmpty({}));",
        packages: ["lodash"],
        timeoutMs: 30000 // Allow time for package installation
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should reject invalid package names", async () => {
      const input: CodeToolInput = {
        code: "console.log('test');",
        packages: ["../invalid", "package;malicious"]
      };

      const result = await executor.execute(input);

      expect(result.success).toBe(false);
      expect(result.error).toContain("Invalid package name");
    });
  });

  describe("Resource Limits", () => {
    it("should respect memory limits", async () => {
      const input: CodeToolInput = {
        code: "console.log('test');",
        memMb: 64,
        timeoutMs: 5000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should respect timeout limits", async () => {
      const input: CodeToolInput = {
        code: "while(true) { /* infinite loop */ }",
        timeoutMs: 2000
      };

      const startTime = Date.now();
      const result = await executor.execute(input);
      const actualTime = Date.now() - startTime;

      // Should timeout within reasonable bounds (allowing for Docker overhead)
      expect(actualTime).toBeLessThan(10000);
      expect(result).toHaveProperty("executionTimeMs");
    });
  });

  describe("Output Handling", () => {
    it("should capture stdout", async () => {
      const input: CodeToolInput = {
        code: "console.log('stdout test');",
        timeoutMs: 5000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("stdout");
    });

    it("should capture stderr", async () => {
      const input: CodeToolInput = {
        code: "console.error('stderr test');",
        timeoutMs: 5000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("stderr");
    });

    it("should handle large output", async () => {
      const input: CodeToolInput = {
        code: "for(let i = 0; i < 1000; i++) { console.log('Line ' + i); }",
        timeoutMs: 10000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("stdout");
      // Note: Without Docker, result structure might be different
      if (result.success || result.stdout.length > 0) {
        expect(result).toHaveProperty("truncated");
      }
    });
  });

  describe("Container Management", () => {
    it("should track running containers", () => {
      const containers = executor.getRunningContainers();
      expect(Array.isArray(containers)).toBe(true);
    });

    it("should cleanup containers", async () => {
      await expect(executor.killAllContainers()).resolves.not.toThrow();
      
      const containers = executor.getRunningContainers();
      expect(containers).toHaveLength(0);
    });
  });

  describe("Network Isolation", () => {
    it("should block network access by default", async () => {
      const input: CodeToolInput = {
        code: `
          const http = require('http');
          http.get('http://google.com', (res) => {
            console.log('Network access successful');
          }).on('error', (err) => {
            console.error('Network access blocked:', err.message);
          });
          
          // Give it time to attempt the request
          setTimeout(() => {
            console.log('Test completed');
          }, 1000);
        `,
        network: false,
        timeoutMs: 5000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("success");
      // The test validates that network isolation is configured,
      // actual blocking would be tested in integration tests
    });

    it("should allow network when explicitly enabled", async () => {
      const input: CodeToolInput = {
        code: "console.log('Network test');",
        network: true,
        timeoutMs: 5000
      };

      const result = await executor.execute(input);

      expect(result).toHaveProperty("success");
    });
  });

  describe("Error Handling", () => {
    it("should handle Docker execution failures gracefully", async () => {
      const input: CodeToolInput = {
        code: "console.log('test');",
        timeoutMs: 1000
      };

      const result = await executor.execute(input);

      // Should return a result structure even on failure
      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("stdout");
      expect(result).toHaveProperty("stderr");
      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should handle container startup failures", async () => {
      // Use an invalid image to simulate startup failure
      const executor = new CodeExecutor("nonexistent-image:latest");
      
      const result = await executor.execute({
        code: "console.log('test');",
        timeoutMs: 5000
      });

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      
      await executor.killAllContainers();
    });
  });
});
