# Templates and Scaffolding

This repository exposes three templates via @metaagent/templates:
- chatbot
- web-automation
- api-copilot

Scaffold a project zip from a template:

pnpm --filter @metaagent/builder scaffold -- --template chatbot --out ./dist/my-chatbot --name my-chatbot --description "A friendly chatbot"

Outputs:
- dist/my-chatbot (project tree)
- dist/my-chatbot.zip (zip archive)

Template defaults are sourced from the template's defaultSpec. The scaffold includes:
- package.json, tsconfig.json, README.md
- spec.json (agent spec)
- src/index.ts (simple run function)
- test/basic.test.ts (Vitest)
