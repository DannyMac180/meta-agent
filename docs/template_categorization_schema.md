# Template Categorization Schema

This document describes the hierarchical system used to organise agent templates. Each template records a primary category, an optional subcategory and a complexity level. Metadata fields are standardised so that templates can be discovered, filtered and mixed consistently.

## Primary Categories

- **conversation** – Interactive dialogue agents such as chat bots or FAQ assistants.
- **reasoning** – Step‑by‑step or analytical agents focused on problem solving.
- **creative** – Templates that produce creative text, images or other media.
- **data_processing** – Agents that transform or analyse data.
- **integration** – Templates that orchestrate tools or external APIs.

Additional categories may be introduced in future. Unknown values should be ignored by older tooling.

## Metadata Fields

Each template defines the following fields:

| Field        | Description                                             |
|--------------|---------------------------------------------------------|
| `slug`            | Unique identifier used when referencing the template.   |
| `title`           | Human friendly name.                                    |
| `description`     | Short summary of the template's purpose.                |
| `intended_use`    | Primary scenario the template targets.                  |
| `io_contract`     | Mapping of expected input and output.                   |
| `tools`           | Tools referenced by the template.                       |
| `guardrails`      | Guardrails applied when running the template.           |
| `model_pref`      | Preferred model/provider for generation.                |
| `category`        | One of the primary categories above.                    |
| `subcategory`     | Optional free‑form subcategory for finer grouping.      |
| `complexity`      | `basic`, `intermediate` or `advanced`.                  |
| `created_by`      | Author or source of the template.                       |
| `semver`          | Semantic version of the template.                       |
| `last_test_passed`| ISO timestamp when tests last passed.                   |
| `tags`            | List of additional keywords.                            |
| `eval_score`      | (optional) Evaluation score from tests.                 |
| `cost_estimate`   | (optional) Estimated cost per run in dollars.           |
| `tokens_per_run`  | (optional) Approximate token usage per run.             |

## Classification Examples

```
- slug: basic-chat
  title: Basic Chat Bot
  description: Minimal conversational agent.
  intended_use: demo
  io_contract:
    input: text
    output: text
  tools: []
  guardrails: []
  model_pref: gpt3
  category: conversation
  subcategory: qa
  complexity: basic
  tags: ["chat", "starter"]

- slug: structured-reasoner
  title: Structured Reasoner
  description: Performs multi-step reasoning with tool calls.
  intended_use: demo
  io_contract:
    input: text
    output: text
  tools: []
  guardrails: []
  model_pref: gpt3
  category: reasoning
  subcategory: step-by-step
  complexity: advanced
  tags: ["chain-of-thought"]
```

These examples illustrate how templates are labelled using the schema. Tools consuming templates can rely on these fields to search for compatible archetypes and to mix templates with similar characteristics.
