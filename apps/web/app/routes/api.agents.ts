import type { LoaderFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node";
import { db, pool } from "@metaagent/db";

// DEV ONLY: stub user id for session context
const DEV_USER_ID = "00000000-0000-0000-0000-000000000001";

export async function loader({ request }: LoaderFunctionArgs) {
  // Set session-scoped current user id for RLS policies
  await pool.query("select set_config('app.current_user_id', $1, false)", [DEV_USER_ID]);

  // Query a few agents (will be filtered by RLS once FORCE is enabled)
  const result = await pool.query("select id, name, slug, owner_user_id from agents order by created_at desc limit 10");
  return json({ agents: result.rows });
}
