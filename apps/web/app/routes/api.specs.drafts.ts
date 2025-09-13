import { json, type ActionFunctionArgs, type LoaderFunctionArgs } from "@remix-run/node";
import { eq, desc } from "drizzle-orm";
import { db, specDrafts, setAppUser, type SpecDraft, type NewSpecDraft } from "@metaagent/db";
import { AgentSpecSchema } from "@metaagent/spec";

// Mock auth - replace with real auth in Week 1
function getCurrentUserId(): string {
  // TODO: Extract from session/JWT
  return "01ARZ3NDEKTSV4RRFFQ69G5FAV"; // placeholder ULID
}

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const id = url.searchParams.get("id");
  
  const userId = getCurrentUserId();
  await setAppUser(userId);

  if (id) {
    // Get single draft
    const draft = await db
      .select()
      .from(specDrafts)
      .where(eq(specDrafts.id, id))
      .limit(1);

    if (draft.length === 0) {
      throw new Response("Draft not found", { status: 404 });
    }

    return json(draft[0]);
  } else {
    // List all drafts for user
    const drafts = await db
      .select()
      .from(specDrafts)
      .where(eq(specDrafts.ownerUserId, userId))
      .orderBy(desc(specDrafts.updatedAt));

    return json(drafts);
  }
}

export async function action({ request }: ActionFunctionArgs) {
  const userId = getCurrentUserId();
  await setAppUser(userId);

  if (request.method === "POST") {
    const body = await request.json();
    
    // Validate payload size
    const bodyStr = JSON.stringify(body);
    if (bodyStr.length > 200 * 1024) { // 200KB limit
      return json({ error: "Spec too large (>200KB)" }, { status: 400 });
    }

    if (body.id) {
      // Update existing draft
      const { id, name, spec, tags } = body;
      
      // Validate spec with Zod
      const validation = AgentSpecSchema.safeParse(spec);
      if (!validation.success) {
        return json({ 
          error: "Invalid spec", 
          validationErrors: validation.error.issues 
        }, { status: 400 });
      }

      const updated = await db
        .update(specDrafts)
        .set({ name, spec, tags })
        .where(eq(specDrafts.id, id))
        .returning();

      if (updated.length === 0) {
        return json({ error: "Draft not found or not authorized" }, { status: 404 });
      }

      return json(updated[0]);
    } else {
      // Create new draft
      const { name, spec, tags = [] } = body;

      // Validate spec with Zod (allow partial for drafts)
      if (spec && Object.keys(spec).length > 0) {
        const validation = AgentSpecSchema.safeParse(spec);
        if (!validation.success && validation.error.issues.some(issue => issue.code !== "invalid_type")) {
          // Allow type issues for incomplete drafts, but fail on other validation errors
          return json({ 
            error: "Invalid spec", 
            validationErrors: validation.error.issues 
          }, { status: 400 });
        }
      }

      const newDraft: NewSpecDraft = {
        ownerUserId: userId,
        name: name || "Untitled Draft",
        spec: spec || {},
        tags,
      };

      const created = await db
        .insert(specDrafts)
        .values(newDraft)
        .returning();

      return json(created[0], { status: 201 });
    }
  }

  if (request.method === "DELETE") {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    
    if (!id) {
      return json({ error: "Draft ID required" }, { status: 400 });
    }

    const deleted = await db
      .delete(specDrafts)
      .where(eq(specDrafts.id, id))
      .returning();

    if (deleted.length === 0) {
      return json({ error: "Draft not found or not authorized" }, { status: 404 });
    }

    return json({ success: true });
  }

  return json({ error: "Method not allowed" }, { status: 405 });
}
