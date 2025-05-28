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
| `slug`       | Unique identifier used when referencing the template.   |
| `title`      | Human friendly name.                                    |
| `description`| Short summary of the template's purpose.                |
| `category`   | One of the primary categories above.                    |
| `subcategory`| Optional free‑form subcategory for finer grouping.      |
| `complexity` | `basic`, `intermediate` or `advanced`.                  |
| `tags`       | List of additional keywords.                            |

## Classification Examples

```
- slug: basic-chat
  title: Basic Chat Bot
  description: Minimal conversational agent.
  category: conversation
  subcategory: qa
  complexity: basic
  tags: ["chat", "starter"]

- slug: structured-reasoner
  title: Structured Reasoner
  description: Performs multi-step reasoning with tool calls.
  category: reasoning
  subcategory: step-by-step
  complexity: advanced
  tags: ["chain-of-thought"]
```

These examples illustrate how templates are labelled using the schema. Tools consuming templates can rely on these fields to search for compatible archetypes and to mix templates with similar characteristics.
