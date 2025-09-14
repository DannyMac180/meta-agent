import { redirect, type LoaderFunctionArgs } from "@remix-run/node";
import { createSpecDraftService } from "../utils/specDraft.server";

function getUserId() { return "01ARZ3NDEKTSV4RRFFQ69G5FAV"; }

export async function loader({ request }: LoaderFunctionArgs) {
  const userId = getUserId();
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
