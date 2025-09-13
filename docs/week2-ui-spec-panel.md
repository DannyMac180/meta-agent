# Week 2 — UI Spec Panel (live validation): Detailed Plan

Owner: Web/Builder
Timeline: Week 2 (Mon–Fri)
Status: Planned

## Objectives
- Provide an in-browser editor to author Agent specs with instant validation and helpful feedback.
- Persist specs as user-owned Drafts and list them in “My Catalog”.
- Enable import/export, formatting, and schema-aware editing.

Acceptance (ties to Week 2):
- User can save a draft spec and see it in My Catalog as Draft.
- Live validation highlights issues as the user types (no page reload).

## Scope
- Remix pages/routes to create and edit draft specs.
- Monaco-based editor (JSON-first, optional YAML toggle) with schema + Zod validation.
- Draft persistence (Postgres) with RLS; list view for drafts.
- No builder execution yet (covered by other Week 2 bullets).

## Dependencies
- packages/spec (Zod validators, types): already present, serves as source of truth.
- packages/db (drizzle + SQL migrations): used for Drafts table + queries.
- apps/web (Remix): add routes, UI, loaders/actions.

## UX/Flows
- Routes
  - /specs/new?template=chatbot|web-automation|api-copilot
  - /specs/:draftId
  - /catalog/drafts
- Editor Screen
  - Left: Monaco editor (JSON), optional YAML toggle
  - Right: Validation panel (issues list), Meta sidebar (name/version/tags)
  - Top bar: Save (Cmd/Ctrl+S), Validate, Format, Import, Export, Template selector
- Drafts List
  - Grid/table of drafts (name, updated, tags); open to continue editing

## Technical Design
- Editor
  - monaco-editor + @monaco-editor/react
  - JSON default; YAML via js-yaml (parse/serialize) with a toggle
  - Prettier (standalone) for format JSON/YAML
- Schema & IntelliSense
  - Generate JSON Schema from Zod using zod-to-json-schema at build/startup
  - Register with Monaco JSON diagnostics for completions/hover/basic validation
- Live Validation
  - Primary validator: packages/spec AgentSpecSchema.safeParse()
  - Run in a Web Worker (debounced ~300ms) to keep UI responsive
  - Map Zod issues to Monaco markers: compute ranges via jsonc-parser from issue.path
  - Show structured list (path, message); clicking focuses editor range
- State & Data
  - Local editor state; dirty flag; optimistic Save via Remix fetcher
  - Import/Export: file upload/download (JSON/YAML), validate on import
- Persistence
  - New table spec_drafts(id uuid pk, owner_user_id uuid fk, name text, spec jsonb, tags text[], updated_at timestamptz)
  - RLS policy: owner-only; index on (owner_user_id, updated_at desc)
  - Migration: packages/db/migrations/002_spec_drafts.sql
- API & Routes (apps/web/app/routes)
  - specs.new.tsx: editor page creating a draft (POST to api)
  - specs.$id.tsx: editor page loading/updating existing draft
  - catalog.drafts.tsx: list drafts for current user
  - api.specs.drafts.ts: GET list, POST create/update, GET by id
- Auth Context
  - Reuse Week 1 auth stub to set current user (RLS assumes app.current_user_id)
- Telemetry/A11y
  - Track: open_editor, validate_success/fail, save_success/fail
  - Keyboard shortcuts, focus management, aria-live for validation results

## Data Model (SQL sketch)
- Migration 002_spec_drafts.sql
  - create table if not exists spec_drafts (
    id uuid primary key,
    owner_user_id uuid not null references app_users(id) on delete cascade,
    name text not null,
    spec jsonb not null,
    tags text[] default array[]::text[],
    updated_at timestamptz default now()
  );
  - create index if not exists idx_spec_drafts_owner on spec_drafts(owner_user_id, updated_at desc);
  - enable RLS; policy: owner_user_id = current_setting('app.current_user_id', true)::uuid

## Testing Plan
- Unit
  - packages/spec: existing tests; add cases for error path mapping (utility)
- Integration
  - Remix action/loader tests for api.specs.drafts (create, update, list, auth)
- E2E (Playwright)
  - Create from template → live error shows on invalid input → fix → Save → Drafts list shows
  - Import invalid JSON → error surfaced; valid JSON → accepted
- A11y
  - Keyboard shortcuts, focus ring, screen reader for error list

## Security & Performance
- Size limits: reject >200KB spec payloads server-side
- Sanitize file imports; validate before persisting
- Debounce validation; worker termination on unload; minimal schema payload

## Milestones (Day-by-day)
- Day 1: Create routes + scaffolding; Drafts table migration; basic editor rendering
- Day 2: JSON Schema generation; Monaco schema wiring; Save/Load draft API
- Day 3: Zod worker validation + marker mapping; Validation panel
- Day 4: Import/Export + Format; YAML toggle
- Day 5: Drafts list UI; tests (integration + smoke e2e); polish & a11y

## Deliverables
- Working editor with live validation and persistence
- Drafts list page
- SQL migration 002_spec_drafts.sql
- Minimal tests covering save/list and validation UX

## Risks & Mitigations
- Marker range mapping from Zod paths → use jsonc-parser and add tests
- Monaco bundle size → code split editor and lazy-load YAML support
- Schema drift vs Zod → generate schema from code on boot to avoid mismatch
