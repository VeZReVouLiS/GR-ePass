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

## [0.8.0] — 2026-08-27

### 🇬🇷 Ελληνικά

**Άλλαξαν**

- Ο αισθητήρας κόστους στο δικό σου δίκτυο λέει πλέον **ποιο** δίκτυο είναι:
  «Κόστος διελεύσεων μήνα (Αττική Οδός)» ή «(Εγνατία Οδός)», ανάλογα με τον
  πάροχο της συνδρομής. Πριν έλεγε πάντα «Αττική Οδός», ακόμη και σε συνδρομή
  Εγνατίας — και με δύο συνδρομές δύο αισθητήρες θα έλεγαν το ίδιο πράγμα.
- **Όλα τα ελληνικά κείμενα σε ενικό.** Το integration μιλά πλέον στον ενικό
  αντί στον πληθυντικό ευγενείας, σε README, μηνύματα ρύθμισης και σφάλματα.

**Τι σημαίνει για υπάρχουσες εγκαταστάσεις**

Το entity id **δεν αλλάζει** — αλλάζει μόνο το εμφανιζόμενο όνομα, οπότε
αυτοματισμοί και κάρτες συνεχίζουν. Σε νέα εγκατάσταση Εγνατίας το id θα βγει
`..._cost_this_month_egnatia_odos` αντί `..._attiki_odos`. Το εσωτερικό
`unique_id` έμεινε σκόπιμα ίδιο, ώστε να μη χαθεί κανένα entity.

### 🇬🇧 English

**Changed**

- The own-network cost sensor now says **which** network it counts: "Cost this
  month (Attiki Odos)" or "(Egnatia Odos)", following the subscription's
  operator. It used to say Attiki Odos on every subscription, including Egnatia
  ones — and with two subscriptions two sensors would have claimed the same
  network while measuring different ones.
- **All Greek text moved to the singular**, the informal form, across the README,
  the setup prompts and the error messages.

**What it means for existing installations**

The entity id does **not** change — only the displayed name does, so automations
and cards keep working. A new Egnatia installation gets
`..._cost_this_month_egnatia_odos` instead of `..._attiki_odos`. The internal
`unique_id` was deliberately left alone so no entity is orphaned.

## [0.7.1] — 2026-08-21

### 🇬🇷 Ελληνικά

**Διορθώθηκαν**

- Η τεκμηρίωση έλεγε ότι ο σύνδεσμος πληρωμής «στέλνεται με Telegram». Δεν
  στέλνεται πουθενά: εμφανίζεται στη σελίδα GR e-Pass και τον ανοίγετε ή τον
  προωθείτε εσείς. Η αγγλική τεκμηρίωση είχε ήδη διορθωθεί, η ελληνική όχι.
- Ο σχεδιασμός δεν αλλάζει, και ο λόγος του παραμένει ο ίδιος: ο σύνδεσμος είναι
  χωρίς authentication ώστε να ανοίγει **μακριά** από το Home Assistant, οπότε η
  γλώσσα του διαβάζεται από τον browser του αναγνώστη και η ακύρωση δέχεται μόνο
  POST.

### 🇬🇧 English

**Fixed**

- The documentation said the payment link "is sent over Telegram". It is not sent
  anywhere: it appears on the GR e-Pass page and you open or forward it yourself.
  The English text had already been corrected; the Greek had not.
- Nothing about the design changes, and its reasoning stands: the link is
  unauthenticated so it can be opened **away** from Home Assistant, which is why
  its language comes from the reader's browser and why cancelling is POST only.

## [0.7.0] — 2026-08-21

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Οι σελίδες του συνδέσμου πληρωμής — επιβεβαίωση, ακύρωση, λήξη, μεταφορά στην
  τράπεζα — υπάρχουν πλέον **και στα αγγλικά**. Ήταν όλες μόνο στα ελληνικά, οπότε
  όποιος δούλευε το Home Assistant στα αγγλικά έβλεπε ελληνικά τη στιγμή που
  επιβεβαίωνε μια χρέωση.

**Άλλαξαν**

- Ο **κωδικός παραγγελίας** στην απόδειξη χωράει σε μία σειρά. Έσπαγε στη μέση,
  και ένας κωδικός κομμένος σε δύο γραμμές δεν διαβάζεται ούτε αντιγράφεται.
- Η σημείωση της απόδειξης χωρίστηκε: το «Δεν αντικαθιστά φορολογικό
  παραστατικό.» ξεκινά τη δική του γραμμή.

**Πώς επιλέγεται η γλώσσα**

Από το `Accept-Language` του browser που ανοίγει τη σελίδα, όχι από τη γλώσσα του
Home Assistant — ο σύνδεσμος στέλνεται με Telegram και ανοίγει σε άλλη συσκευή.
Αν ο browser δεν ζητά ούτε ελληνικά ούτε αγγλικά, χρησιμοποιείται η γλώσσα που
έτρεχε το Home Assistant όταν υπογράφηκε η εντολή.

### 🇬🇧 English

**Added**

- The payment link's pages — confirm, cancelled, expired, hand-off — now exist
  **in English** as well. All four were Greek only, so anyone running Home
  Assistant in English met Greek at the moment of confirming a charge.

**Changed**

- The **order id** on the receipt fits on one line. It used to break mid-string,
  and an identifier split across two lines can be neither read nor copied.
- The receipt's note is split in two: "It is not a tax document." starts its own
  line.

**How the language is chosen**

From the `Accept-Language` of the browser opening the page rather than the Home
Assistant language, because the link is sent over Telegram and opened on another
device. If the browser asks for neither Greek nor English, the language Home
Assistant was running in when the order was signed is used.

## [0.6.5] — 2026-08-21

### 🇬🇷 Ελληνικά

**Διορθώθηκαν**

- Το μήνυμα όταν ο browser εμποδίζει το παράθυρο της απόδειξης έγραφε
  «**μπώναρε**», που δεν είναι λέξη. Πλέον «μπλόκαρε».
- Η γραμμή δικτύου για πάροχο που δεν αναγνωρίζεται έγραφε «**Δικό δίκτυο**»,
  χωρίς άρθρο και χωρίς νόημα. Πλέον «Δίκτυο παρόχου».

### 🇬🇧 English

**Fixed**

- Two Greek strings that were not idiomatic Greek: the message shown when the
  browser blocks the receipt window used a non-existent word, and the network row
  for an unrecognised operator read as a fragment. Both rewritten. The English
  side is unchanged.

## [0.6.4] — 2026-08-21

Τεκμηρίωση μόνο. Ο κώδικας είναι πανομοιότυπος με το 0.6.3.
Documentation only. The code is identical to 0.6.3.

### 🇬🇷 Ελληνικά

- Τα δύο READMEs καλύπτουν πλέον την **ακύρωση** (και από τα δύο σημεία, και ότι
  σβήνει την εντολή από τον server), την **αντίστροφη μέτρηση** και γιατί
  συμφωνούν οι δύο μετρητές, τα attributes `link_expires`, `link_result` και
  `link_result_at`, ότι το endpoint ακύρωσης δέχεται **μόνο POST** και γιατί, και
  ότι η σελίδα πιάνει όλο το πλάτος με γραμματοσειρά που κλιμακώνεται.

### 🇬🇧 English

- Both READMEs now cover **cancelling** (from either place, and that it drops the
  order server side), the **countdown** and why the two agree, the `link_expires`,
  `link_result` and `link_result_at` attributes, that the cancel endpoint is
  **POST only** and why, and that the page takes the full width with type that
  scales.

## [0.6.3] — 2026-08-21

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Μετά την ακύρωση, η σελίδα GR e-Pass **το λέει**: «Η συναλλαγή ακυρώθηκε. Δεν
  έγινε καμία χρέωση.» για δώδεκα δευτερόλεπτα. Πριν, ο σύνδεσμος απλώς
  εξαφανιζόταν — που έμοιαζε ακριβώς σαν να μην είχες πατήσει τίποτα. Λειτουργεί
  και για τους δύο δρόμους ακύρωσης, από τη σελίδα και από το κουμπί.
- Το `button.*_prepare_top_up` δημοσιεύει `link_result` («used», «cancelled» ή
  «expired») και `link_result_at`, ώστε να μπορεί να χτιστεί αυτοματισμός πάνω
  στο τι απέγινε μια εντολή.

**Γιατί χρειάστηκε**

Ο μηχανισμός που ειδοποιεί για μια εντολή που έκλεισε δεν έλεγε **γιατί** έκλεισε:
χρήση, ακύρωση και λήξη κατέληγαν στην ίδια σιωπηλή διαγραφή του συνδέσμου. Πλέον
ο λόγος περνά μέχρι την οντότητα.

### 🇬🇧 English

**Added**

- After a cancel the GR e-Pass page **says so**: "The transaction was cancelled.
  Nothing was charged." for twelve seconds. Before, the link just vanished, which
  looked exactly like never having pressed anything. Works for both cancel paths,
  from the page and from the button.
- `button.*_prepare_top_up` publishes `link_result` ("used", "cancelled" or
  "expired") and `link_result_at`, so an automation can react to how an order
  ended.

**Why it was needed**

The mechanism that reports a closed order did not say **why** it closed: used,
cancelled and expired all ended in the same silent removal of the link. The
reason now travels all the way to the entity.

## [0.6.2] — 2026-08-21

### 🇬🇷 Ελληνικά

**Διορθώθηκαν**

- Στις **Κινήσεις** η γραμμή του δικτύου έλεγε πάντα «Αττική Οδός», ακόμη και σε
  συνδρομή Εγνατίας. Πλέον ονομάζεται με τον πάροχο που διάλεξες: το **δικό σου**
  δίκτυο είναι η επώνυμη γραμμή, και ό,τι άλλο μέσω διαλειτουργικότητας μπαίνει
  στα «Άλλα δίκτυα». Σε άγνωστο πάροχο γράφει «Δικό δίκτυο» αντί να μαντεύει.

**Άλλαξαν**

- Η κάρτα πιάνει **όλο το διαθέσιμο πλάτος** αντί να σταματά σε σταθερό όριο, και
  η **γραμματοσειρά μεγαλώνει μαζί με το παράθυρο**: μία βάση `clamp(14px, …,
  20px)` και όλα τα μεγέθη μέσα σε `em`, ώστε ο κύκλος του υπολοίπου, τα εικονίδια
  και τα κείμενα να κλιμακώνονται μαζί. Στο κινητό η βάση πέφτει στα 14px, δηλαδή
  ακριβώς όπως ήταν.

### 🇬🇧 English

**Fixed**

- The network row under **Activity** always read "Attiki Odos", even on an
  Egnatia subscription. It is now named after the operator you picked: **your
  own** network is the named row, and anything reached through interoperability
  goes under "Other networks". An operator this build does not know reads "Own
  network" rather than guessing.

**Changed**

- The card takes **all the width available** instead of stopping at a fixed cap,
  and the **type scales with the window**: one base of `clamp(14px, …, 20px)` with
  every size inside expressed in `em`, so the balance ring, the icons and the text
  grow together. On a phone the base lands at 14px, exactly what it was.

## [0.6.1] — 2026-08-21

### 🇬🇷 Ελληνικά

**Διορθώθηκαν**

- **Η ακύρωση από τη σελίδα πληρωμής δεν ακύρωνε τίποτα.** Η φόρμα είχε σχετικό
  `action='cancel'`, που κατά τους κανόνες των σχετικών URL **αντικαθιστά το
  τελευταίο κομμάτι** της διαδρομής: αντί για `…/pay/<nonce>/cancel` έστελνε σε
  `…/pay/cancel`, δηλαδή στο κανονικό view με nonce «cancel». Αποτέλεσμα: έβγαινε
  «Ο σύνδεσμος δεν ισχύει πλέον» ενώ **η εντολή έμενε ζωντανή** και ο σύνδεσμος
  δούλευε κανονικά. Πλέον η φόρμα δείχνει σε απόλυτη διαδρομή.

**Άλλαξαν**

- Η σελίδα επιβεβαίωσης μεγάλωσε: 560px αντί 420, βασική γραμματοσειρά 17px, και
  όλα τα μεγέθη μέσα της υπολογίζονται από αυτήν αντί να είναι σταθερά.
- Στη σελίδα GR e-Pass ο σύνδεσμος και η ακύρωση έγιναν **κουμπιά πλήρους
  πλάτους**, στοιχισμένα με τα υπόλοιπα της κάρτας, με την αντίστροφη μέτρηση
  κεντραρισμένη από κάτω. Πριν ήταν δύο links στη σειρά, με το ένα υπογραμμισμένο.
- Οι σελίδες «ακυρώθηκε» και «δεν ισχύει πλέον» **κλείνουν μόνες τους σε 15
  δευτερόλεπτα** και έχουν κουμπί «Κλείσιμο». Αν το πρόγραμμα περιήγησης αρνηθεί
  να κλείσει την καρτέλα — συνηθισμένο όταν δεν την άνοιξε script — το λέει,
  αντί να σε στείλει σε φόρμα εισόδου: ένας σύνδεσμος που άνοιξε από Telegram σε
  κινητό δεν έχει session στο Home Assistant.
- Σε οθόνες από 1500px και πάνω η κάρτα φτάνει τα 1480px.

### 🇬🇧 English

**Fixed**

- **Cancelling from the payment page cancelled nothing.** The form used a
  relative `action='cancel'`, and relative urls **replace the last path
  segment**: it posted to `…/pay/cancel` instead of `…/pay/<nonce>/cancel`,
  landing on the normal view with "cancel" as the nonce. You were told the link
  had expired while **the order stayed live** and the link still worked. The form
  now posts to an absolute path.

**Changed**

- The confirmation page got bigger: 560px instead of 420, a 17px base font, and
  every size inside it derived from that rather than fixed.
- On the GR e-Pass page the link and the cancel are now **full-width buttons**,
  aligned with the rest of the card, with the countdown centred underneath.
  Before they sat side by side as links, one of them underlined.
- The "cancelled" and "no longer valid" pages **close themselves after 15
  seconds** and carry a Close button. If the browser refuses to close the tab —
  usual when a script did not open it — they say so rather than redirecting: a
  link opened from Telegram on a phone has no Home Assistant session and would
  land on a login form.
- From 1500px of window the card reaches 1480px.

## [0.6.0] — 2026-08-21

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- **Ακύρωση συναλλαγής**, σε δύο σημεία: στη σελίδα GR e-Pass δίπλα στον
  σύνδεσμο, και μέσα στην ίδια τη σελίδα επιβεβαίωσης. Η ακύρωση **σβήνει την
  εντολή από τον server** — ο σύνδεσμος παύει να ισχύει την ίδια στιγμή, δεν
  κρύβεται απλώς το κουμπί. Δεύτερο πάτημα ή ήδη ληγμένος σύνδεσμος δείχνουν το
  ίδιο μήνυμα, όχι σφάλμα.
- **Αντίστροφη μέτρηση** στα ίδια δύο σημεία. Κάτω από ένα λεπτό γίνεται κόκκινη·
  στο μηδέν το κουμπί χρέωσης απενεργοποιείται.

**Άλλαξαν**

- Η κάρτα ακολουθεί το πλάτος του παραθύρου αντί να σταματά στα 1040px:
  `min(94vw, 1260px)`. Το όριο υπάρχει επειδή κάθε γραμμή βάζει την ετικέτα
  αριστερά και την τιμή δεξιά — πάνω από ~600px στήλης οι δύο απομακρύνονται
  τόσο που παύουν να διαβάζονται ως ζευγάρι. Στο κινητό δεν αλλάζει τίποτα.

**Γιατί οι δύο μετρητές συμφωνούν**

Η σελίδα επιβεβαίωσης παίρνει τα **δευτερόλεπτα που απομένουν υπολογισμένα από
τον server** τη στιγμή που φορτώνει, αντί να μετράει προς μια απόλυτη ώρα: ένα
κινητό με στραβό ρολόι θα έδειχνε αλλιώς από το Home Assistant για την ίδια
εντολή. Άρα αν η σελίδα GR e-Pass λέει 5 λεπτά, το ίδιο θα πει και ο σύνδεσμος.

**Σημείωση ασφάλειας**

Το endpoint ακύρωσης δέχεται **μόνο POST**. Οι εφαρμογές συνομιλίας κατεβάζουν
τους συνδέσμους για να φτιάξουν preview· ένα cancel που απαντούσε σε GET θα
ακύρωνε την εντολή μόνο του, πριν πατήσει κανείς τίποτα.

### 🇬🇧 English

**Added**

- **Cancel the transaction**, in two places: on the GR e-Pass page next to the
  link, and inside the confirmation page itself. Cancelling **drops the order
  server side** — the link stops working at that moment rather than the button
  merely being hidden. A second press, or an already expired link, reads as
  cancelled rather than as an error.
- **A countdown** in those same two places. It turns red under a minute, and at
  zero the charge button is disabled.

**Changed**

- The card follows the window width instead of stopping at 1040px:
  `min(94vw, 1260px)`. The cap stays because each row puts its label left and its
  value right, and past roughly 600px of column the two drift so far apart that
  the pair stops reading as one line. Nothing changes on a phone.

**Why the two counters agree**

The confirmation page is handed the **remaining seconds as the server computed
them** when it loaded, rather than counting towards an absolute time: a phone
with a skewed clock would otherwise disagree with Home Assistant about the very
same order. So if the GR e-Pass page says five minutes, the link says five too.

**A note on safety**

The cancel endpoint accepts **POST only**. Chat apps fetch links to build their
previews, and a cancel that answered GET would throw the order away by itself,
before anyone tapped anything.

## [0.5.3] — 2026-08-21

Περιέχει τα 0.5.1 και 0.5.2, που δεν έφτασαν ποτέ σε release.
Includes 0.5.1 and 0.5.2, which never reached a release.

### 🇬🇷 Ελληνικά

**Διορθώθηκαν**

- Οι 0.5.1 και 0.5.2 είχαν tag αλλά **κανένα GitHub Release**. Το HACS διαβάζει
  releases, όχι tags: δεν εμφανιζόταν αναβάθμιση και η καρτέλα στο store
  συνέχιζε να δείχνει το README του 0.5.0, με τις εικόνες σπασμένες. Το release
  φτιάχνεται πλέον **αυτόματα** με το push του tag, με σώμα την αντίστοιχη
  ενότητα αυτού του αρχείου.
- Ένας έλεγχος σταματά το release αν το `version` του manifest δεν ταιριάζει με
  το tag — ήταν ο εύκολος τρόπος να δείχνει το store άλλη έκδοση από το
  integration.

### 🇬🇧 English

**Fixed**

- 0.5.1 and 0.5.2 were tagged but had **no GitHub Release**. HACS reads releases
  rather than tags, so no update ever appeared and the store card kept showing
  the 0.5.0 README with its images broken. The release is now created
  **automatically** when the tag is pushed, with this file's matching section as
  its body.
- A guard fails the release when the manifest `version` disagrees with the tag —
  the easy way to end up with the store showing one version and the integration
  another.

## [0.5.2] — 2026-08-21

### 🇬🇷 Ελληνικά

**Άλλαξαν**

- Το εμφανιζόμενο όνομα γράφεται πλέον **GR e-Pass**.
- Η σελίδα στο μενού λέγεται **GR e-Pass** αντί «e-PASS». Το πρόθεμα ξεχωρίζει
  τους ελληνικούς παρόχους, ώστε να υπάρχει χώρος αν προστεθούν κάποτε πάροχοι
  εκτός Ελλάδας.

Το `e-PASS` μένει ως έχει όπου αναφέρεται στο **προϊόν των παρόχων** («my
e-PASS», «συνδρομή e-PASS») — έτσι το γράφουν οι ίδιοι.

Τα entity ids **δεν αλλάζουν**: παράγονται από το όνομα της συσκευής, που
παραμένει `e-PASS <κωδικός>`. Ούτε η διεύθυνση της σελίδας αλλάζει, παραμένει
`/gr_epass` — αλλάζει μόνο η ετικέτα στο μενού.

### 🇬🇧 English

**Changed**

- The display name is now spelled **GR e-Pass**.
- The sidebar page is called **GR e-Pass** rather than "e-PASS". The prefix marks
  these as the Greek operators, leaving room for operators outside Greece later.

`e-PASS` is left alone wherever it refers to the **operators' own product** ("my
e-PASS", "e-PASS subscription") — that is how they spell it.

Entity ids **do not change**: they come from the device name, which stays
`e-PASS <account id>`. The page url is unchanged too, still `/gr_epass`; only the
sidebar label moves.

## [0.5.1] — 2026-08-21

Έκδοση μόνο τεκμηρίωσης. Ο κώδικας είναι πανομοιότυπος με το 0.5.0.
Documentation only. The code is identical to 0.5.0.

### 🇬🇷 Ελληνικά

**Διορθώθηκαν**

- Στο HACS δεν εμφανιζόταν καμία εικόνα και οι οδηγίες έμεναν παλιές όσο κι αν
  πατούσες «Update information». Αιτία: το HACS διαβάζει το README από το
  **release**, όχι από το `main`, και όλες οι διορθώσεις των εικόνων είχαν γίνει
  μετά το tag του 0.5.0. Το README εκείνου του release έδειχνε ακόμη
  `<img src="docs/images/…">` — σχετική διαδρομή μέσα σε HTML, που ο
  `ha-markdown` αφαιρεί και που λύνεται πάνω στον host του Home Assistant αντί
  στο GitHub — και ανέφερε μια εικόνα που είχε αποσυρθεί.
- Τα βήματα της εγκατάστασης ήταν κάτω από τη χειροκίνητη εγκατάσταση και
  ξεκινούσαν από το όνομα χρήστη, χωρίς να αναφέρουν καθόλου ότι πρώτα διαλέγεις
  πάροχο. Ανέβηκαν στην αρχή, με τη σωστή σειρά και με τις εικόνες μαζί.
- Οι σύνδεσμοι σύγκρισης εκδόσεων στο τέλος αυτού του αρχείου έδειχναν στο παλιό
  όνομα του repository, οπότε ήταν όλοι νεκροί.

### 🇬🇧 English

**Fixed**

- No image showed in HACS and the instructions stayed stale no matter how often
  you pressed "Update information". HACS reads the README from the **release**,
  not from `main`, and every image fix had landed after the 0.5.0 tag. That
  release's README still used `<img src="docs/images/…">` — a relative path
  inside HTML, which `ha-markdown` strips and which resolves against the Home
  Assistant host rather than GitHub — and referenced a screenshot since retired.
- The setup steps sat below the manual-install section and opened with the
  username, never mentioning that an operator is picked first. They now lead the
  page, in the right order, with the screenshots alongside.
- The version-comparison links at the foot of this file pointed at the
  repository's old name, so every one of them was dead.

## [0.5.0] — 2026-08-20

### ⚠️ Breaking

Το integration μετονομάστηκε από `attiki_odos_epass` σε **`gr_epass`**, γιατί δεν
αφορά πλέον έναν πάροχο. Το Home Assistant δεν μεταφέρει ρυθμίσεις μεταξύ
domain, οπότε:

1. Ρυθμίσεις → Συσκευές & Υπηρεσίες → αφαίρεσε το παλιό «Attiki Odos e-Pass».
2. Πρόσθεσε το **GR e-PASS** και διάλεξε πάροχο.

Τα entity ids παράγονται από το όνομα της συσκευής, όχι από το domain, οπότε
συνήθως επανέρχονται ίδια (`sensor.e_pass_<κωδικός>_balance`) και οι αυτοματισμοί
συνεχίζουν. Άλλαξαν όμως: η υπηρεσία σε `gr_epass.get_receipt`, τα events σε
`gr_epass_*`, και η διεύθυνση της σελίδας σε `/gr_epass`.

The integration was renamed from `attiki_odos_epass` to **`gr_epass`** — it is no
longer about one operator. Home Assistant does not migrate configuration between
domains, so remove the old entry and add **GR e-PASS**, picking your operator.
Entity ids come from the device name rather than the domain, so they usually come
back identical and automations keep working. The service is now
`gr_epass.get_receipt`, events are `gr_epass_*`, and the page lives at
`/gr_epass`.

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Υποστήριξη **πολλών παρόχων**. Κατά την προσθήκη διαλέγεις πάροχο· τα
  διαπιστευτήρια αφορούν το portal του καθενός.
- **Νέα Εγνατία Οδός** (EgnatiaPass, `myegnatiapass.gr`) δίπλα στη **Νέα Αττική
  Οδό**. Οι δύο εγκαταστάσεις συγκρίθηκαν πεδίο προς πεδίο: ίδιος client, ίδια
  δεκατρία API controllers, ίδια endpoints, και `clientConfig.json` που διαφέρουν
  μόνο στο branding.
- Κάθε κάρτα στη σελίδα παίρνει τα χρώματα του παρόχου της, ώστε δύο συνδρομές
  από διαφορετικούς παρόχους να ξεχωρίζουν με μια ματιά. Το κουμπί «Άνοιγμα my
  e-PASS» πηγαίνει στο σωστό portal.

**Άλλαξαν**

- Τα δημοσιευμένα όρια ανά κατηγορία οχήματος δεν είναι πλέον σταθερά του
  κώδικα· ανήκουν στον πάροχο.

**Γνωστός περιορισμός**

Τα όρια της **Εγνατίας δεν έχουν καταχωρηθεί**. Δεν δημοσιεύονται σε προσβάσιμη
σελίδα και δεν έρχονται από το API — είναι δεδομένα τιμοκαταλόγου. Αντί να
μπουν εικασίες, ο πάροχος δηλώνει «χωρίς όρια»: το «Όριο άκυρου λογαριασμού»
μένει κενό και το προεπιλεγμένο όριο ειδοποίησης είναι ένα ουδέτερο ποσό που
ορίζεις εσύ. Τα όρια της Αττικής Οδού παραμένουν από τον τιμοκατάλογό της.

### 🇬🇧 English

**Added**

- **Multi-operator** support. You pick the operator when adding the integration;
  credentials belong to that operator's portal.
- **Nea Egnatia Odos** (EgnatiaPass, `myegnatiapass.gr`) alongside **Nea Attiki
  Odos**. The two deployments were compared field by field: the same client, the
  same thirteen API controllers, the same endpoints, and `clientConfig.json`
  files differing only in branding.
- Each card on the page takes its operator's colours, so two subscriptions from
  different operators are tellable apart at a glance, and the portal button goes
  to the right one.

**Changed**

- The published per-category limits are no longer module constants; they belong
  to the operator.

**Known limitation**

**Egnatia's limits are not recorded.** They are not published on a reachable page
and do not come from the API — they are price-list data. Rather than guess, the
operator declares no limits: the invalid-account limit stays empty and the
default warning threshold is a neutral figure you set yourself. Attiki Odos keeps
the limits from its own price list.

## [0.4.0] — 2026-08-20

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Κουμπί **Προβολή απόδειξης** στη σελίδα e-PASS, που εμφανίζεται αφού σταλεί μια
  πληρωμή στην τράπεζα. Ανοίγει την απόδειξη σε δικό της παράθυρο, με κουμπιά
  εκτύπωσης/αποθήκευσης ως PDF και επιστροφής — χωρίς να χρειάζεται σύνδεση στο
  portal.
- Το `button.*_prepare_top_up` δημοσιεύει πλέον `last_order_id`, την εντολή που
  στάλθηκε τελευταία στην τράπεζα.

**Σημείωση για το ποσό**

Ο πάροχος καταχωρεί την ανανέωση ως πίστωση, οπότε το `ChargeTotal` έρχεται
αρνητικό (`-1` για ανανέωση 1 €). Η απόδειξη το εμφανίζει ως θετικό ποσό, όπως
γίνεται ήδη με το υπόλοιπο.

### 🇬🇧 English

**Added**

- A **View receipt** button on the e-PASS page, shown once a payment has been
  handed to the bank. It opens the receipt in a window of its own with print /
  save-as-PDF and back buttons — no portal login needed.
- `button.*_prepare_top_up` now publishes `last_order_id`, the order most
  recently handed to the bank.

**A note on the amount**

The operator books a top-up as a credit, so `ChargeTotal` arrives negative
(`-1` for a 1 EUR top-up). The receipt shows it as a positive amount, the same
way the balance already does.

## [0.3.0] — 2026-08-20

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Υπηρεσία `attiki_odos_epass.get_receipt`, που φέρνει την απόδειξη του παρόχου
  για μία εντολή ανανέωσης. Χωρίς όρισμα χρησιμοποιεί την τελευταία εντολή που
  στάλθηκε στην τράπεζα. Με `wait: true` επαναλαμβάνει έως τριάντα δευτερόλεπτα,
  γιατί η τράπεζα επιβεβαιώνει την πληρωμή ξεχωριστά και η απόδειξη δεν υπάρχει
  την στιγμή που ολοκληρώνεται η πληρωμή.

**Γιατί υπάρχει**

Μετά την πληρωμή η τράπεζα επιστρέφει στη **δική της** σελίδα απόδειξης του
portal, όχι στο Home Assistant. Το URL επιστροφής το υπογράφει το portal και
καλύπτεται από το `Digest`, οπότε δεν μπορεί να αλλάξει από εδώ. Η σελίδα εκείνη
θέλει σύνδεση στο portal, που ο browser του Home Assistant δεν έχει — γι' αυτό
εμφανίζεται φόρμα εισόδου. Η ίδια απόδειξη όμως είναι διαθέσιμη μέσω API με το
token που κρατά ήδη το integration, οπότε το Home Assistant μπορεί να τη φέρει
μόνο του.

### 🇬🇧 English

**Added**

- An `attiki_odos_epass.get_receipt` service that fetches the operator's receipt
  for a top-up order. With no argument it uses the last order handed to the
  bank. With `wait: true` it retries for up to thirty seconds, because the bank
  confirms the payment out of band and the receipt is not there the moment the
  payer finishes.

**Why it exists**

After payment the bank returns the payer to the portal's **own** receipt page,
not to Home Assistant. That return url is signed by the portal and covered by
the `Digest`, so it cannot be changed from here. The page needs a portal login
which the Home Assistant browser does not have, which is why a sign-in form
appears. The same receipt is available over the API with the token the
integration already holds, so Home Assistant can fetch it itself.

## [0.2.2] — 2026-08-20

### 🇬🇷 Ελληνικά

**Προστέθηκαν**

- Κουμπί ανανέωσης στην κεφαλίδα της σελίδας. Το integration ρωτά κάθε 30 λεπτά,
  οπότε μετά από μια ανανέωση υπολοίπου το ποσό στην οθόνη είναι παλιό μέχρι το
  επόμενο ερώτημα· το κουμπί ζητά τα στοιχεία αμέσως και γυρίζει όσο περιμένει.

**Διορθώθηκαν**

- Ο σύνδεσμος πληρωμής παρέμενε στη σελίδα αφού χρησιμοποιηθεί, ακόμη και μετά
  από ανανέωση της σελίδας, προσκαλώντας ένα δεύτερο πάτημα που μόνο να
  αποτύχει μπορούσε. Πλέον φεύγει μόλις η εντολή καταναλωθεί, και επίσης όταν
  λήξει το δεκάλεπτο.
- Η σελίδα δήλωνε το custom element χωρίς έλεγχο, οπότε στη δεύτερη φόρτωση του
  module έσκαγε με «name has already been used with this registry». Συνέβαινε
  κανονικά, επειδή η ίδια σελίδα χρησιμεύει και ως σελίδα ρυθμίσεων του
  integration.

### 🇬🇧 English

**Added**

- A refresh control in the page header. The integration polls every 30 minutes,
  so after a top-up the amount on screen is stale until the next poll; the
  control fetches immediately and spins while it waits.

**Fixed**

- The payment link stayed on the page after it had been used, and survived a
  reload, inviting a second press that could only fail. It now goes as soon as
  the order is consumed, and also when the ten minutes run out.
- The page defined its custom element unguarded, so loading the module a second
  time threw "name has already been used with this registry". That happened in
  normal use, because the same page also backs the integration's config panel.

## [0.2.1] — 2026-08-20

### 🇬🇷 Ελληνικά

**Διορθώθηκαν**

- Στη σελίδα e-PASS, το κουμπί «Προετοιμασία πληρωμής» γκρίζαρε και δεν φαινόταν
  τίποτα. Ο σύνδεσμος **δημιουργούνταν** κανονικά, αλλά η σελίδα δεν τον
  εμφάνιζε: το πλαίσιο του συνδέσμου έχανε την κλάση με την οποία το έβρισκε ο
  κώδικας, στο πρώτο σχεδίασμα όσο δεν υπήρχε ακόμη σύνδεσμος. Πλέον το πλαίσιο
  εντοπίζεται με data attribute, που δεν μπορεί να σβηστεί από τα στιλ.

### 🇬🇧 English

**Fixed**

- On the e-PASS page, "Prepare payment" greyed out and nothing appeared. The
  link **was** being created, but the page never displayed it: the link box lost
  the class the code used to find it, during the first paint while no link
  existed yet. The box is now located by a data attribute, which styling cannot
  erase.

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

[Unreleased]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.6.5...v0.7.0
[0.6.5]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.6.4...v0.6.5
[0.6.4]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.5.3...v0.6.0
[0.5.3]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/VeZReVouLiS/GR-ePass/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/VeZReVouLiS/GR-ePass/releases/tag/v0.1.0
