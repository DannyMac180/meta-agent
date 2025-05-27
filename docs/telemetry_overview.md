# Telemetry System Overview

Meta Agent collects basic metrics for each generation run using the
`TelemetryCollector` and persists them in a small SQLite database via
`TelemetryDB`. Each run stores the number of tokens consumed, the
estimated cost, total latency and the number of guardrail hits.

## Dashboard

Use the CLI command `meta-agent dashboard` to inspect recorded runs.
It displays a table summarising timestamp, token usage, cost, latency
and guardrail violations. When no data is available the command prints
"No telemetry data found.".

## Exporting Data

Telemetry can be exported in JSON or CSV format using
`meta-agent export --format <json|csv> --output <file>`.
Optional `--start` and `--end` parameters filter by timestamp and
`--metric` can restrict the columns included. Compression is
supported automatically when the output filename ends with `.gz`.

## API Integration

The optional `TelemetryAPIClient` class sends traces or metrics to
external services. Endpoints are configured with `EndpointConfig` and
`attach_runner` can instrument an Agents SDK `Runner` to forward span
information after each run. Errors while sending are logged and retried
with backoff.

## Error Handling

The `TelemetryCollector` records cost-cap warnings and guardrail
violations as events with severity levels. These events can be viewed in
the exported data for troubleshooting.
