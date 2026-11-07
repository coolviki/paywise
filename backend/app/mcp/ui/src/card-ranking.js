// View for the `recommend_card` tool: the user's cards ranked for a merchant.
import { createBridge, h, inr, safeUrl } from "./bridge.js";

const root = document.getElementById("root");
let args = {};
let rendered = false;

const SOURCE = {
  brand_ecosystem: (r) => `${r.matched_brand || "Brand"} benefit`,
  campaign: (r) => `Offer until ${fmtDate(r.valid_until)}`,
  base_rate: () => "Base rate",
};

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? iso : d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function header(data) {
  const amount = data?.amount_inr ?? args.amount_inr;
  const cat = data?.category_detected && data.category_detected !== "general" ? data.category_detected : null;
  return h(
    "div",
    { class: "head" },
    h(
      "div",
      {},
      h("p", { class: "title" }, `Best card for ${data?.merchant || args.merchant || "this purchase"}`),
      h("p", { class: "sub" }, [amount ? inr(amount) : null, cat].filter(Boolean).join(" · ") || "Your cards, ranked"),
    ),
    h("span", { class: "brand" }, "PayWise"),
  );
}

function row(r, i, bridge) {
  const top = i === 0;
  const src = (SOURCE[r.rate_source] || SOURCE.base_rate)(r);
  const terms = safeUrl(r.terms_url);
  return h(
    "div",
    { class: `row${top ? " top" : ""}` },
    h("span", { class: "rank" }, String(r.rank || i + 1)),
    h(
      "div",
      { style: "min-width:0" },
      h("div", { class: "cname" }, r.card_name),
      h(
        "div",
        { class: "cmeta" },
        [r.bank, src].filter(Boolean).join(" · "),
        terms && " · ",
        terms && h("a", { href: "#", style: "color:inherit", onclick: (e) => { e.preventDefault(); bridge.openLink(terms); } }, "T&C"),
      ),
    ),
    h(
      "div",
      { class: "rate" },
      h("div", { class: "pct" }, `${r.reward_rate_percent}%`),
      h("div", { class: "amt" }, r.estimated_reward_inr != null ? `${inr(r.estimated_reward_inr)} ${r.reward_type || ""}` : r.reward_type || ""),
    ),
  );
}

function render(data, bridge) {
  rendered = true;
  const ranking = data?.ranking || [];
  const children = [header(data)];
  if (!ranking.length) {
    children.push(h("div", { class: "state" }, data?.note || "No cards saved in PayWise yet."));
  } else {
    children.push(h("div", { class: "rows" }, ranking.slice(0, 6).map((r, i) => row(r, i, bridge))));
    const best = ranking[0];
    const second = ranking[1];
    const extra =
      second && best.estimated_reward_inr != null && second.estimated_reward_inr != null
        ? ` · ${inr(best.estimated_reward_inr - second.estimated_reward_inr)} more than ${second.card_name}`
        : "";
    children.push(
      h(
        "div",
        { class: "foot" },
        h("span", {}, "Use ", h("b", {}, best.card_name), extra),
        ranking.length > 6 && h("span", {}, `+${ranking.length - 6} more`),
      ),
    );
  }
  root.replaceChildren(h("div", { class: "card" }, children));
}

function renderLoading() {
  root.replaceChildren(
    h("div", { class: "card" }, header(null), h("div", { class: "state" }, h("div", { class: "spinner" }), "Ranking your cards…")),
  );
}

const bridge = createBridge({
  name: "PayWise card ranking",
  version: "1.0.0",
  onToolInput: (a) => {
    args = a || {};
    if (!rendered) renderLoading();
  },
  onToolResult: (data) => render(data, bridge),
});

renderLoading();
bridge.connect().catch(() => {});

window.__paywiseRender = (data, a) => {
  args = a || {};
  render(data, bridge);
};
