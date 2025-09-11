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
} from "@remix-run/react";
import { getUserId } from "./utils/session.server";

export const links: LinksFunction = () => [];

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
        <header style={{ padding: 12, borderBottom: "1px solid #ddd" }}>
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
