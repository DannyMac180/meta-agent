import type { LoaderFunctionArgs, LinksFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import {
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData,
  Link,
} from "@remix-run/react";
import { getUserId } from "./utils/session.server";
import specEditorStyles from "./styles/spec-editor.css";

export const links: LinksFunction = () => [
  { rel: "stylesheet", href: specEditorStyles },
];

export async function loader({ request }: LoaderFunctionArgs) {
  const user = await getUserId(request);
  return json({ user });
}

export default function App() {
  const { user } = useLoaderData<typeof loader>();
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <header style={{ padding: 12, borderBottom: "1px solid #ddd", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <nav style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
            <Link to="/" style={{ fontWeight: "bold", textDecoration: "none", color: "#1976d2" }}>MetaAgent</Link>
            <Link to="/catalog/drafts" style={{ textDecoration: "none", color: "#666" }}>My Catalog</Link>
            <Link to="/specs/new" style={{ textDecoration: "none", color: "#666" }}>New Spec</Link>
          </nav>
          {user ? (
            <form method="post" action="/auth/logout" style={{ display: "inline" }}>
              <span style={{ marginRight: 8 }}>Hi {user}</span>
              <button type="submit">Logout</button>
            </form>
          ) : (
            <a href="/auth/login">Login</a>
          )}
        </header>
        <Outlet />
        <ScrollRestoration />
        <Scripts />
        <LiveReload />
      </body>
    </html>
  );
}
