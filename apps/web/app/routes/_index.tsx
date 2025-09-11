import type { LoaderFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";

export const loader: LoaderFunction = async () => {
  return json({ message: "Hello MetaAgent" });
};

export default function Index() {
  const { message } = useLoaderData<typeof loader>();
  return (
    <main style={{ padding: 32 }}>
      <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>{message}</h1>
      <nav style={{ marginTop: 16 }}>
        <Link to="/api/hello" style={{ textDecoration: "underline", color: "blue" }}>
          Raw JSON
        </Link>
      </nav>
    </main>
  );
}
