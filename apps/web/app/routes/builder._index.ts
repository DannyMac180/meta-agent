import { redirect, type LoaderFunctionArgs } from "@remix-run/node";
import { requireUserId } from "../utils/session.server";
import { createSpecDraftService } from "../utils/specDraft.server";

export async function loader({ request }: LoaderFunctionArgs) {
  const userId = await requireUserId(request);
  const service = createSpecDraftService(userId);

  const created = await service.saveDraft({
    title: "Untitled Agent",
    payload: {},
    isDraft: true,
    status: "DRAFT",
  });

  return redirect(`/builder/${created.id}`);
}

export default function BuilderIndexRedirect() {
  return null;
}
