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
  useLoaderData,
  Link
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

// app/styles/spec-editor.css
var spec_editor_default = "/build/_assets/spec-editor-VGQYUEQU.css";

// app/root.tsx
import { jsx as jsx2, jsxs } from "react/jsx-runtime";
var links = () => [
  { rel: "stylesheet", href: spec_editor_default }
];
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
      /* @__PURE__ */ jsxs("header", { style: { padding: 12, borderBottom: "1px solid #ddd", display: "flex", justifyContent: "space-between", alignItems: "center" }, children: [
        /* @__PURE__ */ jsxs("nav", { style: { display: "flex", gap: "1rem", alignItems: "center" }, children: [
          /* @__PURE__ */ jsx2(Link, { to: "/", style: { fontWeight: "bold", textDecoration: "none", color: "#1976d2" }, children: "MetaAgent" }),
          /* @__PURE__ */ jsx2(Link, { to: "/catalog/drafts", style: { textDecoration: "none", color: "#666" }, children: "My Drafts" }),
          /* @__PURE__ */ jsx2(Link, { to: "/specs/new", style: { textDecoration: "none", color: "#666" }, children: "New Spec" })
        ] }),
        user ? /* @__PURE__ */ jsxs("form", { method: "post", action: "/auth/logout", style: { display: "inline" }, children: [
          /* @__PURE__ */ jsxs("span", { style: { marginRight: 8 }, children: [
            "Hi ",
            user
          ] }),
          /* @__PURE__ */ jsx2("button", { type: "submit", children: "Logout" })
        ] }) : /* @__PURE__ */ jsx2("a", { href: "/auth/login", children: "Login" })
      ] }),
      /* @__PURE__ */ jsx2(Outlet, {}),
      /* @__PURE__ */ jsx2(ScrollRestoration, {}),
      /* @__PURE__ */ jsx2(Scripts, {}),
      /* @__PURE__ */ jsx2(LiveReload, {})
    ] })
  ] });
}

// app/routes/api.specs.drafts.ts
var api_specs_drafts_exports = {};
__export(api_specs_drafts_exports, {
  action: () => action,
  loader: () => loader2
});
import { json as json2 } from "@remix-run/node";
import { eq, desc } from "drizzle-orm";
import { db, specDrafts, setAppUser } from "@metaagent/db";
import { AgentSpecSchema } from "@metaagent/spec";
function getCurrentUserId() {
  return "01ARZ3NDEKTSV4RRFFQ69G5FAV";
}
async function loader2({ request }) {
  let id = new URL(request.url).searchParams.get("id"), userId = getCurrentUserId();
  if (await setAppUser(userId), id) {
    let draft = await db.select().from(specDrafts).where(eq(specDrafts.id, id)).limit(1);
    if (draft.length === 0)
      throw new Response("Draft not found", { status: 404 });
    return json2(draft[0]);
  } else {
    let drafts = await db.select().from(specDrafts).where(eq(specDrafts.ownerUserId, userId)).orderBy(desc(specDrafts.updatedAt));
    return json2(drafts);
  }
}
async function action({ request }) {
  let userId = getCurrentUserId();
  if (await setAppUser(userId), request.method === "POST") {
    let body = await request.json();
    if (JSON.stringify(body).length > 200 * 1024)
      return json2({ error: "Spec too large (>200KB)" }, { status: 400 });
    if (body.id) {
      let { id, name, spec, tags } = body, validation = AgentSpecSchema.safeParse(spec);
      if (!validation.success)
        return json2({
          error: "Invalid spec",
          validationErrors: validation.error.issues
        }, { status: 400 });
      let updated = await db.update(specDrafts).set({ name, spec, tags }).where(eq(specDrafts.id, id)).returning();
      return updated.length === 0 ? json2({ error: "Draft not found or not authorized" }, { status: 404 }) : json2(updated[0]);
    } else {
      let { name, spec, tags = [] } = body;
      if (spec && Object.keys(spec).length > 0) {
        let validation = AgentSpecSchema.safeParse(spec);
        if (!validation.success && validation.error.issues.some((issue) => issue.code !== "invalid_type"))
          return json2({
            error: "Invalid spec",
            validationErrors: validation.error.issues
          }, { status: 400 });
      }
      let newDraft = {
        ownerUserId: userId,
        name: name || "Untitled Draft",
        spec: spec || {},
        tags
      }, created = await db.insert(specDrafts).values(newDraft).returning();
      return json2(created[0], { status: 201 });
    }
  }
  if (request.method === "DELETE") {
    let id = new URL(request.url).searchParams.get("id");
    return id ? (await db.delete(specDrafts).where(eq(specDrafts.id, id)).returning()).length === 0 ? json2({ error: "Draft not found or not authorized" }, { status: 404 }) : json2({ success: !0 }) : json2({ error: "Draft ID required" }, { status: 400 });
  }
  return json2({ error: "Method not allowed" }, { status: 405 });
}

// app/routes/builder.$draftId.tsx
var builder_draftId_exports = {};
__export(builder_draftId_exports, {
  action: () => action2,
  default: () => BuilderRoute,
  loader: () => loader3
});
import { json as json3 } from "@remix-run/node";
import { useLoaderData as useLoaderData2, useNavigate, useSearchParams } from "@remix-run/react";

// app/utils/specDraft.server.ts
import { eq as eq2, and, desc as desc2 } from "drizzle-orm";
import { db as db2, specDrafts as specDrafts2, setAppUser as setAppUser2 } from "@metaagent/db";
var SpecDraftService = class {
  constructor(userId) {
    this.userId = userId;
  }
  async saveDraft(input) {
    if (await setAppUser2(this.userId), input.id && (await db2.select().from(specDrafts2).where(
      and(
        eq2(specDrafts2.id, input.id),
        eq2(specDrafts2.ownerUserId, this.userId)
      )
    ).limit(1)).length > 0) {
      let [updated] = await db2.update(specDrafts2).set({
        title: input.title,
        spec: input.payload,
        templateId: input.templateId,
        isDraft: input.isDraft ?? !0,
        status: input.status ?? "DRAFT",
        updatedAt: /* @__PURE__ */ new Date()
      }).where(eq2(specDrafts2.id, input.id)).returning();
      return this.recordToSpecDraft(updated);
    }
    let [created] = await db2.insert(specDrafts2).values({
      ownerUserId: this.userId,
      templateId: input.templateId,
      title: input.title,
      name: input.title,
      // backwards compatibility
      spec: input.payload,
      isDraft: input.isDraft ?? !0,
      status: input.status ?? "DRAFT",
      tags: []
    }).returning();
    return this.recordToSpecDraft(created);
  }
  async getDraft(draftId) {
    await setAppUser2(this.userId);
    let [record] = await db2.select().from(specDrafts2).where(
      and(
        eq2(specDrafts2.id, draftId),
        eq2(specDrafts2.ownerUserId, this.userId)
      )
    ).limit(1);
    return record ? this.recordToSpecDraft(record) : null;
  }
  async listDrafts(options = {}) {
    await setAppUser2(this.userId);
    let { limit = 50, offset = 0, status } = options, query = db2.select().from(specDrafts2).where(eq2(specDrafts2.ownerUserId, this.userId)).orderBy(desc2(specDrafts2.updatedAt)).limit(limit).offset(offset);
    return status && (query = query.where(
      and(
        eq2(specDrafts2.ownerUserId, this.userId),
        eq2(specDrafts2.status, status)
      )
    )), (await query).map((record) => this.recordToSpecDraft(record));
  }
  async deleteDraft(draftId) {
    return await setAppUser2(this.userId), (await db2.delete(specDrafts2).where(
      and(
        eq2(specDrafts2.id, draftId),
        eq2(specDrafts2.ownerUserId, this.userId)
      )
    )).rowCount > 0;
  }
  recordToSpecDraft(record) {
    return {
      id: record.id,
      title: record.title,
      isDraft: record.isDraft ?? !0,
      status: record.status ?? "DRAFT",
      payload: record.spec || {},
      createdAt: record.createdAt?.toISOString() ?? (/* @__PURE__ */ new Date()).toISOString(),
      updatedAt: record.updatedAt?.toISOString() ?? (/* @__PURE__ */ new Date()).toISOString()
    };
  }
};
function createSpecDraftService(userId) {
  return new SpecDraftService(userId);
}

// app/components/TemplatePicker.tsx
import { templates } from "@metaagent/templates";
import { jsx as jsx3, jsxs as jsxs2 } from "react/jsx-runtime";
function TemplatePicker({ onSelect }) {
  return /* @__PURE__ */ jsxs2("div", { className: "template-picker", children: [
    /* @__PURE__ */ jsx3("h3", { children: "Select a template" }),
    /* @__PURE__ */ jsx3("div", { className: "template-grid", children: templates.map((t) => /* @__PURE__ */ jsxs2("button", { className: "template-card", onClick: () => onSelect(t.id), children: [
      /* @__PURE__ */ jsx3("div", { className: "template-name", children: t.name }),
      /* @__PURE__ */ jsx3("div", { className: "template-desc", children: t.description }),
      t.tags && /* @__PURE__ */ jsx3("div", { className: "template-tags", children: t.tags.map((tag) => /* @__PURE__ */ jsx3("span", { className: "tag", children: tag }, tag)) })
    ] }, t.id)) })
  ] });
}
var TemplatePicker_default = TemplatePicker;

// app/components/InterviewPanel.tsx
import { useEffect, useMemo, useState } from "react";
import { InterviewRunner } from "@metaagent/interview";

// app/utils/schema.ts
import { zodToJsonSchema } from "zod-to-json-schema";
import { AgentSpecSchema as AgentSpecSchema2 } from "@metaagent/spec";
function generateJsonSchema() {
  return zodToJsonSchema(AgentSpecSchema2, {
    name: "AgentSpec",
    $refStrategy: "none"
    // Inline all refs for Monaco
  });
}
var AGENT_SPEC_JSON_SCHEMA = generateJsonSchema();
function debounce(fn, wait = 300) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout), timeout = setTimeout(() => fn(...args), wait);
  };
}

// app/components/InterviewPanel.tsx
import { jsx as jsx4, jsxs as jsxs3 } from "react/jsx-runtime";
function InterviewPanel({ script, initialState, onStateChange, onAutosave }) {
  let runner = useMemo(() => new InterviewRunner(script), [script]), [state, setState] = useState(initialState), [autosave] = useState(() => debounce((s) => onAutosave?.(s), 800));
  useEffect(() => {
    onStateChange?.(state), autosave(state);
  }, [state]);
  let currentNode = runner.getCurrentNode(state), handleAnswer = (answer) => {
    let { updatedState } = runner.runNode(state, answer);
    setState(updatedState);
  }, renderQuestion = () => {
    switch (currentNode.inputType) {
      case "text":
        return /* @__PURE__ */ jsx4(
          "input",
          {
            type: "text",
            defaultValue: state.answers[currentNode.id] || "",
            onBlur: (e) => handleAnswer(e.target.value)
          }
        );
      case "textarea":
        return /* @__PURE__ */ jsx4(
          "textarea",
          {
            defaultValue: state.answers[currentNode.id] || "",
            onBlur: (e) => handleAnswer(e.target.value)
          }
        );
      case "number":
        return /* @__PURE__ */ jsx4(
          "input",
          {
            type: "number",
            defaultValue: state.answers[currentNode.id] || "",
            onBlur: (e) => handleAnswer(Number(e.target.value))
          }
        );
      case "select":
        return /* @__PURE__ */ jsxs3(
          "select",
          {
            defaultValue: state.answers[currentNode.id] || "",
            onChange: (e) => handleAnswer(e.target.value),
            children: [
              /* @__PURE__ */ jsx4("option", { value: "", disabled: !0, children: "Select..." }),
              currentNode.options?.map((opt) => /* @__PURE__ */ jsx4("option", { value: opt, children: opt }, opt))
            ]
          }
        );
      default:
        return null;
    }
  };
  return currentNode.type === "end" ? /* @__PURE__ */ jsx4("div", { className: "interview-complete", children: "Interview complete." }) : /* @__PURE__ */ jsx4("div", { className: "interview-panel", children: /* @__PURE__ */ jsxs3("div", { className: "question", children: [
    /* @__PURE__ */ jsx4("label", { children: currentNode.prompt }),
    /* @__PURE__ */ jsx4("div", { className: "control", children: renderQuestion() })
  ] }) });
}

// app/routes/builder.$draftId.tsx
import { templates as templates2 } from "@metaagent/templates";
import { genericAgentInterview } from "@metaagent/interview";
import { createDraftSpec } from "@metaagent/spec";
import { jsx as jsx5, jsxs as jsxs4 } from "react/jsx-runtime";
function getUserId2() {
  return "01ARZ3NDEKTSV4RRFFQ69G5FAV";
}
async function loader3({ params, request }) {
  let userId = getUserId2(), service = createSpecDraftService(userId), url = new URL(request.url), draftId = params.draftId, draft = draftId ? await service.getDraft(draftId) : null;
  return draft || (draft = createDraftSpec({ title: "Untitled Agent" })), json3({ draft });
}
async function action2({ params, request }) {
  let userId = getUserId2(), service = createSpecDraftService(userId), body = await request.json(), saved = await service.saveDraft(body);
  return json3(saved);
}
function BuilderRoute() {
  let { draft } = useLoaderData2(), [searchParams, setSearchParams] = useSearchParams(), navigate = useNavigate(), templateId = searchParams.get("template"), handleTemplateSelect = async (id) => {
    let template = templates2.find((t) => t.id === id);
    if (!template)
      return;
    (await fetch("/builder/" + draft.id, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: draft.id,
        title: draft.title,
        templateId: template.id,
        payload: template.defaultSpec.payload,
        isDraft: !0,
        status: "DRAFT"
      })
    })).ok && setSearchParams((prev) => (prev.set("template", template.id), prev));
  }, script = templateId ? templates2.find((t) => t.id === templateId)?.interview || genericAgentInterview : genericAgentInterview, initialState = {
    answers: {},
    currentNodeId: script.startNodeId || "agent-name",
    specDraft: draft,
    visitedNodes: []
  };
  return /* @__PURE__ */ jsxs4("div", { className: "builder-layout", children: [
    /* @__PURE__ */ jsx5("div", { className: "builder-top", children: !templateId && /* @__PURE__ */ jsx5(TemplatePicker_default, { onSelect: handleTemplateSelect }) }),
    /* @__PURE__ */ jsxs4("div", { className: "builder-content", children: [
      /* @__PURE__ */ jsx5("div", { className: "builder-left", children: /* @__PURE__ */ jsx5(InterviewPanel, { script, initialState, onAutosave: async (state) => {
        await fetch("/builder/" + draft.id, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            id: draft.id,
            title: draft.title,
            templateId: templateId ?? void 0,
            payload: state.specDraft.payload,
            isDraft: !0,
            status: "DRAFT"
          })
        });
      } }) }),
      /* @__PURE__ */ jsx5("div", { className: "builder-right", children: /* @__PURE__ */ jsx5("pre", { style: { maxHeight: 500, overflow: "auto", background: "#0b0b0e", color: "#ddd", padding: 12 }, children: JSON.stringify(initialState.specDraft.payload, null, 2) }) })
    ] })
  ] });
}

// app/routes/catalog.drafts.tsx
var catalog_drafts_exports = {};
__export(catalog_drafts_exports, {
  default: () => DraftsCatalogRoute,
  loader: () => loader4
});
import { json as json4 } from "@remix-run/node";
import { useLoaderData as useLoaderData3, Link as Link2 } from "@remix-run/react";
import { jsx as jsx6, jsxs as jsxs5 } from "react/jsx-runtime";
async function loader4({ request }) {
  let response = await fetch(`${request.url.replace(/\/catalog\/drafts.*/, "")}/api/specs/drafts`);
  if (!response.ok)
    throw new Response("Failed to load drafts", { status: response.status });
  let drafts = await response.json();
  return json4({ drafts });
}
function DraftsCatalogRoute() {
  let { drafts } = useLoaderData3(), formatDate = (dateString) => new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
  return /* @__PURE__ */ jsxs5("div", { className: "drafts-catalog", children: [
    /* @__PURE__ */ jsxs5("header", { className: "catalog-header", children: [
      /* @__PURE__ */ jsx6("h1", { children: "My Drafts" }),
      /* @__PURE__ */ jsxs5("div", { className: "catalog-actions", children: [
        /* @__PURE__ */ jsx6(Link2, { to: "/specs/new", className: "new-draft-button", children: "+ New Draft" }),
        /* @__PURE__ */ jsxs5("div", { className: "template-buttons", children: [
          /* @__PURE__ */ jsx6(Link2, { to: "/specs/new?template=chatbot", className: "template-button", children: "Chatbot" }),
          /* @__PURE__ */ jsx6(Link2, { to: "/specs/new?template=web-automation", className: "template-button", children: "Web Automation" }),
          /* @__PURE__ */ jsx6(Link2, { to: "/specs/new?template=api-copilot", className: "template-button", children: "API Copilot" })
        ] })
      ] })
    ] }),
    drafts.length === 0 ? /* @__PURE__ */ jsxs5("div", { className: "empty-state", children: [
      /* @__PURE__ */ jsx6("div", { className: "empty-icon", children: "\u{1F4DD}" }),
      /* @__PURE__ */ jsx6("h2", { children: "No drafts yet" }),
      /* @__PURE__ */ jsx6("p", { children: "Create your first agent spec to get started." }),
      /* @__PURE__ */ jsx6(Link2, { to: "/specs/new", className: "cta-button", children: "Create First Draft" })
    ] }) : /* @__PURE__ */ jsx6("div", { className: "drafts-grid", children: drafts.map((draft) => /* @__PURE__ */ jsxs5("div", { className: "draft-card", children: [
      /* @__PURE__ */ jsxs5("div", { className: "draft-header", children: [
        /* @__PURE__ */ jsx6("h3", { className: "draft-name", children: /* @__PURE__ */ jsx6(Link2, { to: `/specs/${draft.id}`, children: draft.name }) }),
        /* @__PURE__ */ jsx6("div", { className: "draft-actions", children: /* @__PURE__ */ jsx6(Link2, { to: `/specs/${draft.id}`, className: "edit-link", children: "Edit" }) })
      ] }),
      /* @__PURE__ */ jsxs5("div", { className: "draft-meta", children: [
        /* @__PURE__ */ jsxs5("div", { className: "draft-dates", children: [
          /* @__PURE__ */ jsxs5("span", { className: "created", children: [
            "Created: ",
            formatDate(draft.createdAt)
          ] }),
          /* @__PURE__ */ jsxs5("span", { className: "updated", children: [
            "Updated: ",
            formatDate(draft.updatedAt)
          ] })
        ] }),
        draft.tags && draft.tags.length > 0 && /* @__PURE__ */ jsx6("div", { className: "draft-tags", children: draft.tags.map((tag) => /* @__PURE__ */ jsx6("span", { className: "tag", children: tag }, tag)) })
      ] }),
      draft.spec && /* @__PURE__ */ jsxs5("div", { className: "draft-preview", children: [
        draft.spec.meta?.description && /* @__PURE__ */ jsx6("p", { className: "draft-description", children: draft.spec.meta.description }),
        /* @__PURE__ */ jsxs5("div", { className: "spec-info", children: [
          draft.spec.model && /* @__PURE__ */ jsxs5("span", { className: "model-info", children: [
            draft.spec.model.provider,
            "/",
            draft.spec.model.model
          ] }),
          draft.spec.variables && /* @__PURE__ */ jsxs5("span", { className: "variables-count", children: [
            draft.spec.variables.length,
            " variables"
          ] }),
          draft.spec.tools && draft.spec.tools.length > 0 && /* @__PURE__ */ jsxs5("span", { className: "tools-count", children: [
            draft.spec.tools.length,
            " tools"
          ] })
        ] })
      ] })
    ] }, draft.id)) })
  ] });
}

// app/routes/auth.logout.ts
var auth_logout_exports = {};
__export(auth_logout_exports, {
  action: () => action3
});
async function action3({ request }) {
  return logout(request);
}

// app/routes/api.agents.ts
var api_agents_exports = {};
__export(api_agents_exports, {
  loader: () => loader5
});
import { json as json5 } from "@remix-run/node";
import { pool } from "@metaagent/db";
var DEV_USER_ID = "00000000-0000-0000-0000-000000000001";
async function loader5({ request }) {
  await pool.query("select set_config('app.current_user_id', $1, false)", [DEV_USER_ID]);
  let result = await pool.query("select id, name, slug, owner_user_id from agents order by created_at desc limit 10");
  return json5({ agents: result.rows });
}

// app/routes/auth.login.tsx
var auth_login_exports = {};
__export(auth_login_exports, {
  action: () => action4,
  default: () => Login,
  loader: () => loader6
});
import { json as json6, redirect as redirect2 } from "@remix-run/node";
import { Form } from "@remix-run/react";
import { jsx as jsx7, jsxs as jsxs6 } from "react/jsx-runtime";
async function loader6({ request }) {
  return await getUserId(request) ? redirect2("/") : json6({});
}
async function action4({ request }) {
  let form = await request.formData(), username = String(form.get("username"));
  return username ? createUserSession(username, "/") : json6({ error: "username required" }, { status: 400 });
}
function Login() {
  return /* @__PURE__ */ jsxs6(Form, { method: "post", style: { padding: 32 }, children: [
    /* @__PURE__ */ jsxs6("label", { children: [
      "Dev Username",
      /* @__PURE__ */ jsx7("input", { name: "username", style: { border: "1px solid #ccc", marginLeft: 8 } })
    ] }),
    /* @__PURE__ */ jsx7("button", { type: "submit", style: { marginLeft: 8 }, children: "Login" })
  ] });
}

// app/routes/api.hello.ts
var api_hello_exports = {};
__export(api_hello_exports, {
  loader: () => loader7
});
import { json as json7 } from "@remix-run/node";
var loader7 = () => json7({ ok: !0, at: (/* @__PURE__ */ new Date()).toISOString() });

// app/routes/specs.$id.tsx
var specs_id_exports = {};
__export(specs_id_exports, {
  action: () => action5,
  default: () => EditSpecRoute,
  loader: () => loader8
});
import { useState as useState3, useEffect as useEffect3, useRef as useRef2 } from "react";
import { json as json8, redirect as redirect3 } from "@remix-run/node";
import { useLoaderData as useLoaderData4, useSubmit, useNavigation } from "@remix-run/react";

// app/components/SpecEditor.tsx
import { useEffect as useEffect2, useRef, useState as useState2, useCallback } from "react";
import Editor from "@monaco-editor/react";
import { parseTree, findNodeAtLocation } from "jsonc-parser";
import * as yaml from "js-yaml";
import * as prettier from "prettier";
import { jsx as jsx8, jsxs as jsxs7 } from "react/jsx-runtime";
function SpecEditor({
  value,
  onChange,
  onValidationChange,
  readOnly = !1
}) {
  let editorRef = useRef(null), workerRef = useRef(null), validationTimeoutRef = useRef(), [isYaml, setIsYaml] = useState2(!1);
  useEffect2(() => {
    let workerCode = `
import { AgentSpecSchema } from "@metaagent/spec";

self.addEventListener('message', (event) => {
  const { id, content } = event.data;
  
  try {
    let parsed;
    try {
      parsed = JSON.parse(content);
    } catch (parseError) {
      const result = {
        id,
        isValid: false,
        errors: [{
          path: [],
          message: "Invalid JSON syntax",
          code: "invalid_json"
        }]
      };
      self.postMessage(result);
      return;
    }

    const validation = AgentSpecSchema.safeParse(parsed);
    
    if (validation.success) {
      const result = {
        id,
        isValid: true
      };
      self.postMessage(result);
    } else {
      const result = {
        id,
        isValid: false,
        errors: validation.error.issues.map(issue => ({
          path: issue.path,
          message: issue.message,
          code: issue.code
        }))
      };
      self.postMessage(result);
    }
  } catch (error) {
    const result = {
      id,
      isValid: false,
      errors: [{
        path: [],
        message: error instanceof Error ? error.message : "Unknown validation error",
        code: "validation_error"
      }]
    };
    self.postMessage(result);
  }
});
    `, blob = new Blob([workerCode], { type: "application/javascript" });
    return workerRef.current = new Worker(URL.createObjectURL(blob)), workerRef.current.onmessage = (event) => {
      let result = event.data;
      updateValidationMarkers(result), onValidationChange?.(result.errors);
    }, () => {
      workerRef.current && workerRef.current.terminate(), validationTimeoutRef.current && clearTimeout(validationTimeoutRef.current);
    };
  }, [onValidationChange]);
  let validateContent = useCallback((content) => {
    validationTimeoutRef.current && clearTimeout(validationTimeoutRef.current), validationTimeoutRef.current = setTimeout(() => {
      if (workerRef.current && content.trim()) {
        let jsonContent = content;
        if (isYaml)
          try {
            let parsed = yaml.load(content);
            jsonContent = JSON.stringify(parsed, null, 2);
          } catch {
            let result = {
              id: "yaml-parse",
              isValid: !1,
              errors: [{
                path: [],
                message: "Invalid YAML syntax",
                code: "invalid_yaml"
              }]
            };
            updateValidationMarkers(result), onValidationChange?.(result.errors);
            return;
          }
        workerRef.current.postMessage({
          id: Date.now().toString(),
          content: jsonContent
        });
      }
    }, 300);
  }, [isYaml, onValidationChange]), updateValidationMarkers = useCallback((result) => {
    if (!editorRef.current)
      return;
    let model = editorRef.current.getModel();
    if (!model)
      return;
    if (result.isValid || !result.errors) {
      window.monaco.editor.setModelMarkers(model, "validation", []);
      return;
    }
    let markers = result.errors.map((error) => {
      let startLineNumber = 1, startColumn = 1, endLineNumber = 1, endColumn = 1;
      if (error.path.length > 0 && !isYaml)
        try {
          let tree = parseTree(model.getValue()), node = findNodeAtLocation(tree, error.path);
          if (node) {
            let startPos = model.getPositionAt(node.offset), endPos = model.getPositionAt(node.offset + node.length);
            startLineNumber = startPos.lineNumber, startColumn = startPos.column, endLineNumber = endPos.lineNumber, endColumn = endPos.column;
          }
        } catch {
        }
      return {
        startLineNumber,
        startColumn,
        endLineNumber,
        endColumn,
        message: error.message,
        severity: window.monaco.MarkerSeverity.Error,
        source: "validation"
      };
    });
    window.monaco.editor.setModelMarkers(model, "validation", markers);
  }, [isYaml]), handleEditorDidMount = useCallback((editor) => {
    editorRef.current = editor;
    let uri = editor.getModel()?.uri.toString();
    if (uri && !isYaml && window.monaco && window.monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
      validate: !0,
      schemas: [{
        uri: "http://metaagent.com/agent-spec.json",
        fileMatch: [uri],
        schema: AGENT_SPEC_JSON_SCHEMA
      }]
    }), window.monaco) {
      let monaco = window.monaco;
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
        let saveEvent = new CustomEvent("editor-save");
        window.dispatchEvent(saveEvent);
      }), editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyF, () => {
        formatContent();
      });
    }
    validateContent(value);
  }, [isYaml, value, validateContent]), handleEditorChange = useCallback((newValue) => {
    let content = newValue || "";
    onChange(content), validateContent(content);
  }, [onChange, validateContent]), formatContent = useCallback(async () => {
    if (!editorRef.current)
      return;
    let content = editorRef.current.getValue();
    try {
      let formatted;
      if (isYaml) {
        let parsed = yaml.load(content);
        formatted = yaml.dump(parsed, { indent: 2 });
      } else
        formatted = await prettier.format(content, {
          parser: "json",
          tabWidth: 2,
          semi: !1
        });
      editorRef.current.setValue(formatted);
    } catch (formatError) {
      console.warn("Failed to format content:", formatError);
    }
  }, [isYaml]), toggleFormat = useCallback(() => {
    if (!editorRef.current)
      return;
    let content = editorRef.current.getValue().trim();
    if (!content) {
      setIsYaml(!isYaml);
      return;
    }
    try {
      let converted;
      if (isYaml) {
        let parsed = yaml.load(content);
        converted = JSON.stringify(parsed, null, 2);
      } else {
        let parsed = JSON.parse(content);
        converted = yaml.dump(parsed, { indent: 2 });
      }
      setIsYaml(!isYaml), editorRef.current.setValue(converted);
    } catch (conversionError) {
      console.warn("Failed to convert format:", conversionError);
    }
  }, [isYaml]);
  return /* @__PURE__ */ jsxs7("div", { className: "spec-editor", children: [
    /* @__PURE__ */ jsxs7("div", { className: "editor-toolbar", children: [
      /* @__PURE__ */ jsx8(
        "button",
        {
          onClick: toggleFormat,
          className: "format-toggle",
          title: `Switch to ${isYaml ? "JSON" : "YAML"}`,
          children: isYaml ? "JSON" : "YAML"
        }
      ),
      /* @__PURE__ */ jsx8(
        "button",
        {
          onClick: formatContent,
          className: "format-button",
          title: "Format (Ctrl/Cmd+Shift+F)",
          children: "Format"
        }
      )
    ] }),
    /* @__PURE__ */ jsx8(
      Editor,
      {
        height: "500px",
        language: isYaml ? "yaml" : "json",
        value,
        onChange: handleEditorChange,
        onMount: handleEditorDidMount,
        options: {
          readOnly,
          minimap: { enabled: !1 },
          lineNumbers: "on",
          folding: !0,
          wordWrap: "on",
          tabSize: 2,
          insertSpaces: !0,
          automaticLayout: !0,
          scrollBeyondLastLine: !1,
          theme: "vs-dark"
        }
      }
    )
  ] });
}

// app/components/ValidationPanel.tsx
import { jsx as jsx9, jsxs as jsxs8 } from "react/jsx-runtime";
function ValidationPanel({ errors, onErrorClick }) {
  return !errors || errors.length === 0 ? /* @__PURE__ */ jsxs8("div", { className: "validation-panel validation-panel--success", children: [
    /* @__PURE__ */ jsxs8("div", { className: "validation-header", children: [
      /* @__PURE__ */ jsx9("span", { className: "validation-icon", children: "\u2705" }),
      /* @__PURE__ */ jsx9("h3", { children: "Validation Passed" })
    ] }),
    /* @__PURE__ */ jsx9("p", { children: "Your spec is valid and ready to save." })
  ] }) : /* @__PURE__ */ jsxs8("div", { className: "validation-panel validation-panel--errors", children: [
    /* @__PURE__ */ jsxs8("div", { className: "validation-header", children: [
      /* @__PURE__ */ jsx9("span", { className: "validation-icon", children: "\u274C" }),
      /* @__PURE__ */ jsxs8("h3", { children: [
        "Validation Errors (",
        errors.length,
        ")"
      ] })
    ] }),
    /* @__PURE__ */ jsx9("div", { className: "validation-errors", children: errors.map((error, index) => /* @__PURE__ */ jsxs8(
      "div",
      {
        className: "validation-error",
        onClick: () => onErrorClick?.(error),
        role: "button",
        tabIndex: 0,
        onKeyDown: (e) => {
          (e.key === "Enter" || e.key === " ") && onErrorClick?.(error);
        },
        children: [
          /* @__PURE__ */ jsx9("div", { className: "error-path", children: error.path.length > 0 ? error.path.join(".") : "Root" }),
          /* @__PURE__ */ jsx9("div", { className: "error-message", children: error.message }),
          /* @__PURE__ */ jsx9("div", { className: "error-code", children: error.code })
        ]
      },
      index
    )) })
  ] });
}

// app/routes/specs.$id.tsx
import { jsx as jsx10, jsxs as jsxs9 } from "react/jsx-runtime";
async function loader8({ params, request }) {
  let { id } = params;
  if (!id)
    throw new Response("Draft ID required", { status: 400 });
  let response = await fetch(`${request.url.replace(/\/specs\/.*/, "")}/api/specs/drafts?id=${id}`);
  if (!response.ok)
    throw response.status === 404 ? new Response("Draft not found", { status: 404 }) : new Response("Failed to load draft", { status: response.status });
  let draft = await response.json();
  return json8({ draft });
}
async function action5({ params, request }) {
  let { id } = params, formData = await request.formData(), intent = formData.get("intent");
  if (intent === "save") {
    let name = formData.get("name"), spec = JSON.parse(formData.get("spec")), tags = JSON.parse(formData.get("tags") || "[]"), response = await fetch(`${request.url.replace(/\/specs\/.*/, "")}/api/specs/drafts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, name, spec, tags })
    });
    if (response.ok) {
      let draft = await response.json();
      return json8({ draft, success: "Draft saved successfully" });
    } else {
      let error = await response.json();
      return json8({ error: error.error }, { status: response.status });
    }
  }
  if (intent === "delete") {
    let response = await fetch(`${request.url.replace(/\/specs\/.*/, "")}/api/specs/drafts?id=${id}`, {
      method: "DELETE"
    });
    if (response.ok)
      return redirect3("/catalog/drafts");
    {
      let error = await response.json();
      return json8({ error: error.error }, { status: response.status });
    }
  }
  return json8({ error: "Invalid intent" }, { status: 400 });
}
function EditSpecRoute() {
  let { draft } = useLoaderData4(), submit = useSubmit(), navigation = useNavigation(), [spec, setSpec] = useState3(
    () => JSON.stringify(draft.spec, null, 2)
  ), [validationErrors, setValidationErrors] = useState3(), [metadata, setMetadata] = useState3({
    name: draft.name,
    tags: draft.tags || []
  }), [isDirty, setIsDirty] = useState3(!1), [isImporting, setIsImporting] = useState3(!1), fileInputRef = useRef2(null);
  useEffect3(() => {
    let handleSave = (e) => {
      e.preventDefault(), handleSaveSpec();
    };
    return window.addEventListener("editor-save", handleSave), () => window.removeEventListener("editor-save", handleSave);
  }, [spec, metadata, validationErrors]);
  let handleSpecChange = (newSpec) => {
    setSpec(newSpec), setIsDirty(!0);
  }, handleValidationChange = (errors) => {
    setValidationErrors(errors);
  }, handleSaveSpec = () => {
    if (validationErrors && validationErrors.length > 0) {
      alert("Cannot save spec with validation errors. Please fix them first.");
      return;
    }
    let formData = new FormData();
    formData.append("intent", "save"), formData.append("name", metadata.name), formData.append("spec", spec), formData.append("tags", JSON.stringify(metadata.tags)), submit(formData, { method: "post" });
  }, handleDeleteDraft = () => {
    if (confirm("Are you sure you want to delete this draft? This action cannot be undone.")) {
      let formData = new FormData();
      formData.append("intent", "delete"), submit(formData, { method: "post" });
    }
  }, handleImport = () => {
    fileInputRef.current?.click();
  }, handleFileImport = (event) => {
    let file = event.target.files?.[0];
    if (!file)
      return;
    if (file.size > 200 * 1024) {
      alert("File too large (>200KB)");
      return;
    }
    setIsImporting(!0);
    let reader = new FileReader();
    reader.onload = (e) => {
      try {
        let content = e.target?.result;
        setSpec(content), setIsDirty(!0);
        try {
          let parsed = JSON.parse(content);
          parsed.meta?.name && setMetadata((prev) => ({ ...prev, name: parsed.meta.name }));
        } catch {
        }
      } catch {
        alert("Failed to read file");
      } finally {
        setIsImporting(!1);
      }
    }, reader.readAsText(file);
  }, handleExport = () => {
    let blob = new Blob([spec], { type: "application/json" }), url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url, a.download = `${metadata.name}.json`, document.body.appendChild(a), a.click(), document.body.removeChild(a), URL.revokeObjectURL(url);
  }, isValid = !validationErrors || validationErrors.length === 0, isSaving = navigation.state === "submitting";
  return /* @__PURE__ */ jsxs9("div", { className: "spec-editor-page", children: [
    /* @__PURE__ */ jsxs9("header", { className: "spec-editor-header", children: [
      /* @__PURE__ */ jsxs9("div", { className: "spec-meta", children: [
        /* @__PURE__ */ jsx10(
          "input",
          {
            type: "text",
            value: metadata.name,
            onChange: (e) => {
              setMetadata((prev) => ({ ...prev, name: e.target.value })), setIsDirty(!0);
            },
            className: "spec-name-input",
            placeholder: "Spec name"
          }
        ),
        /* @__PURE__ */ jsxs9("span", { className: "draft-id", children: [
          "ID: ",
          draft.id
        ] }),
        isDirty && /* @__PURE__ */ jsx10("span", { className: "dirty-indicator", children: "\u25CF" })
      ] }),
      /* @__PURE__ */ jsxs9("div", { className: "spec-actions", children: [
        /* @__PURE__ */ jsx10("button", { onClick: handleImport, disabled: isImporting, children: isImporting ? "Importing..." : "Import" }),
        /* @__PURE__ */ jsx10("button", { onClick: handleExport, children: "Export" }),
        /* @__PURE__ */ jsx10(
          "button",
          {
            onClick: handleDeleteDraft,
            className: "delete-button",
            disabled: isSaving,
            children: "Delete"
          }
        ),
        /* @__PURE__ */ jsx10(
          "button",
          {
            onClick: handleSaveSpec,
            disabled: !isValid || isSaving,
            className: isValid ? "save-button-valid" : "save-button-invalid",
            children: isSaving ? "Saving..." : "Save Draft"
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxs9("div", { className: "spec-editor-content", children: [
      /* @__PURE__ */ jsx10("div", { className: "spec-editor-main", children: /* @__PURE__ */ jsx10(
        SpecEditor,
        {
          value: spec,
          onChange: handleSpecChange,
          onValidationChange: handleValidationChange
        }
      ) }),
      /* @__PURE__ */ jsx10("div", { className: "spec-editor-sidebar", children: /* @__PURE__ */ jsx10(
        ValidationPanel,
        {
          errors: validationErrors,
          onErrorClick: (error) => {
            console.log("Focus error:", error);
          }
        }
      ) })
    ] }),
    /* @__PURE__ */ jsx10(
      "input",
      {
        ref: fileInputRef,
        type: "file",
        accept: ".json,.yaml,.yml",
        style: { display: "none" },
        onChange: handleFileImport
      }
    )
  ] });
}

// app/routes/specs.new.tsx
var specs_new_exports = {};
__export(specs_new_exports, {
  action: () => action6,
  default: () => NewSpecRoute,
  loader: () => loader9
});
import { useState as useState4, useEffect as useEffect4, useRef as useRef3 } from "react";
import { json as json9, redirect as redirect4 } from "@remix-run/node";
import { useLoaderData as useLoaderData5, useSubmit as useSubmit2, useNavigation as useNavigation2 } from "@remix-run/react";
import { jsx as jsx11, jsxs as jsxs10 } from "react/jsx-runtime";
var TEMPLATES = {
  chatbot: {
    specVersion: "0.1.0",
    meta: {
      id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      name: "chatbot-agent",
      description: "A conversational chatbot agent",
      version: "0.0.1",
      createdAt: (/* @__PURE__ */ new Date()).toISOString(),
      updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
      tags: ["chatbot", "conversation"]
    },
    variables: [
      { key: "topic", type: "string", required: !0 },
      { key: "tone", type: "enum", enumValues: ["friendly", "professional", "casual"], required: !1 }
    ],
    prompt: {
      template: "You are a helpful chatbot. Discuss {{topic}} in a {{tone}} tone."
    },
    model: {
      provider: "openai",
      model: "gpt-4o-mini",
      maxTokens: 1024,
      temperature: 0.7
    },
    tools: [],
    limits: {
      timeoutSec: 60,
      budgetUsd: 1
    }
  },
  "web-automation": {
    specVersion: "0.1.0",
    meta: {
      id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      name: "web-automation-agent",
      description: "Agent for automating web tasks",
      version: "0.0.1",
      createdAt: (/* @__PURE__ */ new Date()).toISOString(),
      updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
      tags: ["automation", "web"]
    },
    variables: [
      { key: "target_url", type: "string", required: !0 },
      { key: "action", type: "enum", enumValues: ["scrape", "interact", "monitor"], required: !0 }
    ],
    prompt: {
      template: "Perform {{action}} on {{target_url}}. Be careful and precise."
    },
    model: {
      provider: "openai",
      model: "gpt-4o",
      maxTokens: 2048,
      temperature: 0.1
    },
    tools: [
      { kind: "http", allowDomains: ["https://*"] }
    ],
    limits: {
      timeoutSec: 120,
      budgetUsd: 2
    }
  },
  "api-copilot": {
    specVersion: "0.1.0",
    meta: {
      id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      name: "api-copilot-agent",
      description: "AI assistant for API development and testing",
      version: "0.0.1",
      createdAt: (/* @__PURE__ */ new Date()).toISOString(),
      updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
      tags: ["api", "development", "testing"]
    },
    variables: [
      { key: "api_spec", type: "string", required: !0 },
      { key: "task", type: "enum", enumValues: ["generate", "test", "document"], required: !0 }
    ],
    prompt: {
      template: "Help with {{task}} for the API: {{api_spec}}. Provide clear, actionable guidance."
    },
    model: {
      provider: "openai",
      model: "gpt-4o",
      maxTokens: 4096,
      temperature: 0.2
    },
    tools: [
      { kind: "http", allowDomains: ["https://api.example.com"] }
    ],
    limits: {
      timeoutSec: 180,
      budgetUsd: 3
    }
  }
};
async function loader9({ request }) {
  let template = new URL(request.url).searchParams.get("template");
  return json9({
    initialSpec: template && template in TEMPLATES ? TEMPLATES[template] : null,
    templateName: template
  });
}
async function action6({ request }) {
  let formData = await request.formData();
  if (formData.get("intent") === "save") {
    let name = formData.get("name"), spec = JSON.parse(formData.get("spec")), tags = JSON.parse(formData.get("tags") || "[]"), response = await fetch(`${request.url.replace(/\/specs\/new.*/, "")}/api/specs/drafts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, spec, tags })
    });
    if (response.ok) {
      let draft = await response.json();
      return redirect4(`/specs/${draft.id}`);
    } else {
      let error = await response.json();
      return json9({ error: error.error }, { status: response.status });
    }
  }
  return json9({ error: "Invalid intent" }, { status: 400 });
}
function NewSpecRoute() {
  let { initialSpec, templateName } = useLoaderData5(), submit = useSubmit2(), navigation = useNavigation2(), [spec, setSpec] = useState4(
    () => initialSpec ? JSON.stringify(initialSpec, null, 2) : "{}"
  ), [validationErrors, setValidationErrors] = useState4(), [metadata, setMetadata] = useState4({
    name: initialSpec?.meta?.name || "untitled-spec",
    tags: initialSpec?.meta?.tags || []
  }), [isDirty, setIsDirty] = useState4(!1), [isImporting, setIsImporting] = useState4(!1), fileInputRef = useRef3(null);
  useEffect4(() => {
    let handleSave = (e) => {
      e.preventDefault(), handleSaveSpec();
    };
    return window.addEventListener("editor-save", handleSave), () => window.removeEventListener("editor-save", handleSave);
  }, [spec, metadata, validationErrors]);
  let handleSpecChange = (newSpec) => {
    setSpec(newSpec), setIsDirty(!0);
  }, handleValidationChange = (errors) => {
    setValidationErrors(errors);
  }, handleSaveSpec = () => {
    if (validationErrors && validationErrors.length > 0) {
      alert("Cannot save spec with validation errors. Please fix them first.");
      return;
    }
    let formData = new FormData();
    formData.append("intent", "save"), formData.append("name", metadata.name), formData.append("spec", spec), formData.append("tags", JSON.stringify(metadata.tags)), submit(formData, { method: "post" });
  }, handleImport = () => {
    fileInputRef.current?.click();
  }, handleFileImport = (event) => {
    let file = event.target.files?.[0];
    if (!file)
      return;
    if (file.size > 200 * 1024) {
      alert("File too large (>200KB)");
      return;
    }
    setIsImporting(!0);
    let reader = new FileReader();
    reader.onload = (e) => {
      try {
        let content = e.target?.result;
        setSpec(content), setIsDirty(!0);
        try {
          let parsed = JSON.parse(content);
          parsed.meta?.name && setMetadata((prev) => ({ ...prev, name: parsed.meta.name }));
        } catch {
        }
      } catch {
        alert("Failed to read file");
      } finally {
        setIsImporting(!1);
      }
    }, reader.readAsText(file);
  }, handleExport = () => {
    let blob = new Blob([spec], { type: "application/json" }), url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url, a.download = `${metadata.name}.json`, document.body.appendChild(a), a.click(), document.body.removeChild(a), URL.revokeObjectURL(url);
  }, isValid = !validationErrors || validationErrors.length === 0, isSaving = navigation.state === "submitting";
  return /* @__PURE__ */ jsxs10("div", { className: "spec-editor-page", children: [
    /* @__PURE__ */ jsxs10("header", { className: "spec-editor-header", children: [
      /* @__PURE__ */ jsxs10("div", { className: "spec-meta", children: [
        /* @__PURE__ */ jsx11(
          "input",
          {
            type: "text",
            value: metadata.name,
            onChange: (e) => {
              setMetadata((prev) => ({ ...prev, name: e.target.value })), setIsDirty(!0);
            },
            className: "spec-name-input",
            placeholder: "Spec name"
          }
        ),
        templateName && /* @__PURE__ */ jsxs10("span", { className: "template-badge", children: [
          "Template: ",
          templateName
        ] }),
        isDirty && /* @__PURE__ */ jsx11("span", { className: "dirty-indicator", children: "\u25CF" })
      ] }),
      /* @__PURE__ */ jsxs10("div", { className: "spec-actions", children: [
        /* @__PURE__ */ jsx11("button", { onClick: handleImport, disabled: isImporting, children: isImporting ? "Importing..." : "Import" }),
        /* @__PURE__ */ jsx11("button", { onClick: handleExport, children: "Export" }),
        /* @__PURE__ */ jsx11(
          "button",
          {
            onClick: handleSaveSpec,
            disabled: !isValid || isSaving,
            className: isValid ? "save-button-valid" : "save-button-invalid",
            children: isSaving ? "Saving..." : "Save Draft"
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxs10("div", { className: "spec-editor-content", children: [
      /* @__PURE__ */ jsx11("div", { className: "spec-editor-main", children: /* @__PURE__ */ jsx11(
        SpecEditor,
        {
          value: spec,
          onChange: handleSpecChange,
          onValidationChange: handleValidationChange
        }
      ) }),
      /* @__PURE__ */ jsx11("div", { className: "spec-editor-sidebar", children: /* @__PURE__ */ jsx11(
        ValidationPanel,
        {
          errors: validationErrors,
          onErrorClick: (error) => {
            console.log("Focus error:", error);
          }
        }
      ) })
    ] }),
    /* @__PURE__ */ jsx11(
      "input",
      {
        ref: fileInputRef,
        type: "file",
        accept: ".json,.yaml,.yml",
        style: { display: "none" },
        onChange: handleFileImport
      }
    )
  ] });
}

// app/routes/healthz.ts
var healthz_exports = {};
__export(healthz_exports, {
  loader: () => loader10
});
import { json as json10 } from "@remix-run/node";
var loader10 = () => json10({ status: "ok" });

// app/routes/_index.tsx
var index_exports = {};
__export(index_exports, {
  default: () => Index,
  loader: () => loader11
});
import { json as json11 } from "@remix-run/node";
import { useLoaderData as useLoaderData6, Link as Link3 } from "@remix-run/react";
import { jsx as jsx12, jsxs as jsxs11 } from "react/jsx-runtime";
var loader11 = async () => json11({ message: "Hello MetaAgent" });
function Index() {
  let { message } = useLoaderData6();
  return /* @__PURE__ */ jsxs11("main", { style: { padding: 32 }, children: [
    /* @__PURE__ */ jsx12("h1", { style: { fontSize: "2rem", fontWeight: "bold" }, children: message }),
    /* @__PURE__ */ jsx12("nav", { style: { marginTop: 16 }, children: /* @__PURE__ */ jsx12(Link3, { to: "/api/hello", style: { textDecoration: "underline", color: "blue" }, children: "Raw JSON" }) })
  ] });
}

// app/routes/readyz.ts
var readyz_exports = {};
__export(readyz_exports, {
  loader: () => loader12
});
import { json as json12 } from "@remix-run/node";
var loader12 = () => json12({ status: "ready" });

// server-assets-manifest:@remix-run/dev/assets-manifest
var assets_manifest_default = { entry: { module: "/build/entry.client-3ULY3N7E.js", imports: ["/build/_shared/chunk-2C25HZ32.js", "/build/_shared/chunk-T36URGAI.js"] }, routes: { root: { id: "root", parentId: void 0, path: "", index: void 0, caseSensitive: void 0, module: "/build/root-ITQMF5CR.js", imports: ["/build/_shared/chunk-KPWQHS6G.js"], hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/_index": { id: "routes/_index", parentId: "root", path: void 0, index: !0, caseSensitive: void 0, module: "/build/routes/_index-YGL7KRWN.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/api.agents": { id: "routes/api.agents", parentId: "root", path: "api/agents", index: void 0, caseSensitive: void 0, module: "/build/routes/api.agents-UWKFOYUA.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/api.hello": { id: "routes/api.hello", parentId: "root", path: "api/hello", index: void 0, caseSensitive: void 0, module: "/build/routes/api.hello-C4RLELRS.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/api.specs.drafts": { id: "routes/api.specs.drafts", parentId: "root", path: "api/specs/drafts", index: void 0, caseSensitive: void 0, module: "/build/routes/api.specs.drafts-T44EM4YB.js", imports: void 0, hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/auth.login": { id: "routes/auth.login", parentId: "root", path: "auth/login", index: void 0, caseSensitive: void 0, module: "/build/routes/auth.login-YHU6M7LG.js", imports: void 0, hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/auth.logout": { id: "routes/auth.logout", parentId: "root", path: "auth/logout", index: void 0, caseSensitive: void 0, module: "/build/routes/auth.logout-S7F2WOON.js", imports: void 0, hasAction: !0, hasLoader: !1, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/builder.$draftId": { id: "routes/builder.$draftId", parentId: "root", path: "builder/:draftId", index: void 0, caseSensitive: void 0, module: "/build/routes/builder.$draftId-U4UZRZ24.js", imports: ["/build/_shared/chunk-RRANPFQE.js"], hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/catalog.drafts": { id: "routes/catalog.drafts", parentId: "root", path: "catalog/drafts", index: void 0, caseSensitive: void 0, module: "/build/routes/catalog.drafts-DD76Q7KK.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/healthz": { id: "routes/healthz", parentId: "root", path: "healthz", index: void 0, caseSensitive: void 0, module: "/build/routes/healthz-MBFLWMUV.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/readyz": { id: "routes/readyz", parentId: "root", path: "readyz", index: void 0, caseSensitive: void 0, module: "/build/routes/readyz-GKLWFVFH.js", imports: void 0, hasAction: !1, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/specs.$id": { id: "routes/specs.$id", parentId: "root", path: "specs/:id", index: void 0, caseSensitive: void 0, module: "/build/routes/specs.$id-S2IV53FD.js", imports: ["/build/_shared/chunk-PW2XMSTX.js", "/build/_shared/chunk-RRANPFQE.js"], hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 }, "routes/specs.new": { id: "routes/specs.new", parentId: "root", path: "specs/new", index: void 0, caseSensitive: void 0, module: "/build/routes/specs.new-OPCUUFXR.js", imports: ["/build/_shared/chunk-PW2XMSTX.js", "/build/_shared/chunk-RRANPFQE.js"], hasAction: !0, hasLoader: !0, hasClientAction: !1, hasClientLoader: !1, hasErrorBoundary: !1 } }, version: "928a8f71", hmr: void 0, url: "/build/manifest-928A8F71.js" };

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
  "routes/api.specs.drafts": {
    id: "routes/api.specs.drafts",
    parentId: "root",
    path: "api/specs/drafts",
    index: void 0,
    caseSensitive: void 0,
    module: api_specs_drafts_exports
  },
  "routes/builder.$draftId": {
    id: "routes/builder.$draftId",
    parentId: "root",
    path: "builder/:draftId",
    index: void 0,
    caseSensitive: void 0,
    module: builder_draftId_exports
  },
  "routes/catalog.drafts": {
    id: "routes/catalog.drafts",
    parentId: "root",
    path: "catalog/drafts",
    index: void 0,
    caseSensitive: void 0,
    module: catalog_drafts_exports
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
  "routes/specs.$id": {
    id: "routes/specs.$id",
    parentId: "root",
    path: "specs/:id",
    index: void 0,
    caseSensitive: void 0,
    module: specs_id_exports
  },
  "routes/specs.new": {
    id: "routes/specs.new",
    parentId: "root",
    path: "specs/new",
    index: void 0,
    caseSensitive: void 0,
    module: specs_new_exports
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
