#!/usr/bin/env ts-node-esm
import { templates } from "@metaagent/templates";
import { scaffoldProject } from "../handlers/scaffoldProject.js";

async function main() {
  const id = process.argv[2] || "chatbot";
  const t = templates.find((x) => x.id === id);
  if (!t) {
    console.error(`Unknown template: ${id}`);
    process.exit(1);
  }
  const draft = { title: t.defaultSpec.title, payload: t.defaultSpec.payload };
  const res = await scaffoldProject({ templateId: id, draft, buildId: `dev-${Date.now()}` });
  console.log(JSON.stringify(res, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
