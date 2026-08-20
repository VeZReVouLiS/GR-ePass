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

## [0.1.1] — 2026-08-20

### 🇬🇷 Ελληνικά

**Διορθώθηκε**

- Το `manifest.json` δεν δήλωνε την εξάρτηση από το `http`, που χρησιμοποιείται
  για τη σελίδα επιβεβαίωσης της ανανέωσης. Δεν επηρέαζε τη λειτουργία — το
  `http` φορτώνεται πάντα από το Home Assistant — αλλά απέτυπτε τον έλεγχο
  hassfest, που είναι προϋπόθεση για το HACS.

### 🇬🇧 English

**Fixed**

- `manifest.json` did not declare its dependency on `http`, used for the top-up
  confirmation page. Harmless at runtime, since `http` is always loaded, but it
  failed the hassfest check that HACS requires.

## [0.1.0] — 2026-08-19

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

[Unreleased]: https://github.com/VeZReVouLiS/attiki-odos-e-pass/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/VeZReVouLiS/attiki-odos-e-pass/releases/tag/v0.1.1
[0.1.0]: https://github.com/VeZReVouLiS/attiki-odos-e-pass/releases/tag/v0.1.0
