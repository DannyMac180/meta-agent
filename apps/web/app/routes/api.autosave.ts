import { json, type ActionFunctionArgs } from "@remix-run/node";
import { enqueueDraftAutosave } from "@metaagent/queue";

function getCurrentUserId(): string {
  return "01ARZ3NDEKTSV4RRFFQ69G5FAV";
}

export async function action({ request }: ActionFunctionArgs) {
  if (request.method !== "POST") {
    return json({ error: "Method not allowed" }, { status: 405 });
  }

  const userId = getCurrentUserId();
  const body = await request.json();

  if (!body || !body.title) {
    return json({ error: "Missing draft title" }, { status: 400 });
  }

  await enqueueDraftAutosave({
    userId,
    draft: {
      id: body.id,
      templateId: body.templateId,
      title: body.title,
      payload: body.payload,
      isDraft: body.isDraft ?? true,
      status: body.status ?? 'DRAFT',
    },
  }, {
    jobId: body.id ? `draft:${userId}:${body.id}` : undefined,
  });

  return json({ enqueued: true }, { status: 202 });
}
