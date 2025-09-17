import { json, type ActionFunctionArgs } from "@remix-run/node";
import { requireUserId } from "../utils/session.server";
import { enqueueBuilderScaffold, type BuilderPackageOptions } from "@metaagent/queue";

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

    let packageOptions: BuilderPackageOptions | undefined;
    if (body?.package && typeof body.package === "object") {
      const includeZip = body.package.includeZip !== false;
      let docker: BuilderPackageOptions["docker"];
      if (body.package.docker && typeof body.package.docker === "object") {
        const enabled = Boolean(body.package.docker.enabled);
        const imageTag =
          body.package.docker.imageTag && typeof body.package.docker.imageTag === "string"
            ? body.package.docker.imageTag
            : undefined;
        docker = enabled ? { enabled, imageTag } : undefined;
      }
      packageOptions = {
        includeZip,
        ...(docker ? { docker } : {}),
      };
    }

    await enqueueBuilderScaffold({ userId, draftId, buildId, package: packageOptions });
    return json({ enqueued: true }, { status: 202 });
  } catch (err) {
    console.error("[scaffold] error", err);
    return json({ error: "Internal server error" }, { status: 500 });
  }
}
