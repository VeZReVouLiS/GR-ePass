# Working on GR e-Pass

Orientation for anyone — human or agent — picking this repository up. Written in
English because every commit message, code comment and identifier here is, even
though the product itself ships Greek and English side by side.

---

## Rule zero: verify, never trust the notes

**This file, the changelog, the handoff note and every comment are claims about
the past. Check them against the repository and the running system before you act
on them.** Notes go stale silently; code does not.

This is not a platitude. Both of these happened:

- A handoff note listed "next task: rename the network sensor" as not started. It
  had shipped six days earlier, in 0.8.0. An agent that trusted the note would
  have rewritten working code.
- `git status` reported `main...origin/main` with no divergence while the clone was
  **nine commits and eight releases behind**. The remote-tracking ref was stale and
  nothing said so. `git fetch` first, always; if fetch errors, treat every
  comparison against `origin/*` as unknown rather than equal.

So, at the start of a session:

```bash
git fetch --tags origin && git status --short --branch
git log --oneline -8
python -c "import json;print(json.load(open('custom_components/gr_epass/manifest.json'))['version'])"
```

Then compare against what is actually installed and running, not against what a
document says is running.

---

## What this is

A Home Assistant custom integration for Greek prepaid toll accounts (**my
e-PASS**), supporting **Nea Attiki Odos** and **Nea Egnatia Odos / EgnatiaPass**.
It is unofficial: **there is no public API**, and every endpoint was derived from
the operators' own Angular bundle. They can change without notice.

Two consequences worth holding onto:

1. **Field names are observations, not contracts.** When something reads wrong,
   confirm what the API actually returns before changing logic — see
   `tools/epass_probe.py`.
2. **The integration never charges anything.** Home Assistant cannot: the backend
   only *signs* an order and the money moves on the bank's own hosted page. Any
   change near payment must preserve that a human clicks last.

---

## Layout

```
custom_components/gr_epass/
  api.py          OAuth2 client. Token refresh, chunked activity fetch (30-day cap).
  coordinator.py  Polls, folds transactions into the statistics the entities read.
  statistics.py   Long-run history the API does not keep. Idempotent day records.
  sensor.py       Every sensor. Entity descriptions with value functions.
  number.py       Top-up amount, low-balance threshold.
  select.py       Stored-card picker.
  button.py       Prepare top-up. Publishes the single-use link and its outcome.
  payment.py      Order signing, the one-shot link, and the pages behind it.
  notifier.py     Sends the payment link out, when asked to.
  panel.py        Registers the sidebar page and serves its module.
  panel/gr-epass-panel.js   The page itself. Plain custom element, no build step.
  operators.py    Per-operator constants: portal urls, colours, published limits.
  entity.py       Shared device info. Identifiers must stay byte-identical.
  services.py     Service handlers, with services.yaml describing them.
  const.py        Domain, enum maps taken from the portal's own JavaScript.
  strings.json + translations/{el,en}.json   All user-visible entity text.
  brand/          The icon Home Assistant serves for this integration.

docs/OPERATORS.md    Which operators work, which do not, and why.
docs/PAYMENT_API.md  The reverse-engineered payment flow in detail.
docs/SECURITY.md     Where the password lives, what is exposed, what is not.
tools/               Development helpers. Not shipped, no release needed.
```

`README.md` is Greek, `README.en.md` is English, and **both** are user-facing.

---

## Checks to run before committing

There is no test suite and no linter wired up. There are four targeted checks,
each written because something specific broke:

```bash
python tools/jscheck.py custom_components/gr_epass/panel/gr-epass-panel.js
python tools/shadowcheck.py
python tools/stats_check.py
python -m py_compile custom_components/gr_epass/*.py
```

- **`jscheck.py`** — the panel script is served to the browser as-is, so one
  unbalanced brace takes down the whole page, and there is usually no `node`
  available. Run it after every edit to the panel.
- **`shadowcheck.py`** — an attribute that shadows a method of the same name is
  legal Python, imports cleanly, passes linters, and then fails at runtime. That
  is how the top-up button broke in 0.10.0.
- **`stats_check.py`** — the coordinator re-fetches the same thirty days on every
  refresh, so folding the same window twice must not change the totals.

CI runs **hassfest** and the **HACS action** on every push, tag and daily cron.
Both check rules that shift over time, so a repository nobody touched can start
failing without a commit.

---

## Releasing

Tag pushes are the whole ritual. `.github/workflows/release.yml` builds the GitHub
Release itself, taking the body from this version's `CHANGELOG.md` section, and
**refuses to publish when the manifest version and the tag disagree**.

```bash
# 1. bump custom_components/gr_epass/manifest.json
# 2. add the CHANGELOG section and its link reference
git add -- <files> && git commit
git tag -a vX.Y.Z -m "GR e-Pass X.Y.Z - short summary"
git push origin main && git push origin vX.Y.Z
```

**HACS reads the README from the release, not from the branch.** Documentation
that sits only on `main` is invisible to everyone installing or browsing the
store. A docs-only commit therefore still gets a patch release — which is cheap,
since the workflow does the work. Changes under `tools/` are the exception:
nothing user-facing moves, so no release.

Versioning: `MINOR` for new entities or features and for anything that changes
entity naming, `PATCH` for fixes and documentation. While on `0.x`, breaking
changes may land in a MINOR — say so loudly in the changelog when they do.

Re-pushing a tag is supported: the workflow edits the existing release rather than
failing, which is the way to correct release notes that have already gone out.

---

## Conventions that are not obvious

**Greek is written, not translated.** Not word-for-word from English. Three
calques reached releases before being caught: *known gap* → «Γνωστό ξεμείνει»
(meaningless; «Γνωστό ζήτημα»), *own network* → «Δικό δίκτυο» (a fragment;
«Δίκτυο παρόχου»), and a «μπώναρε» that is not a word in any language. If a Greek
sentence does not stand up read aloud, it does not ship.

**Release notes are for users.** Internal backlog, TODOs and notes-to-ourselves
belong in the private handoff, never in `CHANGELOG.md`.

**Behaviour changes update both READMEs in the same commit.** A reader following
the docs should never be told the old behaviour.

**Entity ids come from the English name**, whatever language Home Assistant runs
in, and the device name prefixes them. Renaming an entity therefore changes its id
for *new* installations while existing ones keep theirs, because the registry
holds the original. Both states then exist in the wild — document it.

**The operator is not hardcoded.** Anything naming a road network reads it from the
entry's operator. A subscriber to one operator must never see the other's name.

**No operator or bank logo, anywhere.** Those are registered marks and this
integration is unofficial; borrowing one reads as endorsement. Operator *colours*
are used instead, which is not trademark use.

---

## Screenshots

Do not photograph a real subscription and clean it afterwards. Cleaning pixels is
error-prone and has to be redone whenever the layout moves.

```bash
python tools/panel_preview.py                  # both languages
python tools/panel_preview.py --lang el
python tools/panel_preview.py --state link     # a prepared payment link
python tools/panel_preview.py --state receipt  # after a payment
```

This renders the real component against a fabricated Home Assistant, so the
result never contains anything real. Output goes to `docs/images/`.

---

## Platform notes

The project is worked on from Windows and macOS, and the Home Assistant instance
is reachable from some machines and not others. **Which machine can reach what is
recorded in the private handoff, not here.**

### Windows

- **Do not keep this repository inside a cloud-synced folder.** It was in OneDrive
  and broke twice: commits failed with `unable to append to .git/logs/refs/heads/main`
  (worked around by `git config windows.appendAtomically false`), and later
  OneDrive dehydrated 152 files inside `.git`, after which `git fetch` died with
  `mmap failed: Invalid argument` — because `mmap` on a cloud placeholder returns
  `EINVAL`, and the sync engine then refused to rehydrate them. Git already syncs
  across machines through GitHub; a second sync engine over the same `.git` adds
  nothing and can corrupt it. Keep the clone on local disk.
- The shell available may be Git Bash. **Heredocs break on content containing
  `\u` escapes or apostrophes** — write a patch script to a file and run it
  instead of piping it in.
- Greek output needs `PYTHONIOENCODING=utf-8`, or printing raises
  `UnicodeEncodeError` under the cp1253 console.
- `winget` may exist without administrator rights; user-scope `pip install --user`
  works.

### macOS and Linux

- No known quirks. Standard shell, standard git.
- `python3` rather than `python` on some setups.

### Both

- `Pillow` and `pypdf` are needed only by some tools and are **not** declared
  anywhere. Install them per machine when a tool asks: `pip install --user Pillow pypdf`.
- The integration itself has **no Python dependencies** — `manifest.json` lists
  none, deliberately.

---

## What is not in this repository

There is a **private handoff note kept outside the repo**, deliberately never
committed, because it holds the owner's account identifiers, host names, network
addresses and key locations. It carries current state, open questions and
decisions already taken.

**Ask the owner for it at the start of a session, and read it before planning
anything** — then verify it, per rule zero. If a claim in it conflicts with the
repository or the running system, the note is the thing that is wrong.

Nothing personal belongs in this repository. Before committing, it is worth
grepping a diff for account numbers, host names, addresses and card digits.
