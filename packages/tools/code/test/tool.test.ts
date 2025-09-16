import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { CodeTool, codeToolDefinition } from "../src/tool.js";
import { CodeToolInputSchema } from "../src/types.js";

describe("Code Tool", () => {
  let codeTool: CodeTool;

  beforeAll(() => {
    codeTool = new CodeTool({
      allowedPackages: ["lodash", "moment", "uuid"]
    });
  });

  afterAll(async () => {
    await codeTool.cleanup();
  });

  describe("Tool Definition", () => {
    it("should export proper tool definition", () => {
      expect(codeToolDefinition).toHaveProperty("name");
      expect(codeToolDefinition).toHaveProperty("description");
      expect(codeToolDefinition).toHaveProperty("schema");
      expect(codeToolDefinition).toHaveProperty("run");
      
      expect(codeToolDefinition.name).toBe("code_interpreter");
      expect(typeof codeToolDefinition.description).toBe("string");
      expect(codeToolDefinition.schema).toBe(CodeToolInputSchema);
      expect(typeof codeToolDefinition.run).toBe("function");
    });

    it("should validate input schema", () => {
      const validInput = {
        code: "console.log('test');",
        packages: ["lodash"],
        timeoutMs: 5000,
        memMb: 256,
        network: false
      };

      const result = CodeToolInputSchema.safeParse(validInput);
      expect(result.success).toBe(true);

      if (result.success) {
        expect(result.data).toEqual(validInput);
      }
    });
  });

  describe("Package Allow-List Management", () => {
    it("should start with configured allowed packages", () => {
      const allowed = codeTool.getAllowedPackages();
      expect(allowed).toContain("lodash");
      expect(allowed).toContain("moment");
      expect(allowed).toContain("uuid");
    });

    it("should allow adding packages to allow-list", () => {
      codeTool.addAllowedPackages(["axios", "cheerio"]);
      
      const allowed = codeTool.getAllowedPackages();
      expect(allowed).toContain("axios");
      expect(allowed).toContain("cheerio");
    });

    it("should allow removing packages from allow-list", () => {
      codeTool.addAllowedPackages(["test-package"]);
      expect(codeTool.getAllowedPackages()).toContain("test-package");
      
      codeTool.removeAllowedPackages(["test-package"]);
      expect(codeTool.getAllowedPackages()).not.toContain("test-package");
    });

    it("should reject disallowed packages", async () => {
      const result = await codeTool.execute({
        code: "console.log('test');",
        packages: ["disallowed-package"]
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Package validation failed");
      expect(result.stderr).toContain("Disallowed packages: disallowed-package");
    });

    it("should allow explicitly allowed packages", async () => {
      const result = await codeTool.execute({
        code: "console.log('test');",
        packages: ["lodash"] // This is in the allow-list
      });

      // Should not fail due to package validation
      expect(result.error).not.toBe("Package validation failed");
    });
  });

  describe("Input Validation", () => {
    it("should validate required fields", async () => {
      const result = await codeTool.execute({
        // Missing code field
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
      expect(result.stderr).toContain("Input validation failed");
    });

    it("should validate code length", async () => {
      const tooLongCode = "console.log('test');".repeat(10000);
      
      const result = await codeTool.execute({
        code: tooLongCode
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
      expect(result.stderr).toContain("Code too large");
    });

    it("should validate timeout range", async () => {
      const result = await codeTool.execute({
        code: "console.log('test');",
        timeoutMs: 500 // Below minimum
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
    });

    it("should validate memory range", async () => {
      const result = await codeTool.execute({
        code: "console.log('test');",
        memMb: 32 // Below minimum
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
    });

    it("should apply default values", async () => {
      const result = await codeTool.execute({
        code: "console.log('test');"
        // No other fields specified
      });

      // Should not fail due to missing optional fields
      expect(result.error).not.toBe("Invalid input");
    });
  });

  describe("Error Handling", () => {
    it("should handle executor errors gracefully", async () => {
      const result = await codeTool.execute({
        code: "console.log('test');"
      });

      // Should always return a structured result
      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("stdout");
      expect(result).toHaveProperty("stderr");
      expect(result).toHaveProperty("executionTimeMs");
    });

    it("should handle malformed input", async () => {
      const result = await codeTool.execute("not an object");

      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
      expect(result.stderr).toContain("Input validation failed");
    });

    it("should handle null input", async () => {
      const result = await codeTool.execute(null);

      expect(result.success).toBe(false);
      expect(result.error).toBe("Invalid input");
    });
  });

  describe("Container Management", () => {
    it("should provide container information", () => {
      const containers = codeTool.getRunningContainers();
      expect(Array.isArray(containers)).toBe(true);
    });

    it("should allow cleanup", async () => {
      await expect(codeTool.cleanup()).resolves.not.toThrow();
    });
  });
});

describe("Default Code Tool", () => {
  it("should export default allowed packages", async () => {
    const { codeTool: defaultTool } = await import("../src/tool.js");
    
    const allowed = defaultTool.getAllowedPackages();
    
    // Should include commonly safe packages
    expect(allowed).toContain("lodash");
    expect(allowed).toContain("moment");
    expect(allowed).toContain("uuid");
    expect(allowed).toContain("validator");
    expect(allowed).toContain("chalk");
    
    // Should not include dangerous packages
    expect(allowed).not.toContain("child_process");
    expect(allowed).not.toContain("fs");
    expect(allowed).not.toContain("net");
  });
});
