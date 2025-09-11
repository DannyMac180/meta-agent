import type { ActionFunctionArgs, LoaderFunctionArgs } from "@remix-run/node";
import { json, redirect } from "@remix-run/node";
import { Form } from "@remix-run/react";
import { createUserSession, getUserId } from "../utils/session.server";

export async function loader({ request }: LoaderFunctionArgs) {
  if (await getUserId(request)) return redirect("/");
  return json({});
}

export async function action({ request }: ActionFunctionArgs) {
  const form = await request.formData();
  const username = String(form.get("username"));
  if (!username) return json({ error: "username required" }, { status: 400 });
  return createUserSession(username, "/");
}

export default function Login() {
  return (
    <Form method="post" style={{ padding: 32 }}>
      <label>
        Dev Username
        <input name="username" style={{ border: "1px solid #ccc", marginLeft: 8 }} />
      </label>
      <button type="submit" style={{ marginLeft: 8 }}>Login</button>
    </Form>
  );
}
