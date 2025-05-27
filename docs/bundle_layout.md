# Bundle Layout

This document specifies the directory structure and metadata schema for the artefact bundle produced by Meta Agent.

## Directory Structure

```
<bundle>/
├── agent.py              # entry point for the generated agent
├── requirements.txt      # pinned dependencies
├── README.md             # usage instructions
├── tests/                # unit tests
├── guardrails/           # guardrail definitions and tests
├── traces/               # evaluation logs
└── bundle.json           # metadata file
```

Additional files may be placed under `tests/`, `guardrails/` or `traces/` but the files listed above are required. Future versions may add optional directories; consumers should ignore unknown entries.

## Metadata Schema

The `bundle.json` file describes the bundle. The schema is versioned so that new
fields can be introduced without breaking existing tooling. The `BundleGenerator`
allows callers to inject additional metadata fields when creating a bundle, which
will be included in this file. The `meta_agent_version` field is populated from
the running package version unless you supply a value using `metadata_fields`.

```json
{
  "schema_version": "1.0",
  "created_at": "2025-01-01T00:00:00Z",
  "meta_agent_version": "0.1.0",
  "custom": {"key": "value"}
}
```

- `schema_version` — fixed string identifying the structure of the metadata.
- `created_at` — ISO‑8601 timestamp of when the bundle was generated.
- `meta_agent_version` — version of Meta Agent that produced the bundle.
- `custom` — arbitrary key/value pairs for extensibility. Unknown top-level fields
  are allowed and preserved. Use `custom_metadata` when invoking `BundleGenerator`
  to populate this section.

Custom fields may also be added at the top level by future components. Tools
reading the metadata should ignore unrecognised fields while still enforcing the
presence of `schema_version`.
You can supply additional top-level keys using the `metadata_fields` argument
when generating a bundle.

## Bundle API

Use the :class:`meta_agent.bundle.Bundle` helper to load and introspect bundles.
It parses ``bundle.json`` and provides convenience methods to list files and
access metadata.

```python
from meta_agent import Bundle

bundle = Bundle("path/to/bundle")
print(bundle.metadata.meta_agent_version)
print(bundle.list_files())
```

## Extensibility Hooks

``BundleGenerator.generate`` accepts optional ``pre_hook`` and ``post_hook``
callables. The pre hook runs before any files are created; the post hook runs
after ``bundle.json`` is written and Git operations complete. Hooks receive the
bundle directory path, and the post hook also receives the loaded
``BundleMetadata`` object.

```python
def add_marker(path: Path) -> None:
    (path / "MARKER").write_text("generated")

def report(path: Path, meta: BundleMetadata) -> None:
    print("created", meta.meta_agent_version)

gen.generate(agent_code="print('x')", pre_hook=add_marker, post_hook=report)
```
