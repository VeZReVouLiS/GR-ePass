# Attiki Odos e-Pass

Φέρνει τον συνδρομητικό λογαριασμό **my e-PASS** στο Home Assistant: υπόλοιπο,
διελεύσεις, κόστος και στατιστικά — συνολικά και ανά πομποδέκτη.

Brings your **my e-PASS** toll account into Home Assistant: balance, passes,
cost and statistics — account-wide and per transponder.

---

**Ελληνικά**

- Υπόλοιπο με σωστό πρόσημο, κατάσταση λογαριασμού, τελευταία πληρωμή
- Διελεύσεις και κόστος: σήμερα, μήνας, 30 ημέρες, προηγούμενος μήνας
- Ξεχωριστό device για κάθε πομποδέκτη, με πινακίδα και κατηγορία διοδίων
- Διαχωρισμός Αττικής Οδού από άλλα δίκτυα
- Κατώφλι ειδοποίησης **προσαρμοσμένο στην κατηγορία του οχήματός σας**
- Ανανέωση υπολοίπου με ένα tap, από αποθηκευμένη κάρτα
- Events για κάθε διέλευση και κάθε αλλαγή υπολοίπου

**English**

- Balance with the sign the way you expect it, account status, last payment
- Passes and cost: today, this month, 30 days, previous month
- One device per transponder, with plate and toll category
- Attiki Odos split from other motorways
- Warning threshold **matched to your own vehicle category**
- One-tap top-up from a stored card
- Events for every pass and every balance change

---

> Ανεπίσημο. Δεν υπάρχει επίσημο API — τα endpoints εντοπίστηκαν από το δημόσιο
> Angular bundle του `epass.naodos.gr` και μπορούν να αλλάξουν χωρίς
> προειδοποίηση. Δεν σχετίζεται με τη Νέα Αττική Οδό.
>
> Unofficial. There is no public API; the endpoints were derived from the site's
> own JavaScript and may change without notice. Not affiliated with Nea Attiki
> Odos.

Μετά την εγκατάσταση: **Settings → Devices & Services → Add Integration →
Attiki Odos e-Pass**, και βάλτε τα στοιχεία του my e-PASS.
