import { json } from "@remix-run/node";

export const loader = () => json({ ok: true, at: new Date().toISOString() });
