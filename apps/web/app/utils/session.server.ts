import { createCookieSessionStorage, redirect } from "@remix-run/node";

const SESSION_SECRET = process.env.SESSION_SECRET_DEV || "dev-secret-insecure";
if (SESSION_SECRET === "dev-secret-insecure" && process.env.NODE_ENV === "production") {
  throw new Error("Missing SESSION_SECRET_DEV");
}

const storage = createCookieSessionStorage({
  cookie: {
    name: "_metaagent_session",
    httpOnly: true,
    path: "/",
    sameSite: "lax",
    secure: false,
    secrets: [SESSION_SECRET],
  },
});

export async function getUserId(request: Request) {
  const session = await storage.getSession(request.headers.get("Cookie"));
  return session.get("userId") as string | undefined;
}

export async function requireUserId(request: Request) {
  const userId = await getUserId(request);
  if (!userId) throw redirect("/auth/login");
  return userId;
}

export async function createUserSession(userId: string, redirectTo: string) {
  const session = await storage.getSession();
  session.set("userId", userId);
  return redirect(redirectTo, {
    headers: { "Set-Cookie": await storage.commitSession(session) },
  });
}

export async function logout(request: Request) {
  const session = await storage.getSession(request.headers.get("Cookie"));
  return redirect("/", {
    headers: { "Set-Cookie": await storage.destroySession(session) },
  });
}
