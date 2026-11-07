// Minimal MCP Apps (SEP-1865, protocol 2026-01-26) view-side bridge.
//
// The official SDK (@modelcontextprotocol/ext-apps) bundles to ~650 KB because it
// pulls in the full MCP client + zod. These cards only need the handshake, tool
// input/result notifications, theming, auto-resize, open-link and message, which
// the spec documents as plain JSON-RPC over postMessage - so we implement that.

const PROTOCOL_VERSION = "2026-01-26";

export function createBridge({ name, version, onToolInput, onToolResult, onCancelled }) {
  const parent = window.parent;
  const embedded = parent && parent !== window;
  let nextId = 1;
  const pending = new Map();

  const post = (msg) => embedded && parent.postMessage({ jsonrpc: "2.0", ...msg }, "*");

  function request(method, params) {
    const id = nextId++;
    post({ id, method, params });
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (pending.delete(id)) reject(new Error(`${method} timed out`));
      }, 15000);
    });
  }

  const notify = (method, params) => post({ method, params });

  function handleHostRequest(msg) {
    // Host -> view requests we must answer
    if (msg.method === "ui/resource-teardown" || msg.method === "ping") {
      post({ id: msg.id, result: {} });
    } else {
      post({ id: msg.id, error: { code: -32601, message: `Method not found: ${msg.method}` } });
    }
  }

  window.addEventListener("message", (event) => {
    if (embedded && event.source !== parent) return;
    const msg = event.data;
    if (!msg || msg.jsonrpc !== "2.0") return;

    if (msg.id != null && !msg.method) {
      const p = pending.get(msg.id);
      if (!p) return;
      pending.delete(msg.id);
      msg.error ? p.reject(new Error(msg.error.message || "Request failed")) : p.resolve(msg.result);
      return;
    }
    if (msg.id != null && msg.method) return handleHostRequest(msg);

    switch (msg.method) {
      case "ui/notifications/tool-input":
        onToolInput && onToolInput(msg.params?.arguments || {});
        break;
      case "ui/notifications/tool-result":
        onToolResult && onToolResult(parseToolResult(msg.params));
        break;
      case "ui/notifications/tool-cancelled":
        onCancelled && onCancelled(msg.params);
        break;
      case "ui/notifications/host-context-changed":
        applyHostContext(msg.params);
        break;
    }
  });

  // --- Auto-resize: report our content height so the host sizes the iframe ---
  let lastHeight = 0;
  let resizeTimer = null;
  function reportSize() {
    const height = Math.ceil(document.documentElement.getBoundingClientRect().height);
    if (height && height !== lastHeight) {
      lastHeight = height;
      notify("ui/notifications/size-changed", { height });
    }
  }
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(() => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(reportSize, 30);
    }).observe(document.documentElement);
  }

  async function connect() {
    if (!embedded) return null;
    const result = await request("ui/initialize", {
      appInfo: { name, version },
      appCapabilities: {},
      protocolVersion: PROTOCOL_VERSION,
    });
    applyHostContext(result?.hostContext);
    notify("ui/notifications/initialized", {});
    reportSize();
    return result;
  }

  return {
    embedded,
    connect,
    openLink: (url) => request("ui/open-link", { url }).catch(() => window.open(url, "_blank", "noopener")),
    sendMessage: (text) =>
      request("ui/message", { role: "user", content: [{ type: "text", text }] }).catch(() => null),
  };
}

export function parseToolResult(params) {
  if (!params) return null;
  if (params.structuredContent) return params.structuredContent;
  const text = (params.content || []).find((c) => c.type === "text")?.text;
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function applyHostContext(ctx) {
  if (!ctx) return;
  const root = document.documentElement;
  if (ctx.theme === "light" || ctx.theme === "dark") {
    root.dataset.theme = ctx.theme;
    root.style.colorScheme = ctx.theme;
  }
  const vars = ctx.styles?.variables;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      if (k.startsWith("--") && typeof v === "string" && v) root.style.setProperty(k, v);
    }
  }
  const fonts = ctx.styles?.css?.fonts;
  if (fonts && !document.getElementById("host-fonts")) {
    const style = document.createElement("style");
    style.id = "host-fonts";
    style.textContent = fonts;
    document.head.appendChild(style);
  }
  if (ctx.safeAreaInsets) {
    const { top = 0, right = 0, bottom = 0, left = 0 } = ctx.safeAreaInsets;
    document.body.style.padding = `${top}px ${right}px ${bottom}px ${left}px`;
  }
}

// ---- tiny DOM helper (always uses textContent: tool data is never HTML) ----
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    el.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
  }
  return el;
}

export function safeUrl(url) {
  try {
    const u = new URL(url);
    return u.protocol === "https:" || u.protocol === "http:" ? u.href : null;
  } catch {
    return null;
  }
}

export const inr = (n) =>
  "₹" + Math.round(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
