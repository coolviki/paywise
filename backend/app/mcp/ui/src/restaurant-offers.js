// View for the `get_restaurant_offers` tool: dine-out deals as cards.
import { createBridge, h, safeUrl } from "./bridge.js";

const PLATFORM = {
  swiggy_dineout: { name: "Swiggy Dineout", initial: "S" },
  eazydiner: { name: "EazyDiner", initial: "E" },
  district: { name: "District", initial: "D" },
};

const root = document.getElementById("root");
let args = {};
let rendered = false;

function platformOf(o) {
  const key = o.platform in PLATFORM ? o.platform : "other";
  const meta = PLATFORM[key] || { name: o.platform_display_name || "Offer", initial: "•" };
  return { key, name: o.platform_display_name || meta.name, initial: meta.initial };
}

function headline(o) {
  if (o.discount_percentage) return { text: `${Math.round(o.discount_percentage)}% off`, big: true };
  const m = /(₹\s?[\d,]+|\d+\s?%)\s*(off|cashback)?/i.exec(o.discount_text || "");
  if (m) return { text: `${m[1].replace(/\s/g, "")} ${m[2] ? m[2].toLowerCase() : "off"}`, big: true };
  return { text: o.discount_text || "Offer", big: false };
}

// An offer is usable if it needs no particular bank, or needs one the user holds.
const usable = (o) => !o.bank_name || o.matches_your_cards;
// Best first: usable offers by discount %, ties go to the user's own bank deal;
// offers needing a bank the user doesn't hold always sink to the bottom.
function score(o) {
  return (usable(o) ? 1000 : 0) + (o.discount_percentage || 0) + (o.matches_your_cards ? 0.5 : 0);
}
const shortBank = (b) => (b || "").replace(/\s+bank$/i, "");
const cap = (t) => (t ? t.charAt(0).toUpperCase() + t.slice(1) : t);

function header(data) {
  const searched = (data?.platforms_searched || [])
    .map((p) => PLATFORM[p]?.name || p)
    .join(" · ");
  return h(
    "div",
    { class: "head" },
    h(
      "div",
      {},
      h("p", { class: "title" }, data?.restaurant || args.restaurant || "Restaurant offers"),
      h("p", { class: "sub" }, [data?.city || args.city, searched && `Live from ${searched}`].filter(Boolean).join(" · ")),
    ),
    h("span", { class: "brand" }, "PayWise"),
  );
}

function renderLoading() {
  root.replaceChildren(
    h(
      "div",
      { class: "card" },
      header(null),
      h("div", { class: "state" }, h("div", { class: "spinner" }), "Checking Swiggy Dineout, EazyDiner and District…"),
      h("div", { class: "grid" }, h("div", { class: "skel" }), h("div", { class: "skel" }), h("div", { class: "skel" })),
    ),
  );
}

function tile(o, isBest, bridge) {
  const p = platformOf(o);
  const hl = headline(o);
  const link = safeUrl(o.platform_url) || safeUrl(o.source_url);
  const detail = cap([o.offer_type && o.offer_type.replace(/[_-]/g, " "), o.valid_days].filter(Boolean).join(" · "));
  const sub = hl.big && o.discount_text && o.discount_text !== hl.text ? o.discount_text : null;
  const limits = [
    o.max_discount && `up to ₹${Math.round(o.max_discount).toLocaleString("en-IN")}`,
    o.min_order && `min ₹${Math.round(o.min_order).toLocaleString("en-IN")}`,
  ].filter(Boolean).join(" · ");

  return h(
    "div",
    { class: `tile${isBest ? " best" : ""}` },
    h("div", { class: "plat" }, h("span", { class: `dot ${p.key}`, "aria-hidden": "true" }, p.initial), p.name),
    h("p", { class: `big${hl.big ? "" : " text"}` }, hl.text),
    sub && h("p", { class: "muted" }, sub),
    detail && h("p", { class: "muted" }, detail),
    limits && h("p", { class: "muted" }, limits),
    o.conditions && h("p", { class: "muted" }, o.conditions),
    o.matched_restaurant && h("p", { class: "muted" }, `📍 ${o.matched_restaurant}`),
    h(
      "div",
      { class: "chips" },
      o.bank_name &&
        (o.matches_your_cards
          ? h("span", { class: "chip mine" }, `✓ Your ${shortBank(o.bank_name)} card`)
          : h("span", { class: "chip" }, `Needs ${shortBank(o.bank_name)} card`)),
      !o.bank_name && h("span", { class: "chip" }, "Any card"),
      o.coupon_code && h("span", { class: "code" }, o.coupon_code),
    ),
    link && h("button", { class: "linkbtn", onclick: () => bridge.openLink(link) }, "Open ↗"),
  );
}

function render(data, bridge) {
  rendered = true;
  if (!data) {
    root.replaceChildren(h("div", { class: "card" }, header(null), h("div", { class: "state" }, "No result to show.")));
    return;
  }
  const offers = [...(data.offers || [])].sort((a, b) => score(b) - score(a));
  const best = offers[0];
  const pay = data.pay_with;

  const children = [header(data)];

  // Apps that returned nothing are shown, never silently dropped
  const missing = Object.entries(data.platform_status || {}).filter(([, st]) => st.status !== "ok");
  if (missing.length) {
    const label = { no_offers: "no offers found", timed_out: "timed out", error: "search failed" };
    children.push(
      h(
        "div",
        { class: "warn" },
        h("span", { class: "ico", "aria-hidden": "true" }, "⚠️"),
        h(
          "div",
          { style: "flex:1;min-width:0" },
          h("b", {}, "Not every app answered"),
          missing.map(([p, st]) =>
            h("div", {}, `${PLATFORM[p]?.name || p}: ${label[st.status] || st.status}` +
              (st.attempts > 1 ? ` (tried ${st.attempts}×)` : "")),
          ),
        ),
        h(
          "button",
          {
            onclick: () =>
              bridge.sendMessage(
                `Search ${missing.map(([p]) => PLATFORM[p]?.name || p).join(" and ")} again on its own for ${data.restaurant} in ${data.city}.`,
              ),
          },
          "Search again ↗",
        ),
      ),
    );
  }

  if (!offers.length) {
    children.push(h("div", { class: "state" }, data.note || "No dine-out offers found for this restaurant right now."));
  } else {
    const bestP = platformOf(best);
    children.push(
      h(
        "div",
        { class: "hero" },
        h("span", { class: "ico", "aria-hidden": "true" }, "🏆"),
        h(
          "div",
          {},
          h("b", {}, `Top deal: ${headline(best).text} on ${bestP.name}`),
          best.matches_your_cards
            ? `Pay with your ${shortBank(best.bank_name)} card to get it` +
                (pay && pay.bank === best.bank_name ? ` (${pay.card_name} also earns ${pay.reward_rate_percent}% ${pay.reward_type})` : "")
            : !usable(best)
              ? `Needs a ${shortBank(best.bank_name)} card, which you don't have`
              : pay
              ? `Pay with ${pay.card_name} for ${pay.reward_rate_percent}% ${pay.reward_type} on top`
              : best.discount_text || "",
        ),
      ),
    );
    children.push(h("div", { class: "grid" }, offers.map((o, i) => tile(o, i === 0, bridge))));
  }

  children.push(
    h(
      "div",
      { class: "foot" },
      pay
        ? h("span", {}, "💳 Best card here: ", h("b", {}, pay.card_name), ` · ${pay.reward_rate_percent}% ${pay.reward_type}`)
        : h("span", {}, `${offers.length} offer${offers.length === 1 ? "" : "s"} found`),
      offers.length > 1 &&
        h(
          "button",
          {
            onclick: () =>
              bridge.sendMessage(
                `Compare the dine-out offers for ${data.restaurant} in ${data.city} and tell me the single best way to pay, including which of my cards to use.`,
              ),
          },
          "Compare for me ↗",
        ),
    ),
  );

  root.replaceChildren(h("div", { class: "card" }, children));
}

const bridge = createBridge({
  name: "PayWise dine-out offers",
  version: "1.0.0",
  onToolInput: (a) => {
    args = a || {};
    if (!rendered) renderLoading();
  },
  onToolResult: (data) => render(data, bridge),
  onCancelled: () => {
    if (!rendered) root.replaceChildren(h("div", { class: "card" }, header(null), h("div", { class: "state" }, "Search cancelled.")));
  },
});

renderLoading();
bridge.connect().catch(() => {});

// Local preview / screenshot hook (not used inside Claude)
window.__paywiseRender = (data, a) => {
  args = a || {};
  render(data, bridge);
};
