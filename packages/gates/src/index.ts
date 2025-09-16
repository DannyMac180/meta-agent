export * from './types.js';
export * from './runner.js';
export * from './gates/tsc.js';
export * from './gates/eslint.js';
export * from './gates/vitest.js';
export * from './gates/audit.js';
export * from './gates/license.js';

import { GateRunner } from './runner.js';
import { TypeScriptGate } from './gates/tsc.js';
import { ESLintGate } from './gates/eslint.js';
import { VitestGate } from './gates/vitest.js';
import { AuditGate } from './gates/audit.js';
import { LicenseGate } from './gates/license.js';

export function createDefaultGateRunner(): GateRunner {
  const runner = new GateRunner();
  
  // Add gates in the order they should run
  runner.addGate(new TypeScriptGate());
  runner.addGate(new ESLintGate());
  runner.addGate(new VitestGate());
  runner.addGate(new AuditGate());
  runner.addGate(new LicenseGate());
  
  return runner;
}
