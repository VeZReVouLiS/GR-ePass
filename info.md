# GR e-PASS

Φέρνει τους **προπληρωμένους λογαριασμούς διοδίων** στο Home Assistant: υπόλοιπο,
διελεύσεις, κόστος και στατιστικά — συνολικά και ανά πομποδέκτη. Υποστηρίζονται η
**Νέα Αττική Οδός** και η **Νέα Εγνατία Οδός** (EgnatiaPass).

Brings **prepaid Greek toll accounts** into Home Assistant: balance, passes, cost
and statistics — account-wide and per transponder. Supports **Nea Attiki Odos**
and **Nea Egnatia Odos** (EgnatiaPass).

---

**Ελληνικά**

- Επιλογή παρόχου κατά την προσθήκη· κάθε κάρτα παίρνει τα χρώματά του
- Δική του σελίδα στο μενού — δεν χρειάζεται dashboard ούτε YAML
- Υπόλοιπο με σωστό πρόσημο, κατάσταση λογαριασμού, τελευταία πληρωμή
- Διελεύσεις και κόστος: σήμερα, μήνας, 30 ημέρες, προηγούμενος μήνας
- Ξεχωριστό device για κάθε πομποδέκτη, με πινακίδα και κατηγορία διοδίων
- Διαχωρισμός του δικτύου του παρόχου από τα υπόλοιπα δίκτυα
- Ανανέωση υπολοίπου με ένα tap, από αποθηκευμένη κάρτα, και απόδειξη μέσα από
  το Home Assistant
- Events για κάθε διέλευση και κάθε αλλαγή υπολοίπου

Το κατώφλι ειδοποίησης προσαρμόζεται στην κατηγορία του οχήματος **όπου ο πάροχος
δημοσιεύει όρια**. Για τη Νέα Αττική Οδό είναι από τον τιμοκατάλογό της· για τη
Νέα Εγνατία Οδό δεν έχουν καταχωρηθεί ακόμη, οπότε το ορίζετε εσείς.

**English**

- Pick your operator when adding it; each card takes that operator's colours
- Its own page in the sidebar — no dashboard to build, no YAML
- Balance with the sign the way you expect it, account status, last payment
- Passes and cost: today, this month, 30 days, previous month
- One device per transponder, with plate and toll category
- The operator's own network split from the other motorways
- One-tap top-up from a stored card, and the receipt from inside Home Assistant
- Events for every pass and every balance change

The warning threshold follows the vehicle category **where the operator publishes
limits**. Nea Attiki Odos does, from its price list; Nea Egnatia Odos has not
been recorded yet, so you set it yourself.

---

> Ανεπίσημο. Δεν υπάρχει επίσημο API — τα endpoints εντοπίστηκαν από τα δημόσια
> Angular bundles των portal και μπορούν να αλλάξουν χωρίς προειδοποίηση. Δεν
> σχετίζεται με καμία από τις εταιρείες παραχώρησης.
>
> Unofficial. There is no public API; the endpoints were derived from the
> portals' own JavaScript and may change without notice. Not affiliated with any
> of the concession companies.

Μετά την εγκατάσταση: **Settings → Devices & Services → Add Integration →
GR e-PASS**, διαλέξτε πάροχο και βάλτε τα στοιχεία του portal του.
