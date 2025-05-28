# Telemetry Development Roadmap

Meta Agent's telemetry system begins with a simple CLI interface and will expand to a VS Code experience. This roadmap summarises the planned stages.

## 1. CLI Baseline
- Record tokens, estimated cost, latency and guardrail hits via `TelemetryCollector`.
- Persist metrics in a local SQLite database using `TelemetryDB`.
- Display a one-line summary after each generation and provide `dashboard` and `export` commands.
- Enforce a default cost cap of $0.50 per run with warnings at 75% and 90%.

## 2. Enhanced CLI Reporting
- Surface cost cap and guardrail events in the dashboard output.
- Allow custom cost caps and metric selection via CLI flags.
- Provide JSON and CSV export suitable for bundling with generated agents.

## 3. VS Code Integration
- Reuse the telemetry database to power a VS Code panel.
- Show live token spend and latency charts while an agent runs.
- Offer quick access to historical runs and export actions from the editor.

## 4. Third-Party Observability
- Define an adapter layer for forwarding telemetry to external monitoring tools.
- Support custom endpoints using `TelemetryAPIClient`.

This staged approach ensures useful telemetry is available immediately in the CLI while paving the way for a richer developer experience in VS Code.
