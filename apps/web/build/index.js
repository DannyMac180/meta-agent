var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: !0 });
};

// app/entry.server.tsx
var entry_server_exports = {};
__export(entry_server_exports, {
  default: () => handleRequest
});
import { RemixServer } from "@remix-run/react";
import { renderToString } from "react-dom/server";
import { jsx } from "react/jsx-runtime";
function handleRequest(request, responseStatusCode, responseHeaders, remixContext) {
  let markup = renderToString(
    /* @__PURE__ */ jsx(RemixServer, { context: remixContext, url: request.url })
  );
  return responseHeaders.set("Content-Type", "text/html"), new Response("<!DOCTYPE html>" + markup, {
    status: responseStatusCode,
    headers: responseHeaders
  });
}

// app/root.tsx
var root_exports = {};
__export(root_exports, {
  default: () => App,
  links: () => links,
  loader: () => loader
});
import { json } from "@remix-run/node";
import {
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData
} from "@remix-run/react";

// app/utils/session.server.ts
import { createCookieSessionStorage, redirect } from "@remix-run/node";
var SESSION_SECRET = process.env.SESSION_SECRET_DEV || "dev-secret-insecure";
if (SESSION_SECRET === "dev-secret-insecure")
  throw new Error("Missing SESSION_SECRET_DEV");
var storage = createCookieSessionStorage({
  cookie: {
    name: "_metaagent_session",
    httpOnly: !0,
    path: "/",
    sameSite: "lax",
    secure: !1,
    secrets: [SESSION_SECRET]
  }
});
async function getUserId(request) {
  return (await storage.getSession(request.headers.get("Cookie"))).get("userId");
}
async function createUserSession(userId, redirectTo) {
  let session = await storage.getSession();
  return session.set("userId", userId), redirect(redirectTo, {
    headers: { "Set-Cookie": await storage.commitSession(session) }
  });
}
async function logout(request) {
  let session = await storage.getSession(request.headers.get("Cookie"));
  return redirect("/", {
    headers: { "Set-Cookie": await storage.destroySession(session) }
  });
}

// app/root.tsx
import { jsx as jsx2, jsxs } from "react/jsx-runtime";
var links = () => [];
async function loader({ request }) {
  let user = await getUserId(request);
  return json({ user });
}
function App() {
  let { user } = useLoaderData();
  return /* @__PURE__ */ jsxs("html", { lang: "en", children: [
    /* @__PURE__ */ jsxs("head", { children: [
      /* @__PURE__ */ jsx2("meta", { charSet: "utf-8" }),
      /* @__PURE__ */ jsx2("meta", { name: "viewport", content: "width=device-width, initial-scale=1" }),
      /* @__PURE__ */ jsx2(Meta, {}),
      /* @__PURE__ */ jsx2(Links, {})
    ] }),
    /* @__PURE__ */ jsxs("body", { children: [
      /* @__PURE__ */ jsx2("header", { style: { padding: 12, borderBottom: "1px solid #ddd" }, children: user ? /* @__PURE__ */ jsxs("form", { method: "post", action: "/auth/logout", style: { display: "inline" }, children: [
        /* @__PURE__ */ jsxs("span", { style: { marginRight: 8 }, children: [
          "Hi ",
          user
        ] }),
        /* @__PURE__ */ jsx2("button", { type: "submit", children: "Logout" })
      ] }) : /* @__PURE__ */ jsx2("a", { href: "/auth/login", children: "Login" }) }),
      /* @__PURE__ */ jsx2(Outlet, {}),
      /* @__PURE__ */ jsx2(ScrollRestoration, {}),
      /* @__PURE__ */ jsx2(Scripts, {}),
      /* @__PURE__ */ jsx2(LiveReload, {})
    ] })
  ] });
}

// app/routes/auth.logout.ts
var auth_logout_exports = {};
__export(auth_logout_exports, {
  action: () => action
});
async function action({ request }) {
  return logout(request);
}

// app/routes/api.agents.ts
var api_agents_exports = {};
__export(api_agents_exports, {
  loader: () => loader2
});
import { json as json2 } from "@remix-run/node";
import { pool } from "@metaagent/db";
var DEV_USER_ID = "00000000-0000-0000-0000-000000000001";
async function loader2({ request }) {
  await pool.query("select set_config('app.current_user_id', $1, false)", [DEV_USER_ID]);
  let result = await pool.query("select id, name, slug, owner_user_id from agents order by created_at desc limit 10");
  return json2({ agents: result.rows });
}

// app/routes/auth.login.tsx
var auth_login_exports = {};
__export(auth_login_exports, {
  action: () => action2,
  default: () => Login,
  loader: () => loader3
});
import { json as json3, redirect as redirect2 } from "@remix-run/node";
import { Form } from "@remix-run/react";
import { jsx as jsx3, jsxs as jsxs2 } from "react/jsx-runtime";
async function loader3({ request }) {
  return await getUserId(request) ? redirect2("/") : json3({});
}
async function action2({ request }) {
  let form = await request.formData(), username = String(form.get("username"));
  return username ? createUserSession(username, "/") : json3({ error: "username required" }, { status: 400 });
}
function Login() {
  return /* @__PURE__ */ jsxs2(Form, { method: "post", style: { padding: 32 }, children: [
    /* @__PURE__ */ jsxs2("label", { children: [
      "Dev Username",
      /* @__PURE__ */ jsx3("input", { name: "username", style: { border: "1px solid #ccc", marginLeft: 8 } })
    ] }),
    /* @__PURE__ */ jsx3("button", { type: "submit", style: { marginLeft: 8 }, children: "Login" })
  ] });
}

// app/routes/api.hello.ts
var api_hello_exports = {};
__export(api_hello_exports, {
  loader: () => loader4
});
import { json as json4 } from "@remix-run/node";
var loader4 = () => json4({ ok: !0, at: (/* @__PURE__ */ new Date()).toISOString() });

// app/routes/healthz.ts
var healthz_exports = {};
__export(healthz_exports, {
  loader: () => loader5
});
import { json as json5 } from "@remix-run/node";
var loader5 = () => json5({ status: "ok" });

// app/routes/_index.tsx
var index_exports = {};
__export(index_exports, {
  default: () => Index,
  loader: () => loader6
});
import { json as json6 } from "@remix-run/node";
import { useLoaderData as useLoaderData2, Link } from "@remix-run/react";
import { jsx as jsx4, jsxs as jsxs3 } from "react/jsx-runtime";
var loader6 = async () => json6({ message: "Hello MetaAgent" });
function Index() {
  let { message } = useLoaderData2();
  return /* @__PURE__ */ jsxs3("main", { style: { padding: 32 }, children: [
    /* @__PURE__ */ jsx4("h1", { style: { fontSize: "2rem", fontWeight: "bold" }, children: message }),
    /* @__PURE__ */ jsx4("nav", { style: { marginTop: 16 }, children: /* @__PURE__ */ jsx4(Link, { to: "/api/hello", style: { textDecoration: "underline", color: "blue" }, children: "Raw JSON" }) })
  ] });
}

// app/routes/readyz.ts
var readyz_exports = {};
__export(readyz_exports, {
  loader: () => loader7
});
import { json as json7 } from "@remix-run/node";
var loader7 = () => json7({ status: "ready" });

// server-assets-manifest:@remix-run/dev/assets-manifest
var assets_manifest_default = { entry: { module: "/build/entry.client-X7YHCF7F.js", imports: ["/build/_shared/chunk-HWQ7IXSS.js", "/build/_shared/chunk-Q3IECNXJ.js"] }, routes: { root: { id: "root", parentId: void 0, path: "", index: void 0, caseSensitive: void 0, module: "/build/root-CTD66XX2.js", imports: ["/build/_shared/chunk-PGOH7JLP.js"], hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/_index": { id: "routes/_index", parentId: "root", path: void 0, index: !0, caseSensitive: void 0, module: "/build/routes/_index-OZ6Z7A4S.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/api.agents": { id: "routes/api.agents", parentId: "root", path: "api/agents", index: void 0, caseSensitive: void 0, module: "/build/routes/api.agents-SPBG63TZ.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/api.hello": { id: "routes/api.hello", parentId: "root", path: "api/hello", index: void 0, caseSensitive: void 0, module: "/build/routes/api.hello-T6FN7MBG.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/auth.login": { id: "routes/auth.login", parentId: "root", path: "auth/login", index: void 0, caseSensitive: void 0, module: "/build/routes/auth.login-73UZSDJY.js", imports: void 0, hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/auth.logout": { id: "routes/auth.logout", parentId: "root", path: "auth/logout", index: void 0, caseSensitive: void 0, module: "/build/routes/auth.logout-626NX3Q4.js", imports: void 0, hasAction: !0, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/healthz": { id: "routes/healthz", parentId: "root", path: "healthz", index: void 0, caseSensitive: void 0, module: "/build/routes/healthz-3XLKHQJA.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/readyz": { id: "routes/readyz", parentId: "root", path: "readyz", index: void 0, caseSensitive: void 0, module: "/build/routes/readyz-R5KZZXLX.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 } }, version: "67bf159e", hmr: void 0, url: "/build/manifest-67BF159E.js" };

// server-entry-module:@remix-run/dev/server-build
var mode = "production", assetsBuildDirectory = "public/build", future = { v3_fetcherPersist: !1, v3_relativeSplatPath: !1, v3_throwAbortReason: !1, v3_routeConfig: !1, v3_singleFetch: !1, v3_lazyRouteDiscovery: !1, unstable_optimizeDeps: !1 }, publicPath = "/build/", entry = { module: entry_server_exports }, routes = {
  root: {
    id: "root",
    parentId: void 0,
    path: "",
    index: void 0,
    caseSensitive: void 0,
    module: root_exports
  },
  "routes/auth.logout": {
    id: "routes/auth.logout",
    parentId: "root",
    path: "auth/logout",
    index: void 0,
    caseSensitive: void 0,
    module: auth_logout_exports
  },
  "routes/api.agents": {
    id: "routes/api.agents",
    parentId: "root",
    path: "api/agents",
    index: void 0,
    caseSensitive: void 0,
    module: api_agents_exports
  },
  "routes/auth.login": {
    id: "routes/auth.login",
    parentId: "root",
    path: "auth/login",
    index: void 0,
    caseSensitive: void 0,
    module: auth_login_exports
  },
  "routes/api.hello": {
    id: "routes/api.hello",
    parentId: "root",
    path: "api/hello",
    index: void 0,
    caseSensitive: void 0,
    module: api_hello_exports
  },
  "routes/healthz": {
    id: "routes/healthz",
    parentId: "root",
    path: "healthz",
    index: void 0,
    caseSensitive: void 0,
    module: healthz_exports
  },
  "routes/_index": {
    id: "routes/_index",
    parentId: "root",
    path: void 0,
    index: !0,
    caseSensitive: void 0,
    module: index_exports
  },
  "routes/readyz": {
    id: "routes/readyz",
    parentId: "root",
    path: "readyz",
    index: void 0,
    caseSensitive: void 0,
    module: readyz_exports
  }
};
export {
  assets_manifest_default as assets,
  assetsBuildDirectory,
  entry,
  future,
  mode,
  publicPath,
  routes
};
