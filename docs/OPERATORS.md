# Πάροχοι διοδίων / Toll operators

Αναλυτικά ευρήματα: ποιοι πάροχοι δουλεύουν με αυτό το integration, ποιοι όχι,
και **γιατί**. Η σύντομη απάντηση είναι στο README.

The detailed findings: which operators work with this integration, which do not,
and **why**. The short answer lives in the README.

---

## Η σύντομη εκδοχή / The short version

| Πάροχος | Συνδρομή | Υποστηρίζεται |
|---|---|---|
| Νέα Αττική Οδός | e-PASS | ✅ |
| Νέα Εγνατία Οδός | EgnatiaPass | ✅ |
| Μορέας | *δεν έχει δική του* — χρησιμοποιεί e-PASS | ✅ μέσω Αττικής Οδού |
| Νέα Οδός / Κεντρική Οδός | fastpass | ❌ |
| Ολυμπία Οδός | ΟΛΥΜΠΙΑ PASS | ❌ |
| Αυτοκινητόδρομος Αιγαίου | eway | ❌ |
| Γέφυρα Ρίου–Αντιρρίου | Gefyra e-Pass | ❌ |

Οι διελεύσεις σας σε **όλα** τα παραπάνω δίκτυα φαίνονται ούτως ή άλλως, χάρη στη
διαλειτουργικότητα: μπαίνουν στη γραμμή «Άλλα δίκτυα». Αυτό που δεν είναι
προσβάσιμο είναι ο **λογαριασμός** των υπόλοιπων παρόχων.

Passes on **every** network above show up anyway, through interoperability: they
land in the "other networks" line. What is not reachable is the other operators'
**accounts**.

---

## Γιατί δουλεύουν δύο / Why two of them work

Η Αττική Οδός και η Εγνατία τρέχουν **το ίδιο εμπορικό προϊόν**, μία εγκατάσταση
ανά πάροχο. Το συγκρίναμε πεδίο προς πεδίο:

- ίδιο Angular client, ίδιο `assets/clientConfig.json` — τα δύο αρχεία διαφέρουν
  μόνο σε ονόματα και χρώματα, ούτε καν σε δομή
- ίδια δεκατρία API controllers (`api/Account`, `api/alphaPaym`, `api/Payment`, …)
- ίδια endpoints μέχρι λεπτομέρειας: `oauth2/token`, `GetAccountRecentActivities`,
  `PrepAlphaPayment`, `GetTxnReceipt`, ακόμη και `IbiSystemIntegrityCheck`
- κανένα από τα δύο δεν δηλώνει `serverUrl`, άρα το καθένα μιλά στο δικό του origin

Γι' αυτό η προσθήκη της Εγνατίας ήταν **ένα base URL** και λίγα labels, όχι νέα
υλοποίηση.

Attiki Odos and Egnatia run **the same commercial product**, deployed once per
operator, which is why adding Egnatia was one base url rather than a new client.

---

## Γιατί δεν δουλεύουν οι υπόλοιποι / Why the others do not

Καθένας τρέχει **δικό του, άσχετο** σύστημα. Κανένας δεν έχει
`assets/clientConfig.json`, `oauth2/token` ή `api/alphaPaym` — ελέγχθηκαν ένα προς
ένα και επιστρέφουν 404.

### Νέα Οδός & Κεντρική Οδός — fastpass

WordPress με **φόρμες PHP**: η σύνδεση ποστάρει σε `kp_authenticate.php`, με
`create_user.php` και `forget_password.php` δίπλα. Καμία JSON υπηρεσία. Η
εφαρμογή «MyOdos» είναι ξεχωριστό προϊόν και δεν βρέθηκε host API για κινητό.

### Ολυμπία Οδός — ΟΛΥΜΠΙΑ PASS

`opass.olympiaodos.gr/EPT/Login.aspx`: **ASP.NET Web Forms**, με `__VIEWSTATE`,
`__EVENTVALIDATION`, `ScriptResource.axd` και jQuery 1.4.4 φορτωμένο από `http://`.
Μηδέν `.ashx/.asmx/.svc/.json`, δηλαδή καθόλου JSON API από κάτω.

Είναι η **πιο εύθραυστη** περίπτωση από όλες: το `__VIEWSTATE` είναι αδιαφανές
base64 που πρέπει να διαβαστεί από κάθε σελίδα και να επιστραφεί αυτούσιο, και
οποιαδήποτε αλλαγή στη σελίδα το ακυρώνει.

### Αυτοκινητόδρομος Αιγαίου — eway

Το «My eway» (`myeway.gr/myeasyway/profile/`) είναι σελίδα **WordPress**. Κανένα
από τα endpoints της πλατφόρμας δεν απαντά.

### Γέφυρα Ρίου–Αντιρρίου — Gefyra e-Pass

`gefyraepass.gr`: **AngularJS 1.x** με `angular-route.min.js` και jQuery 1.7.1 —
παλιά, εντελώς διαφορετική στοίβα.

### Μορέας — δεν χρειάζεται

Ο Μορέας **δεν εκδίδει δική του συνδρομή**. Η σελίδα του λέει ότι οι οδηγοί
αποκτούν «την ηλεκτρονική συσκευή e-PASS της Νέας Αττικής Οδού», και παραπέμπει
στα Σημεία Εξυπηρέτησης και στο τηλέφωνο της Αττικής Οδού. Άρα ένας συνδρομητής
Μορέα προσθέτει τον **e-PASS** λογαριασμό του και δουλεύει σήμερα.

Moreas issues no subscription of its own: its drivers carry the Attiki Odos
e-PASS, so a Moreas subscriber is already covered.

---

## Τι θα χρειαζόταν για τους υπόλοιπους / What supporting the rest would take

**Scraper, όχι API client.** Σύνδεση με cookies συνεδρίας, ανάγνωση τιμών από
πίνακες HTML, και καμία εγγύηση σταθερότητας: κάθε ανασχεδίαση σελίδας το σπάει.
Ο μηχανισμός υπογραφής που κάνει δυνατή την ανανέωση υπολοίπου εδώ **δεν υπάρχει**
σε καμία από τις άλλες πλατφόρμες.

Αν γίνει ποτέ, ανήκει σε ξεχωριστό integration, με ρητή προειδοποίηση ότι σπάει,
και πιθανότατα μόνο για ανάγνωση υπολοίπου — όχι πληρωμή.

It would be a scraper rather than an API client, and the signing mechanism that
makes topping up possible here does not exist on any of them. If it ever happens
it belongs in a separate integration, read-only, with an explicit warning about
how easily it breaks.

---

## Πώς να ελέγξεις έναν πάροχο / How to check an operator

Αν εμφανιστεί νέος πάροχος, δύο εντολές αρκούν:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<portal>/assets/clientConfig.json
curl -s https://<portal>/ | grep -oE 'main\.[a-f0-9]+\.js'   # και μετά grep για api/alphaPaym
```

Αν το πρώτο απαντήσει 200 και το bundle περιέχει `api/alphaPaym`, είναι η ίδια
πλατφόρμα και η υποστήριξη είναι μια εγγραφή στο
[`operators.py`](https://github.com/VeZReVouLiS/GR-ePass/blob/main/custom_components/gr_epass/operators.py).
