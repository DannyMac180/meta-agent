import { json } from "@remix-run/node";

export const loader = () => json({ status: "ready" });
