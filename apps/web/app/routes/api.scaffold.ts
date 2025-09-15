import { json, type ActionFunctionArgs } from "@remix-run/node";
import { requireUserId } from "../utils/session.server";
import { enqueueBuilderScaffold } from "@metaagent/queue";

export async function action({ request }: ActionFunctionArgs) {
  if (request.method !== "POST") {
    return json({ error: "Method not allowed" }, { status: 405 });
  }

  try {
    const userId = await requireUserId(request);
    const body = await request.json();
    const draftId = body?.draftId;
    if (!draftId || typeof draftId !== "string") {
      return json({ error: "draftId is required" }, { status: 400 });
    }

    const buildId = body?.buildId && typeof body.buildId === "string" ? body.buildId : undefined;

    await enqueueBuilderScaffold({ userId, draftId, buildId });
    return json({ enqueued: true }, { status: 202 });
  } catch (err) {
    console.error("[scaffold] error", err);
    return json({ error: "Internal server error" }, { status: 500 });
  }
}
