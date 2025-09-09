# Checklists

## Feature PR Checklist
- [ ] Update or add unit tests.
- [ ] Add/refresh demo scenario in `apps/web/docs/demos.md`.
- [ ] If touching spec: update `packages/spec` types + zod + examples.
- [ ] If touching DB: add migration; document in `CHANGELOG.md`.
- [ ] Ensure gates run locally: `tsc`, `eslint`, `vitest`, `npm audit`, license.
- [ ] Confirm logs/traces visible in UI for new paths.

## Template Addition Checklist
- [ ] Folders: `src/mastra/{agents,tools,workflows}`, optional `src/server/`.
- [ ] README with quickstart + `.env.example`.
- [ ] At least one eval in `tests/evals/`.
- [ ] `package.json` with scripts: `dev`, `build`, `start`, `test`.
- [ ] Works with Builder scaffolder (placeholders replaced).

## Release Gate (end of week)
- [ ] All acceptance criteria in `delivery_plan.md` met.
- [ ] Build Report samples archived.
- [ ] Two recorded end-to-end demos updated.
