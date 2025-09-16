import { Gate, GateContext, GateResult, GateRunResult } from './types.js';

export class GateRunner {
  private gates: Gate[] = [];

  addGate(gate: Gate): void {
    this.gates.push(gate);
  }

  async run(context: GateContext): Promise<GateRunResult> {
    const results: GateResult[] = [];
    const startTime = Date.now();
    let failedGate: string | undefined;

    for (const gate of this.gates) {
      console.log(`Running gate: ${gate.name}`);
      const gateStartTime = Date.now();

      try {
        const result = await gate.execute(context);
        results.push(result);

        if (!result.passed) {
          failedGate = gate.name;
          console.log(`Gate ${gate.name} failed:`, result.errors);
          break; // Stop on first failure
        }

        console.log(`Gate ${gate.name} passed in ${result.duration}ms`);
      } catch (error) {
        const gateEndTime = Date.now();
        const result: GateResult = {
          gate: gate.name,
          passed: false,
          duration: gateEndTime - gateStartTime,
          errors: [`Gate execution failed: ${error instanceof Error ? error.message : String(error)}`],
        };
        results.push(result);
        failedGate = gate.name;
        break;
      }
    }

    const totalDuration = Date.now() - startTime;
    const success = !failedGate;

    return {
      success,
      results,
      totalDuration,
      failedGate,
    };
  }

  getGates(): Gate[] {
    return [...this.gates];
  }
}
