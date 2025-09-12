import { describe, it, expect } from "vitest";
import { VariableSpecSchema } from "../src/validators/variable";

describe("VariableSpecSchema", () => {
  it("requires enumValues when type is enum", () => {
    const res = VariableSpecSchema.safeParse({ key: "mode", type: "enum" });
    expect(res.success).toBe(false);
  });

  it("accepts enum with values", () => {
    const res = VariableSpecSchema.safeParse({ key: "mode", type: "enum", enumValues: ["a", "b"] });
    expect(res.success).toBe(true);
  });
});
