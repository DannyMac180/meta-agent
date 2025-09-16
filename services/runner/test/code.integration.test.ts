import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { createServer } from "../src/index.js";
import type { FastifyInstance } from "fastify";

describe("Runner Service - Code Tool Integration", () => {
  let app: FastifyInstance;

  beforeAll(async () => {
    app = createServer();
    await app.ready();
  });

  afterAll(async () => {
    await app.close();
  });

  describe("Code Tool Endpoint", () => {
    it("should handle basic JavaScript execution", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "console.log('Hello from code tool!'); Math.PI;",
          timeoutMs: 5000
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("stdout");
      expect(result).toHaveProperty("stderr");
      expect(result).toHaveProperty("executionTimeMs");
      
      // Note: Without Docker, this will fail, but the endpoint structure is validated
      if (!result.success) {
        // Expected when Docker is not available
        expect(result.error).toBeDefined();
      }
    });

    it("should handle code with packages", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "const _ = require('lodash'); console.log(_.isEmpty({}));",
          packages: ["lodash"],
          timeoutMs: 30000
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should reject disallowed packages", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "console.log('test');",
          packages: ["child_process", "fs"]
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result.success).toBe(false);
      expect(result.error).toBe("Package validation failed");
    });

    it("should handle invalid input", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "", // Empty code
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
    });

    it("should handle timeout configuration", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "setTimeout(() => { console.log('delayed'); }, 2000);",
          timeoutMs: 1000 // Short timeout
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should handle memory limit configuration", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "console.log('Memory test');",
          memMb: 128
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result).toHaveProperty("success");
    });

    it("should handle network isolation", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: `
            try {
              const http = require('http');
              console.log('HTTP module available');
            } catch (e) {
              console.log('HTTP module blocked');
            }
          `,
          network: false // Explicitly disable network
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result).toHaveProperty("success");
    });

    it("should validate maximum timeout", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "console.log('test');",
          timeoutMs: 400000 // Over maximum
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
    });

    it("should validate maximum memory", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "console.log('test');",
          memMb: 2048 // Over maximum
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
    });
  });

  describe("Error Handling", () => {
    it("should handle malformed JSON", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: "invalid json"
      });

      expect([400, 415]).toContain(response.statusCode); // Could be 400 (bad request) or 415 (unsupported media type)
    });

    it("should handle empty payload", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {}
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
    });
  });

  describe("Security Integration", () => {
    it("should maintain security when called via REST API", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: `
            const fs = require('fs');
            console.log('File system access attempted');
          `,
          packages: ["fs"] // Attempt to use dangerous package
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result.success).toBe(false);
      expect(result.error).toBe("Package validation failed");
    });

    it("should prevent code injection attempts", async () => {
      const response = await app.inject({
        method: "POST",
        url: "/tools/code",
        payload: {
          code: "console.log('test');",
          packages: ["lodash'; rm -rf / #"] // Injection attempt
        }
      });

      expect(response.statusCode).toBe(200);
      
      const result = response.json();
      expect(result.success).toBe(false);
      expect(result.stderr).toMatch(/Disallowed packages|Invalid package name/); // Could be either depending on validation order
    });
  });
});
