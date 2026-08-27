# Ασφάλεια / Security

Πού αποθηκεύεται ο κωδικός σου, τι κινδυνεύει, και τι μπορείς να κάνεις.

Where your password is kept, what is actually at risk, and what you can do about
it.

---

## Ο κωδικός αποθηκεύεται σε καθαρό κείμενο

Και ναι, αξίζει να το ξέρεις.

Το Home Assistant κρατά τα στοιχεία κάθε integration στο
`.storage/core.config_entries`, **χωρίς κρυπτογράφηση**. Δεν είναι κάτι ειδικό σε
αυτό το integration: ισχύει για κάθε integration που χρειάζεται κωδικό, και δεν
υπάρχει μηχανισμός στο Home Assistant για κρυπτογραφημένη αποθήκευση που θα
μπορούσαμε να χρησιμοποιήσουμε.

Home Assistant stores every integration's credentials unencrypted in
`.storage/core.config_entries`. That is true of every integration that needs a
password, and Home Assistant offers no encrypted store to use instead.

## Γιατί δεν κρατάμε μόνο ένα token

Η προφανής εναλλακτική — να μη σώζουμε καθόλου κωδικό, μόνο ένα refresh token —
**ελέγχθηκε και δεν δουλεύει εδώ**.

Τα tokens του portal είναι βραχύβια. Το `clientConfig.json` του δηλώνει
`SessionTimeOut: 900` και `RestoreLoginTokenPeriod: 600`, δηλαδή δεκαπέντε και
δέκα λεπτά, και όταν ο server δεν στέλνει `expires_in` υποθέτουμε δέκα. Το refresh
token δεν επιβιώνει επανεκκίνησης του Home Assistant.

Με ανανέωση κάθε 30 λεπτά, ένα integration που κρατούσε μόνο token θα ζητούσε
κωδικό ξανά σχεδόν σε κάθε κύκλο. Το API απαιτεί `grant_type=password` για κάθε
νέα σύνδεση.

The obvious alternative — keep a refresh token instead of the password — was
checked and does not work here: the portal's tokens live ten to fifteen minutes
and do not survive a restart, so it would ask for the password again on almost
every poll.

## Τι **δεν** διαρρέει

- **Diagnostics.** Ο κωδικός είναι στη λίστα απόκρυψης, οπότε αν κατεβάσεις
  diagnostics για να αναφέρεις πρόβλημα, δεν περιέχουν τον κωδικό.
- **Logs.** Ούτε ο κωδικός ούτε τα tokens καταγράφονται πουθενά, ούτε σε debug.

Downloading diagnostics to report a problem does not expose the password, and
neither the password nor the tokens are ever logged.

## Τι προστατεύει πραγματικά

Αφού το `.storage` είναι σε καθαρό κείμενο, η προστασία είναι γύρω από το αρχείο,
όχι μέσα του:

- **Κρυπτογραφημένα backup.** Ο ευκολότερος τρόπος να φύγει αντίγραφο του
  `.storage` από το μηχάνημα είναι ένα backup. Το Home Assistant υποστηρίζει
  κρυπτογράφηση — χρησιμοποίησέ τη, ειδικά αν τα backup ανεβαίνουν σε cloud.
- **Κρυπτογράφηση δίσκου** στο μηχάνημα που τρέχει το Home Assistant.
- **Δικαιώματα και πρόσβαση** στο `/config`: όποιος διαβάζει τον φάκελο, διαβάζει
  τον κωδικό.
- **Ξεχωριστός κωδικός** για το portal, που δεν τον χρησιμοποιείς αλλού.

Encrypted backups matter most: a backup is the easiest way for a copy of
`.storage` to leave the machine.

## Ο σύνδεσμος πληρωμής

Ο σύνδεσμος είναι σκόπιμα χωρίς authentication, ώστε να ανοίγει μακριά από το Home
Assistant. Τον προστατεύει ότι:

- φέρει nonce 128 bit, **μίας χρήσης**
- λήγει σε **δέκα λεπτά**
- το ποσό και η κάρτα είναι **κλειδωμένα στην υπογραφή** — δεν μπορεί να γίνει
  edit σε άλλη χρέωση
- το endpoint ακύρωσης δέχεται **μόνο POST**, ώστε οι εφαρμογές συνομιλίας που
  κατεβάζουν συνδέσμους για preview να μη σκοτώνουν την εντολή

Το χειρότερο που κάνει μια διαρροή είναι **ανανέωση του δικού σου υπολοίπου**.

The worst a leaked payment link can do is top up your own toll balance.

## Ο κωδικός δεν φεύγει από το Home Assistant σου

Το integration μιλά **μόνο** με το portal του παρόχου. Δεν υπάρχει τηλεμετρία,
ούτε ενδιάμεσος διακομιστής, ούτε κάποια υπηρεσία δική μας. Τα στατιστικά
χτίζονται και μένουν τοπικά.

The integration talks only to your operator's portal. There is no telemetry, no
intermediate server, and the statistics are built and kept locally.
