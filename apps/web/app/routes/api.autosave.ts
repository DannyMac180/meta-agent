import { json, type ActionFunctionArgs } from "@remix-run/node";
import { requireUserId } from "../utils/session.server";
import { enqueueDraftAutosave } from "@metaagent/queue";

const rateLimitMap = new Map<string, { count: number; resetAt: number }>();
const RATE_LIMIT_PER_MINUTE = 30;
const RATE_LIMIT_WINDOW_MS = 60 * 1000;

function checkRateLimit(userId: string): boolean {
  const now = Date.now();
  const userLimit = rateLimitMap.get(userId);
  
  if (!userLimit || now > userLimit.resetAt) {
    rateLimitMap.set(userId, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
    return true;
  }
  
  if (userLimit.count >= RATE_LIMIT_PER_MINUTE) {
    return false;
  }
  
  userLimit.count++;
  return true;
}

function validatePayload(body: any): { valid: boolean; error?: string } {
  if (!body || typeof body !== 'object') {
    return { valid: false, error: "Invalid request body" };
  }
  
  if (!body.title || typeof body.title !== 'string' || body.title.length > 200) {
    return { valid: false, error: "Missing or invalid title (max 200 chars)" };
  }
  
  if (body.payload && JSON.stringify(body.payload).length > 500 * 1024) {
    return { valid: false, error: "Payload too large (max 500KB)" };
  }
  
  if (body.id && (typeof body.id !== 'string' || body.id.length > 100)) {
    return { valid: false, error: "Invalid draft ID" };
  }
  
  return { valid: true };
}

export async function action({ request }: ActionFunctionArgs) {
  if (request.method !== "POST") {
    return json({ error: "Method not allowed" }, { status: 405 });
  }

  try {
    const userId = await requireUserId(request);
    
    if (!checkRateLimit(userId)) {
      console.warn(`[autosave] Rate limit exceeded for user ${userId}`);
      return json({ error: "Rate limit exceeded" }, { status: 429 });
    }

    const body = await request.json();
    const validation = validatePayload(body);
    
    if (!validation.valid) {
      console.warn(`[autosave] Validation failed for user ${userId}: ${validation.error}`);
      return json({ error: validation.error }, { status: 400 });
    }

    console.log(`[autosave] Enqueuing draft autosave for user ${userId}, draft ${body.id || 'new'}`);
    
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
  } catch (error) {
    console.error(`[autosave] Error processing autosave request:`, error);
    return json({ error: "Internal server error" }, { status: 500 });
  }
}
