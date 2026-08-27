#!/usr/bin/env python3
"""Render the GR e-Pass page locally, with sample data, for screenshots.

Why this exists: the page can only be seen inside Home Assistant, so every
screenshot used to start life showing a real subscription -- account number,
alias, card digits, toll plaza and the times somebody drove through it -- and had
to be cleaned afterwards. Cleaning pixels is error-prone and has to be redone
every time the layout changes. This builds a page that renders the real component
against a fabricated Home Assistant, so the screenshot never contains anything
real in the first place.

It is the panel's own JavaScript doing the drawing, so what you capture is what
users see, not an imitation.

    python tools/panel_preview.py            # both languages
    python tools/panel_preview.py --lang el
    python tools/panel_preview.py --state link      # a prepared payment link
    python tools/panel_preview.py --state receipt   # after a payment

Open the printed file in a browser and capture the card. Icons are fetched from
the Material Design Icons CDN on first run and cached next to the output; pass
--no-icons to skip them if you are offline.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PANEL_JS = os.path.join(ROOT, "custom_components", "gr_epass", "panel",
                        "gr-epass-panel.js")
MDI_URL = "https://cdn.jsdelivr.net/npm/@mdi/svg/svg/%s.svg"

# Everything below is invented. The account number is a round number no operator
# would issue, the card digits are the usual test sequence, and the plaza is
# named after nothing in particular.
ACCOUNT_ID = "10000000"
ALIAS = {"el": "Χρήστης", "en": "User"}
VEHICLE = {"el": "Αυτοκίνητο", "en": "My car"}
PLAZA = {"el": "ΔΙΟΔΙΑ Α", "en": "PLAZA A"}
CARD = "Mastercard ••••1234"


def icon_paths(names: list[str], cache: str, fetch: bool) -> dict[str, str]:
    """Map mdi names to svg path data, cached so repeat runs are offline."""
    known: dict[str, str] = {}
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as handle:
            known = json.load(handle)
    missing = [n for n in names if n not in known]
    if missing and fetch:
        for name in missing:
            try:
                with urllib.request.urlopen(MDI_URL % name, timeout=20) as resp:
                    svg = resp.read().decode("utf-8")
            except OSError as err:
                print("  could not fetch %s: %s" % (name, err), file=sys.stderr)
                continue
            match = re.search(r'\sd="([^"]+)"', svg)
            if match:
                known[name] = match.group(1)
        with open(cache, "w", encoding="utf-8") as handle:
            json.dump(known, handle, indent=1, sort_keys=True)
    return known


def entity(key: str, state, unit=None, attributes=None, domain="sensor",
           device="account") -> dict:
    return {
        "key": key,
        "entity_id": "%s.gr_epass_preview_%s_%s" % (domain, device, key),
        "state": str(state),
        "unit": unit,
        "attributes": attributes or {},
    }


def iso(**offset) -> str:
    """A timestamp relative to now.

    Fixed dates would go stale: a link whose expiry is in the past renders as
    "expired" instead of showing the countdown the screenshot is meant to show.
    """
    return (datetime.now(timezone.utc) + timedelta(**offset)).isoformat()


def build_hass(lang: str, state: str) -> dict:
    """The smallest Home Assistant the page is willing to read."""
    money = "EUR"
    link = None
    link_result = None
    last_order = None
    if state == "link":
        link = "https://example.invalid/api/gr_epass/pay/Xk3pQ9vT2mR7wLnB4sZaHg"
    elif state == "receipt":
        last_order = "26082712000010000000-100000-10000000"
        link_result = "used"

    account = [
        entity("balance", "17.24", money),
        entity("balance_status", "good"),
        entity("account_status", "active", attributes={
            "account_id": ACCOUNT_ID,
            "account_alias": ALIAS[lang],
            "account_profile": "ePASS 1.2",
            "operator": "attiki",
        }),
        entity("transponder_count", "1"),
        entity("low_balance_threshold", "12.00", money, domain="number"),
        entity("invalid_balance_limit", "2.55", money),
        entity("last_payment_amount", "1.00", money),
        entity("last_payment_date", iso(days=-7)),
        entity("passes_month", "2"),
        entity("cost_month", "5.10", money),
        entity("cost_month_own", "5.10", money),
        entity("cost_month_other", "0.00", money),
        entity("payments_month", "16.00", money),
        entity("passes_today", "1"),
        entity("cost_today", "2.55", money),
        entity("last_pass", iso(hours=-6), attributes={
            "plaza": PLAZA[lang],
            "lane": "A-L02",
            "amount": 2.55,
            "external_network": False,
        }),
        entity("payment_card", CARD, domain="select",
               attributes={"options": [CARD, "Visa ••••5678"]}),
        entity("topup_amount", "5.00", money, domain="number",
               attributes={"min": 0.01, "max": 5000}),
        entity("prepare_topup", iso(minutes=-2), domain="button",
               attributes={
                   "link": link,
                   "link_expires": iso(minutes=8) if link else None,
                   "link_result": link_result,
                   "link_result_at": iso(minutes=-3) if link_result else None,
                   "last_order_id": last_order,
               }),
    ]
    transponder = [
        entity("transponder_status", "active", device="veh", attributes={
            "plate": "AB 1234", "toll_category": 2,
        }),
        entity("passes_today", "1", device="veh"),
        entity("cost_today", "2.55", money, device="veh"),
        entity("passes_month", "2", device="veh"),
        entity("cost_month", "5.10", money, device="veh"),
        entity("last_pass", iso(hours=-6), device="veh", attributes={
            "plaza": PLAZA[lang], "lane": "A-L02", "amount": 2.55,
            "external_network": False,
        }),
    ]

    entities, states = {}, {}
    for group, device_id, name in (
        (account, "dev_account", "e-PASS %s" % ACCOUNT_ID),
        (transponder, "dev_veh", VEHICLE[lang]),
    ):
        for item in group:
            entities[item["entity_id"]] = {
                "entity_id": item["entity_id"],
                "device_id": device_id,
                "platform": "gr_epass",
                "translation_key": item["key"],
            }
            states[item["entity_id"]] = {
                "entity_id": item["entity_id"],
                "state": item["state"],
                "attributes": dict(
                    item["attributes"],
                    **({"unit_of_measurement": item["unit"]} if item["unit"] else {})
                ),
            }
    devices = {
        "dev_account": {"name": "e-PASS %s" % ACCOUNT_ID, "name_by_user": None},
        "dev_veh": {"name": VEHICLE[lang], "name_by_user": None},
    }
    return {"entities": entities, "states": states, "devices": devices,
            "language": lang}


HTML = """<!doctype html>
<meta charset="utf-8">
<title>GR e-Pass preview (%(lang)s)</title>
<body>
<style>
  /* The page reads Home Assistant's theme variables. Without them the text is
     black on a dark background and the whole card renders invisible -- which is
     what a blank preview actually meant. These match HA's default dark theme
     closely enough that the capture looks like the real thing. */
  :root {
    --primary-text-color: #e1e1e1;
    --secondary-text-color: #9b9b9b;
    --divider-color: rgba(225, 225, 225, 0.12);
    --primary-color: #03a9f4;
    --error-color: #db4437;
    --card-background-color: #1c1c1c;
    --ha-card-background: #1c1c1c;
    --secondary-background-color: #202020;
    --state-icon-color: #9b9b9b;
    --paper-item-icon-color: #9b9b9b;
    --ha-card-border-radius: 12px;
    --ha-card-box-shadow: none;
  }
  html, body { margin: 0; background: %(page)s; color: var(--primary-text-color); }
  body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
</style>
<script>
// A stand-in for Home Assistant's ha-icon, drawing the same Material icon so the
// capture matches what users see. Without it the icon column renders empty.
const ICONS = %(icons)s;
class HaIconStub extends HTMLElement {
  connectedCallback() { this._draw(); }
  attributeChangedCallback() { this._draw(); }
  static get observedAttributes() { return ["icon"]; }
  _draw() {
    const name = (this.getAttribute("icon") || "").replace(/^mdi:/, "");
    const path = ICONS[name];
    this.style.display = "inline-flex";
    this.style.width = "24px";
    this.style.height = "24px";
    this.innerHTML = path
      ? '<svg viewBox="0 0 24 24" style="width:100%%;height:100%%;fill:currentColor">'
        + '<path d="' + path + '"></path></svg>'
      : "";
  }
}
customElements.define("ha-icon", HaIconStub);
</script>
<script>
// The panel's own source, inlined. Referencing it as a separate file made the
// preview depend on relative paths, which some viewers do not give it -- and a
// self-contained file can be opened or sent anywhere.
%(panel)s
</script>
<script>
const DATA = %(data)s;

// Values are shown through hass.formatEntityState, so the stand-in formats the
// same two kinds the page cares about: money and timestamps.
function formatEntityState(stateObj) {
  const attrs = stateObj.attributes || {};
  const raw = stateObj.state;
  if (attrs.unit_of_measurement === "EUR") {
    const n = Number(raw);
    if (!Number.isFinite(n)) return raw;
    return n.toLocaleString(DATA.language === "el" ? "el-GR" : "en-GB",
      { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " \\u20ac";
  }
  if (/^\\d{4}-\\d{2}-\\d{2}T/.test(raw)) {
    const d = new Date(raw);
    if (!isNaN(d)) {
      return d.toLocaleString(DATA.language === "el" ? "el-GR" : "en-GB",
        { dateStyle: "long", timeStyle: "short" });
    }
  }
  if (raw === "active") return DATA.language === "el" ? "Ενεργή" : "Active";
  if (raw === "good") return DATA.language === "el" ? "Έγκυρος" : "Valid";
  return raw;
}

const hass = {
  entities: DATA.entities,
  states: DATA.states,
  devices: DATA.devices,
  language: DATA.language,
  formatEntityState,
  // Nothing here should reach a real service; the preview is read-only.
  callService: (domain, service) => {
    console.info("preview: ignored", domain + "." + service);
    return Promise.resolve();
  },
};

// Failures are written into the page: this file is opened in whatever browser
// is at hand, often without devtools, and a blank page says nothing.
function report(message) {
  const box = document.createElement("pre");
  box.style.cssText =
    "margin:16px;padding:14px;background:#3b1111;color:#ffd9d9;" +
    "font:13px/1.5 ui-monospace,monospace;white-space:pre-wrap;border-radius:8px";
  box.textContent = "preview failed\\n\\n" + message;
  (document.body || document.documentElement).appendChild(box);
}
window.addEventListener("error", (e) =>
  report((e.message || "error") + "\\n" + (e.filename || "") + ":" + (e.lineno || "")));

function start() {
try {
  if (!customElements.get("gr-epass-panel")) {
    throw new Error("gr-epass-panel was never defined - did panel.js load?");
  }
  const panel = document.createElement("gr-epass-panel");
  document.body.appendChild(panel);
  panel.hass = hass;
  // A panel that drew nothing is a failure worth seeing, not an empty page.
  setTimeout(() => {
    const root = panel.shadowRoot;
    const painted = root && root.textContent && root.textContent.trim().length > 20;
    if (!painted) {
      report("the component rendered nothing.\\n\\nshadowRoot: "
        + (root ? "present" : "missing")
        + "\\ntext length: " + (root ? root.textContent.trim().length : 0));
    }
  }, 1200);
} catch (err) {
  report((err && err.stack) || String(err));
}
}

// Scripts here run while the document is still being parsed, so document.body
// can be null -- appending to it then throws, and so does reporting the throw.
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", start);
} else {
  start();
}
</script>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=("el", "en"), action="append",
                        help="language to render; repeatable, default both")
    parser.add_argument("--state", choices=("idle", "link", "receipt"),
                        default="idle",
                        help="idle, a prepared link, or after a payment")
    parser.add_argument("--out", default=None,
                        help="output directory (default: shots-raw/preview)")
    parser.add_argument("--no-icons", action="store_true",
                        help="skip fetching icons")
    args = parser.parse_args()

    langs = args.lang or ["el", "en"]
    out_dir = args.out or os.path.join(ROOT, "shots-raw", "preview")
    os.makedirs(out_dir, exist_ok=True)

    source = open(PANEL_JS, encoding="utf-8").read()
    names = sorted(set(re.findall(r"mdi:([a-z0-9-]+)", source)))
    icons = icon_paths(names, os.path.join(out_dir, "icons.json"),
                       fetch=not args.no_icons)
    missing = [n for n in names if n not in icons]
    if missing:
        print("  icons missing (will render blank): %s" % ", ".join(missing))

    for lang in langs:
        name = "panel-%s%s.html" % (lang, "" if args.state == "idle" else "-" + args.state)
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(HTML % {
                "lang": lang,
                "page": "#111111",
                "icons": json.dumps(icons),
                "panel": source,
                "data": json.dumps(build_hass(lang, args.state), ensure_ascii=False),
            })
        print("  %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
