# Changelog

Όλες οι αξιοσημείωτες αλλαγές καταγράφονται εδώ.
Η μορφή ακολουθεί το [Keep a Changelog](https://keepachangelog.com/el/1.1.0/)
και η αρίθμηση το [Semantic Versioning](https://semver.org/lang/el/).

All notable changes are documented here, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/).

<!--
Πώς αριθμούμε / How versions work
  MAJOR  1.0.0  σταθερό API entities. Όσο είμαστε σε 0.x μπορεί να αλλάξουν.
  MINOR  0.2.0  νέα entities ή λειτουργίες. Στο 0.x εδώ μπαίνουν και breaking.
  PATCH  0.1.1  διόρθωση χωρίς νέα entities.

Το `version` στο manifest.json πρέπει ΠΑΝΤΑ να ταιριάζει με το git tag χωρίς
το «v»: tag v0.2.0 -> manifest 0.2.0. Το HACS διαβάζει το manifest για την
έκδοση και το σώμα του GitHub Release για τις σημειώσεις.
-->

## [Unreleased]

## [0.2.0] — 2026-08-20

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Δική του σελίδα στο μενού του Home Assistant («e-PASS»). Εμφανίζεται μόλις
  προστεθεί το integration, χωρίς να φτιάξεις dashboard ή να γράψεις YAML, και
  ακολουθεί τη γλώσσα του χρήστη (ελληνικά ή αγγλικά).
- Στη σελίδα: υπόλοιπο με χρωματιστό δείκτη, στοιχεία συνδρομής, κινήσεις μήνα,
  τελευταία διέλευση, ανανέωση υπολοίπου και ξεχωριστή ενότητα ανά πομποδέκτη με
  κατηγορία οχήματος, διελεύσεις ημέρας/μήνα και τελευταία διέλευση.
- Δύο κολόνες σε οθόνη υπολογιστή, μία σε κινητό.

**Άλλαξαν**

- Το κουμπί ανανέωσης λέει πλέον «Προετοιμασία πληρωμής» και από κάτω εξηγεί ότι
  δεν χρεώνει: φτιάχνει σύνδεσμο μιας χρήσης που λήγει σε 10 λεπτά.
- Τα ποσά στα δύο πεδία αριθμού εμφανίζονται ως νόμισμα («12,00 €») αντί για
  «12.0 EUR».

**Διορθώθηκαν**

- Οι γραμμές ανά πομποδέκτη ήταν κενές. Η σελίδα εντόπιζε τα entities κόβοντας το
  entity_id, που δεν δουλεύει για τους πομποδέκτες επειδή το δικό τους id
  προέρχεται από την ονομασία τους. Πλέον χρησιμοποιεί το `translation_key`, που
  δεν αλλάζει ούτε αν μετονομάσεις entity.
- Ένας proxy με cache μπροστά από το Home Assistant (π.χ. Cloudflare, nginx)
  συνέχιζε να σερβίρει την προηγούμενη έκδοση της σελίδας μετά από αναβάθμιση.

### 🇬🇧 English

**Added**

- A dedicated page in the Home Assistant sidebar ("e-PASS"). It appears as soon
  as the integration is added — no dashboard to build, no YAML to write — and
  follows the user's language (Greek or English).
- The page shows the balance with a colour indicator, subscription details,
  this month's activity, the last pass, top-up controls, and a section per
  transponder with its vehicle category, passes today and this month, and its
  own last pass.
- Two columns on a desktop window, one on a phone.

**Changed**

- The top-up button now reads "Prepare payment" and states underneath that it
  charges nothing: it creates a single-use link that expires in 10 minutes.
- Both number fields render as currency ("12,00 €") instead of "12.0 EUR".

**Fixed**

- The per-transponder rows were empty. The page located entities by slicing the
  entity id apart, which never matched the transponder entities because theirs
  are slugged from the transponder alias. It now uses `translation_key`, which
  survives an entity rename.
- A caching proxy in front of Home Assistant (Cloudflare, nginx) kept serving
  the previous version of the page after an upgrade.

## [0.1.0] — 2026-08-20

Πρώτη δημόσια έκδοση.

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Παρακολούθηση συνδρομής my e-PASS: υπόλοιπο, κατάσταση υπολοίπου, τελευταία
  πληρωμή και εκκαθάριση, πλήθος πομποδεκτών, κατάσταση συνδρομής.
- Στατιστικά διελεύσεων και κόστους για σήμερα, τρέχοντα μήνα, κυλιόμενο
  30ήμερο και προηγούμενο μήνα — συνολικά και **ανά πομποδέκτη** (ξεχωριστό
  device για κάθε πομποδέκτη).
- Διαχωρισμός κόστους σε **Αττική Οδό** και **άλλα δίκτυα** μέσω
  διαλειτουργικότητας.
- Sensor τελευταίας διέλευσης με σταθμό, λωρίδα, ποσό και κατηγορία διοδίων
  στα attributes.
- **Όρια ανά κατηγορία οχήματος**, από τον επίσημο τιμοκατάλογο: κατώφλι
  ειδοποίησης χαμηλού υπολοίπου (`number`) και όριο άκυρου λογαριασμού
  (`sensor`), παραγόμενα από το `TollCategoryId` του πομποδέκτη. Δεν χρειάζεται
  να φτιάξετε helper.
- **Ανανέωση υπολοίπου με ένα tap**: επιλογή αποθηκευμένης κάρτας (`select`),
  ποσό (`number`) και κουμπί που ζητά υπογεγραμμένη εντολή. Παράγεται σύνδεσμος
  μιας χρήσης, με λήξη 10 λεπτά, που δείχνει ποσό και κάρτα πριν τη μεταφορά
  στην τράπεζα.
- Sensors για αποθηκευμένες κάρτες και πότε λήγει η πιο κοντινή.
- **Events** στο bus: `attiki_odos_epass_pass`,
  `attiki_odos_epass_balance_changed`, `attiki_odos_epass_payment_ready`.
- Config flow με επιλογή συνδρομής και πομποδεκτών, options flow για αλλαγή
  επιλογής και συχνότητας (10–1440 λεπτά), και reauth όταν αλλάξει ο κωδικός.
- Πλήρη ελληνικά και αγγλικά, diagnostics με απόκρυψη προσωπικών δεδομένων,
  δύο παραδείγματα dashboard και probe εργαλείο για έλεγχο του API.

**Γνωστοί περιορισμοί**

- Το backend απορρίπτει διαστήματα άνω των 30 ημερών· τα αιτήματα σπάνε
  αυτόματα, οπότε ένα refresh κάνει 3–5 κλήσεις.
- Η διάκριση «άλλα δίκτυα» βασίζεται στο `PlazaExternal = "Y"`, που είναι
  **επιβεβαιωμένο μόνο από τον κώδικα του SPA** και όχι από πραγματικά
  δεδομένα. Αν έχετε τέτοιες διελεύσεις και το νούμερο μένει 0, ανοίξτε issue.
- Η χρέωση ολοκληρώνεται πάντα σε σελίδα της τράπεζας — αυτόματη ανανέωση
  χωρίς άνθρωπο δεν είναι εφικτή από κανένα integration.
- Ο κωδικός αποθηκεύεται στο config entry, γιατί το API απαιτεί password grant
  σε κάθε νέο login.

### 🇬🇧 English

**Added**

- my e-PASS subscription monitoring: balance, balance status, last payment and
  statement, transponder count, account status.
- Pass and cost statistics for today, this month, a rolling 30 days and the
  previous month — account-wide and **per transponder** (one device each).
- Cost split between **Attiki Odos** and **other motorways** reached through
  interoperability.
- Last-pass sensor carrying plaza, lane, amount and toll category as attributes.
- **Per-vehicle-category limits** taken from the published price list: a
  low-balance warning threshold (`number`) and the no-pass limit (`sensor`),
  both derived from the transponder's `TollCategoryId`. No helper to create.
- **One-tap top-up**: stored-card picker (`select`), amount (`number`) and a
  button that requests a signed order. It publishes a single-use link, valid
  for 10 minutes, showing the amount and card before handing off to the bank.
- Sensors for stored cards and the soonest card expiry.
- **Bus events**: `attiki_odos_epass_pass`,
  `attiki_odos_epass_balance_changed`, `attiki_odos_epass_payment_ready`.
- Config flow with subscription and transponder selection, options flow for
  changing the selection and poll interval (10–1440 minutes), and reauth.
- Full Greek and English translations, diagnostics with personal data redacted,
  two dashboard examples and a probe tool for inspecting the API.

**Known limitations**

- The backend rejects ranges wider than 30 days; requests are chunked
  automatically, so one refresh makes 3–5 calls.
- The "other motorways" split relies on `PlazaExternal = "Y"`, which is
  **confirmed only from the SPA source**, not from observed data. If you have
  such passes and the figure stays 0, please open an issue.
- A charge always completes on the bank's own page — unattended automatic
  top-up is not possible from any integration.
- The password is stored in the config entry because the API requires a
  password grant for every fresh login.

[Unreleased]: https://github.com/VeZReVouLiS/attiki-odos-e-pass/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/VeZReVouLiS/attiki-odos-e-pass/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/VeZReVouLiS/attiki-odos-e-pass/releases/tag/v0.1.0
