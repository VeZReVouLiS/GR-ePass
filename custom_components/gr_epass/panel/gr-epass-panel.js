/*
 * Sidebar panel for the GR e-Pass integration.
 *
 * Served by the integration itself, so there is no build step and no HACS
 * frontend plugin to install separately: plain custom element, no framework.
 *
 * Two things it does that a hand-written Lovelace card cannot:
 *
 *   1. Finds its own entities. It filters the entity registry by platform and
 *      groups by device, so it keeps working when entities are renamed and it
 *      shows every subscription without anyone editing YAML.
 *   2. Follows the user's language. Values go through hass.formatEntityState,
 *      which returns the translated enum state and the locale-formatted number,
 *      and its own labels come from the LABELS table below keyed on
 *      hass.language.
 */

const BRAND = {
  navy: "#024e7e",
  yellow: "#fcbd02",
  green: "#0dd058",
  amber: "#ffb900",
  red: "#ff253a",
  grey: "#a0a0a0",
};

// The donut in the portal is a filled circle whose colour alone changes, driven
// by BalanceStatus, with grey reserved for a closed account.
const STATUS_COLOUR = {
  good: BRAND.green,
  low: BRAND.amber,
  bad: BRAND.red,
};

// PaymentCardType as the operator reports it on a receipt.
const CARD_NAMES = {
  0: "\u2014",
  1: "Visa",
  2: "Mastercard",
  3: "Maestro",
  4: "American Express",
  5: "Diners",
};

// Top-up page per operator. The page only ever opens one of these, so they are
// listed rather than derived from an attribute that a browser would then follow.
const PORTALS = {
  attiki: "https://epass.naodos.gr/PaymentA",
  egnatia: "https://myegnatiapass.gr/PaymentA",
};

// The row for the subscriber's own network is named after the operator they
// signed up with; every other motorway reached through interoperability falls
// under "other". Keyed on the operator attribute the account status carries.
const NETWORKS = {
  attiki: { el: "Αττική Οδός", en: "Attiki Odos" },
  egnatia: { el: "Εγνατία Οδός", en: "Egnatia Odos" },
};

// How long a "cancelled" note stays on the page.
const NOTE_MS = 12000;

const LABELS = {
  el: {
    balance: "Υπόλοιπο",
    noAccounts: "Δεν βρέθηκε συνδρομή e-PASS. Πρόσθεσε το integration από τις Ρυθμίσεις.",
    plan: "Συνδρομητικό πρόγραμμα",
    accountStatus: "Κατάσταση συνδρομής",
    lastPayment: "Τελευταία πληρωμή",
    paymentDate: "Ημερομηνία πληρωμής",
    transponders: "Πομποδέκτες",
    threshold: "Όριο ειδοποίησης",
    noPassLimit: "Όριο άκυρου λογαριασμού",
    activity: "Κινήσεις",
    passesMonth: "Διελεύσεις μήνα",
    costMonth: "Κόστος διελεύσεων μήνα",
    ownNetwork: "Δίκτυο παρόχου",
    other: "Άλλα δίκτυα",
    paymentsMonth: "Πληρωμές μήνα",
    lastPass: "Τελευταία διέλευση",
    noPass: "Καμία διέλευση καταγεγραμμένη",
    topUp: "Ανανέωση υπολοίπου",
    card: "Κάρτα",
    amount: "Ποσό",
    prepare: "Προετοιμασία πληρωμής",
    prepareHint: "Δεν χρεώνει. Φτιάχνει σύνδεσμο μιας χρήσης, που λήγει σε 10 λεπτά, ο οποίος δείχνει ποσό και κάρτα πριν σε στείλει στην τράπεζα.",
    openPortal: "Άνοιγμα my e-PASS",
    receiptOpen: "Προβολή απόδειξης",
    receiptBlocked: "Το πρόγραμμα περιήγησης μπλόκαρε το νέο παράθυρο. Επέτρεψε τα αναδυόμενα παράθυρα για αυτή τη σελίδα και ξαναδοκίμασε.",
    receiptWait: "Γίνεται λήψη…",
    receiptNone: "Η απόδειξη δεν είναι διαθέσιμη ακόμη. Η τράπεζα την επιβεβαιώνει λίγο μετά την πληρωμή — δοκίμασε ξανά σε λίγο.",
    receiptTitle: "Απόδειξη πληρωμής",
    receiptAmount: "Ποσό",
    receiptDate: "Ημερομηνία",
    receiptCard: "Κάρτα",
    receiptApproval: "Κωδικός έγκρισης",
    receiptTxn: "Κωδικός συναλλαγής",
    receiptOrder: "Κωδικός παραγγελίας",
    receiptStatus: "Κατάσταση",
    receiptApproved: "Εγκρίθηκε",
    receiptDeclined: "Δεν εγκρίθηκε",
    receiptPrint: "Εκτύπωση / Αποθήκευση PDF",
    receiptBack: "Επιστροφή στο Home Assistant",
    receiptNote: "Εκδόθηκε από το Home Assistant με στοιχεία του παρόχου.",
    receiptNoteTax: "Δεν αντικαθιστά φορολογικό παραστατικό.",
    refresh: "Ανανέωση στοιχείων",
    linkReady: "Έτοιμο. Άνοιξε τον σύνδεσμο για να ολοκληρώσεις.",
    linkOpen: "Ολοκλήρωση πληρωμής",
    linkCancel: "Ακύρωση",
    linkCancelling: "Ακυρώνεται…",
    linkExpires: "Λήγει σε",
    linkExpired: "Ο σύνδεσμος έληξε.",
    linkCancelled: "Η συναλλαγή ακυρώθηκε. Δεν έγινε καμία χρέωση.",
    noCard: "Δεν υπάρχει αποθηκευμένη κάρτα. Η πρώτη χρέωση γίνεται στο my e-PASS, με «αποθήκευση κάρτας».",
    externalNet: "σε άλλο δίκτυο",
    lane: "λωρίδα",
    vehicles: "Πομποδέκτες",
    today: "Σήμερα",
    month: "Μήνας",
    plate: "Πινακίδα",
    category: "Κατηγορία",
    status: "Κατάσταση",
  },
  en: {
    balance: "Balance",
    noAccounts: "No e-PASS subscription found. Add the integration from Settings.",
    plan: "Subscription plan",
    accountStatus: "Account status",
    lastPayment: "Last payment",
    paymentDate: "Payment date",
    transponders: "Transponders",
    threshold: "Warning threshold",
    noPassLimit: "No-pass limit",
    activity: "Activity",
    passesMonth: "Passes this month",
    costMonth: "Toll cost this month",
    ownNetwork: "Own network",
    other: "Other networks",
    paymentsMonth: "Payments this month",
    lastPass: "Last pass",
    noPass: "No pass recorded yet",
    topUp: "Top up",
    card: "Card",
    amount: "Amount",
    prepare: "Prepare payment",
    prepareHint: "Does not charge anything. It creates a single-use link, valid for 10 minutes, that shows the amount and card before handing you to the bank.",
    openPortal: "Open my e-PASS",
    receiptOpen: "View receipt",
    receiptBlocked: "The browser blocked the new window. Allow popups for this page and try again.",
    receiptWait: "Fetching…",
    receiptNone: "The receipt is not available yet. The bank confirms it shortly after payment - try again in a moment.",
    receiptTitle: "Payment receipt",
    receiptAmount: "Amount",
    receiptDate: "Date",
    receiptCard: "Card",
    receiptApproval: "Approval code",
    receiptTxn: "Transaction id",
    receiptOrder: "Order id",
    receiptStatus: "Status",
    receiptApproved: "Approved",
    receiptDeclined: "Not approved",
    receiptPrint: "Print / Save as PDF",
    receiptBack: "Back to Home Assistant",
    receiptNote: "Produced by Home Assistant from the operator's data.",
    receiptNoteTax: "It is not a tax document.",
    refresh: "Refresh data",
    linkReady: "Ready. Open the link to finish.",
    linkOpen: "Complete payment",
    linkCancel: "Cancel",
    linkCancelling: "Cancelling…",
    linkExpires: "Expires in",
    linkExpired: "The link has expired.",
    linkCancelled: "The transaction was cancelled. Nothing was charged.",
    noCard: "No stored card. The first charge happens on my e-PASS, with \"save card\" ticked.",
    externalNet: "on another network",
    lane: "lane",
    vehicles: "Transponders",
    today: "Today",
    month: "This month",
    plate: "Plate",
    category: "Category",
    status: "Status",
  },
};

const STYLE = `
  /* One base size for the whole panel; every length below is in em, so the
     card grows with the window instead of staying phone-sized on a monitor.
     The clamp lands on 14px at phone widths -- what the panel used to hardcode
     -- and tops out at 20px so a very wide screen does not turn comical. */
  :host { display: block; font-size: clamp(14px, 0.35vw + 12.2px, 20px); }
  /* Full width on purpose. Rows put the label left and the value right, so on a
     wide monitor the two do sit far apart; the larger type is what keeps the
     pair readable. */
  .wrap { max-width: 100%; margin: 0; padding: clamp(12px, 1.1vw, 28px); }
  /* Two columns once there is room for them; one column on a phone. */
  @media (min-width: 900px) {
    .body { display: grid; grid-template-columns: 1fr 1fr; gap: 0 2em;
            align-items: start; }
    .col > h3:first-child { margin-top: 0; }
  }
  .linkHead { text-align: center; }
  /* An anchor rather than a button, so the confirmation page still opens in its
     own tab, but wearing the same clothes as every other action in the card. */
  .btnLink { display: block; box-sizing: border-box; text-align: center;
             text-decoration: none; font: inherit; font-weight: 600;
             border-radius: 8px; padding: 11px 16px; margin-top: 12px;
             background: ${BRAND.navy}; color: #fff; }
  .countdown { font-size: 0.86em; color: var(--secondary-text-color);
               margin-top: 10px; text-align: center; }
  .countdown b { color: var(--primary-text-color);
                 font-variant-numeric: tabular-nums; }
  .countdown.low b { color: var(--error-color, #c22); }
  .card { background: var(--ha-card-background, var(--card-background-color, #fff));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 4px rgba(0,0,0,.14));
          overflow: hidden; margin-bottom: 16px; }
  .head { background: ${BRAND.navy}; color: #fff; padding: 14px 18px;
          border-bottom: 3px solid ${BRAND.yellow}; }
  .head { display: flex; align-items: center; gap: 12px; }
  .head .headText { flex: 1; min-width: 0; }
  .head h2 { margin: 0; font-size: 1.29em; font-weight: 600; }
  /* The shared button rule sets width:100% and a top margin for the full-width
     action buttons, both of which have to be undone here or this one eats the
     header and pushes the title into a single-word column. */
  .head .refresh { flex: none; width: 36px; height: 36px; padding: 6px;
                   margin: 0; background: none; border: none; color: #fff;
                   cursor: pointer; border-radius: 50%; display: flex;
                   align-items: center; justify-content: center; opacity: .85; }
  .head .refresh:hover { opacity: 1; background: rgba(255,255,255,.14); }
  /* Spins while the request is in flight, so a slow poll still looks alive. */
  .head .refresh[disabled] { cursor: default; animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .head .sub { color: ${BRAND.yellow}; font-size: 0.93em; margin-top: 2px; }
  .body { padding: 18px; }
  .donutWrap { display: flex; justify-content: center; padding: 6px 0 14px; }
  .donut { width: 11.3em; height: 11.3em; border-radius: 50%;
           display: flex; align-items: center; justify-content: center; }
  .hole { width: 7.4em; height: 7.4em; border-radius: 50%; display: flex;
          flex-direction: column; align-items: center; justify-content: center;
          gap: 2px; background: var(--ha-card-background, var(--card-background-color, #fff)); }
  .amt { font-size: 1.36em; font-weight: 700; white-space: nowrap;
         color: var(--primary-text-color); }
  .st { font-size: 0.86em; }
  .caption { text-align: center; font-size: 0.93em;
             color: var(--secondary-text-color); }
  .rows { display: grid; grid-template-columns: 1.75em 1fr auto; gap: 0.7em 0.85em;
          align-items: center; font-size: 1em; }
  .rows ha-icon { color: var(--state-icon-color, var(--paper-item-icon-color));
                  --mdc-icon-size: 1.43em; }
  .rows .k { color: var(--primary-text-color); }
  .rows .v { color: var(--secondary-text-color); text-align: right; }
  h3 { font-size: 1.07em; margin: 1.55em 0 0.7em; color: var(--primary-text-color); }
  .sep { height: 1px; background: var(--divider-color); margin: 14px 0; grid-column: 1 / -1; }
  .rows .full { grid-column: 2 / -1; }
  select, input { font: inherit; color: var(--primary-text-color);
                  background: var(--secondary-background-color);
                  border: 1px solid var(--divider-color); border-radius: 6px;
                  padding: 6px 8px; max-width: 210px; }
  button { font: inherit; font-weight: 600; border: none; border-radius: 8px;
           padding: 11px 16px; background: ${BRAND.navy}; color: #fff;
           cursor: pointer; width: 100%; margin-top: 14px; }
  button.secondary { background: transparent; color: var(--primary-color);
                     border: 1px solid var(--divider-color); }
  button:disabled { opacity: .5; cursor: default; }
  .note { font-size: 0.86em; color: var(--secondary-text-color);
          line-height: 1.45; margin-top: 12px; }
  .warn { background: rgba(255,185,0,.12); border-left: 3px solid ${BRAND.amber};
          padding: 10px 12px; border-radius: 4px; font-size: 0.93em;
          margin-top: 12px; }
  .ok { background: rgba(13,208,88,.12); border-left: 3px solid ${BRAND.green};
        padding: 10px 12px; border-radius: 4px; font-size: 0.93em; margin-top: 12px; }
  .empty { text-align: center; color: var(--secondary-text-color); padding: 40px 16px; }
  a.finish { display: block; text-align: center; margin-top: 10px;
             color: var(--primary-color); font-weight: 600; }
  .veh { border: 1px solid var(--divider-color); border-radius: 8px;
         padding: 12px 14px; margin-bottom: 10px; }
  .vehName { font-weight: 600; font-size: 1em; margin-bottom: 8px;
             color: var(--primary-text-color); }
`;

class GrEpassPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
    this._signature = "";
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  set narrow(value) {
    this._narrow = value;
  }

  get _t() {
    const lang = (this._hass?.language || "en").toLowerCase();
    return lang.startsWith("el") ? LABELS.el : LABELS.en;
  }

  /*
   * Group this integration's entities by the device they belong to.
   *
   * Entities are grouped by device and keyed by translation_key, so a renamed
   * entity is still found and the two device shapes -- the subscription and one
   * per transponder -- are told apart by which keys they carry.
   */
  _accounts() {
    const hass = this._hass;
    if (!hass?.entities) return [];

    const byDevice = new Map();
    for (const entry of Object.values(hass.entities)) {
      if (entry.platform !== "gr_epass" || !entry.device_id) continue;
      if (!byDevice.has(entry.device_id)) byDevice.set(entry.device_id, []);
      byDevice.get(entry.device_id).push(entry);
    }

    const accounts = [];
    const transponders = [];
    for (const [deviceId, entries] of byDevice) {
      const device = hass.devices?.[deviceId];
      const group = {
        deviceId,
        name: device?.name_by_user || device?.name || "e-PASS",
        entities: {},
      };
      for (const entry of entries) {
        // translation_key is what the integration declares for each entity and
        // it does not change when the user renames the entity, so it is the
        // only safe key here. Entity ids are not: the per-transponder ones are
        // slugged from the transponder alias, not from the account id.
        if (entry.translation_key) group.entities[entry.translation_key] = entry.entity_id;
      }
      // Only the subscription device carries a balance; the rest are vehicles.
      if (group.entities.balance) accounts.push(group);
      else transponders.push(group);
    }
    for (const account of accounts) account.transponders = transponders;
    return accounts;
  }

  _state(entityId) {
    return entityId ? this._hass.states[entityId] : undefined;
  }

  /** Localised, formatted value straight from Home Assistant. */
  _fmt(entityId, fallback = "—") {
    const stateObj = this._state(entityId);
    if (!stateObj || ["unknown", "unavailable", ""].includes(stateObj.state)) {
      return fallback;
    }
    try {
      return this._hass.formatEntityState(stateObj);
    } catch (err) {
      return stateObj.state;
    }
  }

  _num(entityId) {
    const stateObj = this._state(entityId);
    const value = parseFloat(stateObj?.state);
    return Number.isNaN(value) ? null : value;
  }

  _update() {
    const accounts = this._accounts();
    // Rebuild only when the set of entities changes, so typing in a field or
    // an open dropdown is not destroyed by an unrelated state update.
    const signature = JSON.stringify(
      accounts.map((a) => [a.deviceId, Object.keys(a.entities).sort()])
    ) + (this._hass?.language || "");
    if (signature !== this._signature) {
      this._signature = signature;
      this._build(accounts);
    }
    this._paint(accounts);
  }

  _build(accounts) {
    const t = this._t;
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><div class="wrap"></div>`;
    const wrap = this.shadowRoot.querySelector(".wrap");
    this._refs = [];

    if (!accounts.length) {
      wrap.innerHTML = `<div class="card"><div class="empty">${t.noAccounts}</div></div>`;
      return;
    }

    for (const account of accounts) {
      const section = document.createElement("div");
      section.className = "card";
      section.innerHTML = `
        <div class="head">
          <div class="headText">
            <h2></h2>
            <div class="sub"></div>
          </div>
          <button class="refresh" title="${t.refresh}" aria-label="${t.refresh}">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
        </div>
        <div class="body">
          <div class="col">
          <div class="caption">${t.balance}</div>
          <div class="donutWrap">
            <div class="donut"><div class="hole">
              <span class="amt"></span><span class="st"></span>
            </div></div>
          </div>

          <div class="rows">
            <ha-icon icon="mdi:card-account-details-outline"></ha-icon><span class="k">${t.plan}</span><span class="v" data-k="plan"></span>
            <ha-icon icon="mdi:check-circle"></ha-icon><span class="k">${t.accountStatus}</span><span class="v" data-k="account_status"></span>
            <span class="sep"></span>
            <ha-icon icon="mdi:cash-check"></ha-icon><span class="k">${t.lastPayment}</span><span class="v" data-k="last_payment_amount"></span>
            <ha-icon icon="mdi:calendar-check"></ha-icon><span class="k">${t.paymentDate}</span><span class="v" data-k="last_payment_date"></span>
            <span class="sep"></span>
            <ha-icon icon="mdi:credit-card-multiple-outline"></ha-icon><span class="k">${t.transponders}</span><span class="v" data-k="transponder_count"></span>
            <ha-icon icon="mdi:bell-alert-outline"></ha-icon><span class="k">${t.threshold}</span><span class="v" data-k="low_balance_threshold"></span>
            <ha-icon icon="mdi:boom-gate-alert-outline"></ha-icon><span class="k">${t.noPassLimit}</span><span class="v" data-k="invalid_balance_limit"></span>
          </div>

          <h3>${t.activity}</h3>
          <div class="rows">
            <ha-icon icon="mdi:boom-gate-arrow-up"></ha-icon><span class="k">${t.passesMonth}</span><span class="v" data-k="passes_month"></span>
            <ha-icon icon="mdi:cash"></ha-icon><span class="k">${t.costMonth}</span><span class="v" data-k="cost_month"></span>
            <ha-icon icon="mdi:road-variant"></ha-icon><span class="k">— <span data-net></span></span><span class="v" data-k="cost_month_attiki"></span>
            <ha-icon icon="mdi:swap-horizontal"></ha-icon><span class="k">— ${t.other}</span><span class="v" data-k="cost_month_other"></span>
            <ha-icon icon="mdi:cash-plus"></ha-icon><span class="k">${t.paymentsMonth}</span><span class="v" data-k="payments_month"></span>
          </div>
          </div>

          <div class="col">
          <h3>${t.lastPass}</h3>
          <div class="note lastPass"></div>

          <h3>${t.topUp}</h3>
          <div class="topUp"></div>

          <div class="vehicles"></div>
          </div>
        </div>`;
      section.querySelector(".refresh").addEventListener("click", async (event) => {
        const button = event.currentTarget;
        button.disabled = true;
        try {
          // Updating one entity of the integration is enough: they all share a
          // coordinator, so this refetches the whole subscription.
          await this._hass.callService("homeassistant", "update_entity", {
            entity_id: account.entities.balance,
          });
        } finally {
          button.disabled = false;
        }
      });
      wrap.appendChild(section);
      this._refs.push({ account, section });
      this._buildTopUp(account, section.querySelector(".topUp"));
    }
  }

  _buildTopUp(account, host) {
    const t = this._t;
    const { payment_card, topup_amount, prepare_topup } = account.entities;

    if (!prepare_topup) {
      host.innerHTML = `<div class="note">${t.noCard}</div>`;
      return;
    }

    host.innerHTML = `
      <div class="rows">
        <ha-icon icon="mdi:credit-card-outline"></ha-icon>
        <span class="k">${t.card}</span>
        <span class="v"><select class="cardSel"></select></span>
        <ha-icon icon="mdi:cash-plus"></ha-icon>
        <span class="k">${t.amount}</span>
        <span class="v"><input class="amtIn" type="number" step="0.01" inputmode="decimal"> €</span>
      </div>
      <button class="prep">${t.prepare}</button>
      <div class="note">${t.prepareHint}</div>
      <div data-linkbox></div>
      <button class="secondary receipt" hidden>${t.receiptOpen}</button>
      <button class="secondary portal">${t.openPortal}</button>`;

    host.querySelector(".receipt").addEventListener("click", async (event) => {
      const button = event.currentTarget;
      const label = button.textContent;
      button.disabled = true;
      button.textContent = t.receiptWait;
      try {
        // wait:true lets the integration retry while the bank confirms, which it
        // does a moment after the payer finishes rather than immediately.
        const result = await this._hass.callService(
          "gr_epass",
          "get_receipt",
          { wait: true },
          undefined,
          false,
          true
        );
        const payload = result && result.response;
        if (payload && payload.found && payload.receipt) {
          this._openReceipt(payload.receipt);
        } else {
          alert(t.receiptNone);
        }
      } finally {
        button.disabled = false;
        button.textContent = label;
      }
    });

    host.querySelector(".portal").addEventListener("click", () => {
      // Whichever operator this subscription belongs to, not a fixed one.
      const status = this._state(account.entities.account_status);
      const url = PORTALS[status?.attributes?.operator] || PORTALS.attiki;
      window.open(url, "_blank", "noopener");
    });

    if (payment_card) {
      host.querySelector(".cardSel").addEventListener("change", (event) => {
        this._hass.callService("select", "select_option", {
          entity_id: payment_card,
          option: event.target.value,
        });
      });
    }
    if (topup_amount) {
      host.querySelector(".amtIn").addEventListener("change", (event) => {
        this._hass.callService("number", "set_value", {
          entity_id: topup_amount,
          value: event.target.value,
        });
      });
    }
    host.querySelector(".prep").addEventListener("click", async (event) => {
      event.target.disabled = true;
      try {
        await this._hass.callService("button", "press", {
          entity_id: prepare_topup,
        });
      } finally {
        // The link arrives with the next state update; re-enable either way so a
        // failure does not leave the button stuck.
        event.target.disabled = false;
      }
    });
  }

  _paint(accounts) {
    if (!this._refs?.length) return;
    const t = this._t;

    for (const { account, section } of this._refs) {
      const ent = account.entities;
      section.querySelector(".head h2").textContent = account.name;

      // The card should look like the portal behind it, so a subscription from
      // another operator is recognisable at a glance.
      const brand = this._state(ent.account_status)?.attributes;
      const head = section.querySelector(".head");
      const navy = brand?.brand_navy || BRAND.navy;
      const accent = brand?.brand_accent || BRAND.yellow;
      if (head.dataset.brand !== navy + accent) {
        head.dataset.brand = navy + accent;
        head.style.background = navy;
        head.style.borderBottomColor = accent;
        section.querySelector(".head .sub").style.color = accent;
      }

      const statusObj = this._state(ent.account_status);
      const alias = statusObj?.attributes?.account_alias;
      const profile = statusObj?.attributes?.account_profile;
      const accountId = statusObj?.attributes?.account_id;
      section.querySelector(".head .sub").textContent = [
        alias && accountId ? `${alias} (${accountId})` : alias || accountId,
        profile,
      ]
        .filter(Boolean)
        .join(" · ");

      this._paintDonut(section, ent);

      for (const cell of section.querySelectorAll(".rows .v[data-k]")) {
        const key = cell.dataset.k;
        if (key === "plan") {
          cell.textContent = profile || "—";
        } else {
          cell.textContent = this._fmt(ent[key]);
        }
      }

      const net = section.querySelector("[data-net]");
      if (net) {
        const key = statusObj?.attributes?.operator;
        const lang = this._hass?.language?.toLowerCase().startsWith("el")
          ? "el"
          : "en";
        net.textContent = NETWORKS[key]?.[lang] || this._t.ownNetwork;
      }

      this._paintLastPass(section.querySelector(".lastPass"), ent);
      this._paintTopUp(section.querySelector(".topUp"), ent);
      this._paintVehicles(section.querySelector(".vehicles"), account);
    }
  }

  _paintDonut(section, ent) {
    const balance = this._num(ent.balance);
    const status = this._state(ent.balance_status)?.state;
    const closed = this._state(ent.account_status)?.state === "closed";
    const threshold = this._num(ent.low_balance_threshold);

    let colour = closed ? BRAND.grey : STATUS_COLOUR[status] || BRAND.red;
    // Same extra rule as the Lovelace card: the operator's status only flips at
    // its own fixed limit, so a stricter personal threshold turns it red early.
    if (!closed && threshold !== null && balance !== null && balance < threshold) {
      colour = BRAND.red;
    }

    section.querySelector(".donut").style.background = colour;
    section.querySelector(".amt").textContent = this._fmt(ent.balance);
    const stateCell = section.querySelector(".st");
    stateCell.textContent = closed ? "" : this._fmt(ent.balance_status, "");
    stateCell.style.color = colour;
  }

  _paintLastPass(host, ent) {
    const t = this._t;
    const stateObj = this._state(ent.last_pass);
    if (!stateObj || ["unknown", "unavailable"].includes(stateObj.state)) {
      host.textContent = t.noPass;
      return;
    }
    const attrs = stateObj.attributes || {};
    const when = new Date(stateObj.state);
    const parts = [
      attrs.plaza,
      attrs.lane ? `${t.lane} ${attrs.lane}` : null,
      attrs.amount != null ? `${attrs.amount} €` : null,
    ].filter(Boolean);
    host.textContent =
      `${parts.join(" · ")}\n${when.toLocaleString(this._hass.language)}` +
      (attrs.external_network ? ` (${t.externalNet})` : "");
    host.style.whiteSpace = "pre-line";
  }

  /*
   * One compact block per transponder.
   *
   * Rebuilt in place rather than in _build, because a subscription can gain or
   * lose a vehicle between refreshes and the account card should not have to be
   * torn down for that.
   */
  _paintVehicles(host, account) {
    const t = this._t;
    const vehicles = account.transponders || [];
    if (!vehicles.length) {
      host.innerHTML = "";
      return;
    }

    const signature = vehicles.map((v) => v.deviceId).join("|");
    if (host.dataset.sig !== signature) {
      host.dataset.sig = signature;
      host.innerHTML =
        `<h3>${t.vehicles}</h3>` +
        vehicles
          .map(
            (v) => `<div class="veh" data-dev="${v.deviceId}">
              <div class="vehName"></div>
              <div class="rows">
                <ha-icon icon="mdi:check-circle"></ha-icon><span class="k">${t.status}</span><span class="v" data-vk="transponder_status"></span>
                <ha-icon icon="mdi:calendar-today"></ha-icon><span class="k">${t.today}</span><span class="v" data-vk="today"></span>
                <ha-icon icon="mdi:calendar-month"></ha-icon><span class="k">${t.month}</span><span class="v" data-vk="month"></span>
                <ha-icon icon="mdi:road-variant"></ha-icon><span class="k">${t.lastPass}</span><span class="v" data-vk="last_pass"></span>
              </div>
            </div>`
          )
          .join("");
    }

    for (const vehicle of vehicles) {
      const block = host.querySelector(`.veh[data-dev="${vehicle.deviceId}"]`);
      if (!block) continue;
      const ent = vehicle.entities;
      const statusObj = this._state(ent.transponder_status);
      const attrs = statusObj?.attributes || {};

      const detail = [attrs.plate, attrs.toll_category ? `${t.category} ${attrs.toll_category}` : null]
        .filter(Boolean)
        .join(" · ");
      block.querySelector(".vehName").textContent =
        vehicle.name + (detail ? ` — ${detail}` : "");

      const cells = block.querySelectorAll(".v[data-vk]");
      for (const cell of cells) {
        switch (cell.dataset.vk) {
          case "transponder_status":
            cell.textContent = this._fmt(ent.transponder_status);
            break;
          case "today":
            cell.textContent = `${this._fmt(ent.passes_today, "0")} · ${this._fmt(ent.cost_today)}`;
            break;
          case "month":
            cell.textContent = `${this._fmt(ent.passes_month, "0")} · ${this._fmt(ent.cost_month)}`;
            break;
          case "last_pass": {
            const passObj = this._state(ent.last_pass);
            cell.textContent =
              passObj && !["unknown", "unavailable"].includes(passObj.state)
                ? new Date(passObj.state).toLocaleString(this._hass.language)
                : "—";
            break;
          }
        }
      }
    }
  }

  /** Build the receipt markup. Split out so its values can be checked. */
  _receiptHtml(receipt) {
    const t = this._t;
    const locale = this._hass && this._hass.language === "el" ? "el-GR" : "en-GB";

    // A top-up is a credit in the operator's ledger, so the amount is negative.
    const total = Number(receipt.ChargeTotal);
    const amount = Number.isFinite(total)
      ? Math.abs(total).toLocaleString(locale, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }) + " \u20ac"
      : "\u2014";

    const stamp = receipt.LDateTime ? new Date(receipt.LDateTime) : null;
    const when = stamp && !isNaN(stamp) ? stamp.toLocaleString(locale) : "\u2014";
    const approved = receipt.BankAuthorizationStatusDB === "A";

    const rows = [
      [t.receiptAmount, amount],
      [t.receiptDate, when],
      [t.receiptCard, CARD_NAMES[receipt.PaymentCardType] || "\u2014"],
      [t.receiptStatus, approved ? t.receiptApproved : t.receiptDeclined],
      [t.receiptApproval, receipt.BankApprovalCode || "\u2014"],
      [t.receiptTxn, receipt.BankTransactionId || "\u2014"],
      [t.receiptOrder, receipt.ResponseOrderID || "\u2014", "id"],
    ];

    const esc = (value) =>
      String(value).replace(/[&<>"]/g, (ch) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch])
      );

    const html =
      '<!doctype html><html><head><meta charset="utf-8">' +
      "<title>" + esc(t.receiptTitle) + "</title><style>" +
      'body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;' +
      "background:#f4f4f4;color:#14140f}" +
      ".wrap{max-width:580px;margin:0 auto;padding:24px 18px}" +
      ".card{background:#fff;border-radius:12px;overflow:hidden;" +
      "box-shadow:0 1px 4px rgba(0,0,0,.15)}" +
      ".head{background:" + BRAND.navy + ";color:#fff;padding:14px 18px;" +
      "border-bottom:3px solid " + BRAND.yellow + ";font-weight:600}" +
      ".body{padding:18px}.big{font-size:32px;font-weight:700;margin:2px 0 16px}" +
      "table{width:100%;border-collapse:collapse;font-size:14px}" +
      "th,td{text-align:left;padding:7px 0;vertical-align:top;" +
      "border-bottom:1px solid #eee}" +
      "th{color:#666;font-weight:400;width:38%}" +
      "td{text-align:right;word-break:break-all}" +
      // The order id is a single token and reads as nonsense when split,
      // so it opts out of breaking and takes a smaller size to fit whole.
      "td.id{white-space:nowrap;word-break:normal;font-size:12px}" +
      ".note{font-size:12px;color:#666;margin-top:14px;line-height:1.45}" +
      ".actions{display:flex;gap:10px;margin-top:18px}" +
      "button{flex:1;padding:12px;border:none;border-radius:8px;background:" +
      BRAND.navy + ";color:#fff;font-size:14px;font-weight:600;cursor:pointer;" +
      "font-family:inherit}" +
      "button.secondary{background:#fff;color:" + BRAND.navy +
      ";border:1px solid #ccc}" +
      "@media print{.actions{display:none}body{background:#fff}" +
      ".card{box-shadow:none}}" +
      "</style></head><body><div class=\"wrap\"><div class=\"card\">" +
      '<div class="head">' + esc(t.receiptTitle) + "</div>" +
      '<div class="body"><div class="big">' + esc(amount) + "</div><table>" +
      rows
        .map(
          (pair) =>
            "<tr><th>" +
            esc(pair[0]) +
            "</th><td" +
            (pair[2] ? ' class="' + pair[2] + '"' : "") +
            ">" +
            esc(pair[1]) +
            "</td></tr>"
        )
        .join("") +
      '</table><div class="note">' + esc(t.receiptNote) +
      "<br>" + esc(t.receiptNoteTax) + "</div>" +
      '<div class="actions">' +
      '<button onclick="window.print()">' + esc(t.receiptPrint) + "</button>" +
      '<button class="secondary" onclick="window.close()">' +
      esc(t.receiptBack) + "</button>" +
      "</div></div></div></div></body></html>";

    return html;
  }

  /** Show the receipt in a window of its own, so it prints without the app. */
  _openReceipt(receipt) {
    const html = this._receiptHtml(receipt);
    const win = window.open("", "_blank", "width=660,height=820");
    if (!win) {
      // A blocked popup is not a missing receipt, and saying so would send the
      // reader looking in the wrong place.
      alert(this._t.receiptBlocked);
      return false;
    }
    win.document.write(html);
    win.document.close();
    return true;
  }

  _paintTopUp(host, ent) {
    const t = this._t;
    const select = host.querySelector(".cardSel");
    if (select) {
      const stateObj = this._state(ent.payment_card);
      const options = stateObj?.attributes?.options || [];
      const current = stateObj?.state;
      // Rebuild only when the options really changed, so an open dropdown is
      // not yanked away mid-choice.
      const asText = JSON.stringify(options);
      if (select.dataset.opts !== asText) {
        select.dataset.opts = asText;
        select.innerHTML = options
          .map((option) => `<option>${option}</option>`)
          .join("");
      }
      if (current && select.value !== current) select.value = current;
      select.disabled = !options.length;
    }

    const input = host.querySelector(".amtIn");
    if (input) {
      const stateObj = this._state(ent.topup_amount);
      if (document.activeElement !== input && stateObj) {
        // A number input cannot hold a decimal comma, so the value stays in the
        // machine format -- but two decimals read as money rather than "5.0".
        const amount = Number(stateObj.state);
        input.value = Number.isFinite(amount) ? amount.toFixed(2) : stateObj.state;
        input.min = stateObj.attributes?.min ?? 0;
        input.max = stateObj.attributes?.max ?? 5000;
      }
    }

    const receiptButton = host.querySelector(".receipt");
    if (receiptButton) {
      const state = this._state(ent.prepare_topup);
      receiptButton.hidden = !(state && state.attributes.last_order_id);
    }

    const box = host.querySelector("[data-linkbox]");
    if (!box) return;
    const button = this._state(ent.prepare_topup);
    const link = button?.attributes?.link;
    const available = button && button.state !== "unavailable";
    const prep = host.querySelector(".prep");
    if (prep) prep.disabled = !available;

    if (!available) {
      box.className = "warn";
      box.textContent = t.noCard;
      box.dataset.link = "";
    } else if (link) {
      box.className = "ok";
      // Rebuilt only when the link itself changes, so the running countdown and
      // a half-pressed cancel survive the state updates that arrive meanwhile.
      if (box.dataset.link !== link) {
        box.dataset.link = link;
        box.innerHTML =
          `<div class="linkHead">${t.linkReady}</div>` +
          `<a class="btnLink" href="${link}" target="_blank" rel="noopener">${t.linkOpen}</a>` +
          `<button class="secondary cancelLink" type="button">${t.linkCancel}</button>` +
          `<div class="countdown" data-expires="${button.attributes.link_expires || ""}"></div>`;
        box.querySelector(".cancelLink").addEventListener("click", (event) => {
          this._cancelLink(event.currentTarget, link);
        });
      }
      this._paintCountdown(box.querySelector(".countdown"));
    } else {
      box.dataset.link = "";
      // A cancel leaves nothing on screen otherwise: the link simply vanishes,
      // which looks the same as never having pressed anything. Shown briefly,
      // then cleared by the ticker -- no further state change is coming.
      const at = button?.attributes?.link_result_at || "";
      const cancelled = button?.attributes?.link_result === "cancelled";
      if (cancelled && at && Date.now() - new Date(at).getTime() < NOTE_MS) {
        if (box.dataset.note !== at) {
          box.dataset.note = at;
          box.className = "ok";
          box.textContent = t.linkCancelled;
        }
      } else if (box.dataset.note || box.textContent) {
        box.dataset.note = "";
        box.className = "";
        box.textContent = "";
      }
    }
  }

  /*
   * Drops the order server side.
   *
   * Posted to the path rather than to the attribute's absolute url: that url is
   * built from the external address so the browser could be talking to a
   * different origin, and this view answers no preflight. POST because the
   * cancel route refuses GET on purpose -- see payment.py.
   */
  async _cancelLink(trigger, link) {
    const t = this._t;
    trigger.disabled = true;
    trigger.textContent = t.linkCancelling;
    try {
      let path = link;
      try {
        path = new URL(link).pathname;
      } catch (err) {
        /* Already relative. */
      }
      await fetch(`${path}/cancel`, { method: "POST" });
    } catch (err) {
      trigger.disabled = false;
      trigger.textContent = t.linkCancel;
      return;
    }
    // The button entity forgets the link through the manager's watcher, which
    // pushes a state update; that clears this box on the next paint.
  }

  /* Ticks towards the same absolute instant the confirmation page counts to. */
  _paintCountdown(node) {
    if (!node) return;
    const t = this._t;
    const iso = node.dataset.expires;
    if (!iso) {
      node.textContent = "";
      return;
    }
    const left = Math.floor((new Date(iso).getTime() - Date.now()) / 1000);
    if (left <= 0) {
      node.className = "countdown low";
      node.innerHTML = t.linkExpired;
      return;
    }
    const mm = Math.floor(left / 60);
    const ss = left % 60;
    node.className = left <= 60 ? "countdown low" : "countdown";
    node.innerHTML = `${t.linkExpires} <b>${mm}:${ss < 10 ? "0" : ""}${ss}</b>`;
  }

  connectedCallback() {
    // The state only changes when the link appears or goes, so the countdown
    // needs its own heartbeat to move between those moments.
    this._ticker = setInterval(() => {
      const nodes = this.shadowRoot?.querySelectorAll(".countdown") || [];
      for (const node of nodes) this._paintCountdown(node);
      for (const box of this.shadowRoot?.querySelectorAll("[data-note]") || []) {
        const at = box.dataset.note;
        if (at && Date.now() - new Date(at).getTime() >= NOTE_MS) {
          box.dataset.note = "";
          box.className = "";
          box.textContent = "";
        }
      }
    }, 1000);
  }

  disconnectedCallback() {
    clearInterval(this._ticker);
    this._ticker = null;
  }
}

// Guarded because this module is loaded more than once in a session: it backs
// both the sidebar panel and the integration's own config panel, and the module
// url carries a cache-busting token that changes on upgrade, so the browser
// treats the new url as a separate module and runs it again. An unguarded
// define() throws there and takes the rest of the module with it.
if (!customElements.get("gr-epass-panel")) {
  customElements.define("gr-epass-panel", GrEpassPanel);
}
