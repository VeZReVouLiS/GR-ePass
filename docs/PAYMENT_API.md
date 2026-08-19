# Ανανέωση υπολοίπου — πώς δουλεύει στην πραγματικότητα

Τεκμηρίωση του reverse-engineered flow πληρωμής του my e-PASS, για όποιον
διαβάσει το `custom_components/attiki_odos_epass/payment.py` και θέλει να
καταλάβει *γιατί* είναι έτσι γραμμένο.

> Τίποτα από αυτά δεν είναι επίσημο API. Εξήχθη από το δημόσιο Angular bundle
> του `epass.naodos.gr` και επαληθεύτηκε με capture μιας πραγματικής υποβολής.
> Μπορεί να αλλάξει χωρίς προειδοποίηση.

## Το κρίσιμο σημείο: το Home Assistant δεν μπορεί να χρεώσει

Ο gateway είναι η **Alpha Bank** (controller `api/alphaPaym`). Η ροή έχει δύο
σκέλη και **μόνο το πρώτο** γίνεται από server:

1. `POST /api/alphaPaym/PrepAlphaPayment` — το backend του e-PASS **υπογράφει**
   μια εντολή και επιστρέφει `Digest`, `MerchantId`, `OrderId`,
   `OrderDescription`, `SuccessUrl`, `FailUrl`, `Email`, `PostUrl`.
   **Δεν κινείται χρήμα εδώ.**
2. Τα πεδία υποβάλλονται ως **HTML form POST από browser** στο `PostUrl`
   (`https://www.alphaecommerce.gr/vpos/shophandlermpi`). Εκεί τρέχει το
   3-D Secure και εκεί γίνεται η χρέωση.

Δεν υπάρχει endpoint που χρεώνει αποθηκευμένη κάρτα server-side. Το 3-D Secure
απαιτεί browser context (device fingerprint, browser info) **ακόμα και όταν
είναι frictionless** — δηλαδή όταν η τράπεζα δεν εμφανίζει challenge γιατί
εφαρμόζεται low-value exemption του PSD2.

**Συνέπεια:** αυτόματη ανανέωση χωρίς άνθρωπο δεν είναι εφικτή από το HA. Η
πάγια εντολή που αναφέρει ο τιμοκατάλογος («Όριο Ανανέωσης Λογαριασμού με
Πιστωτική Κάρτα») στήνεται από τον πάροχο, όχι από το portal — δεν υπάρχει
route ή endpoint γι' αυτήν στο SPA.

## Αποθηκευμένες κάρτες

```
GET  /api/alphaPaym/GetStoredCards        -> Id, Alias, CardNumber (4 ψηφία),
                                             CardTypeId, Token, ExpiryDate
GET  /api/alphaPaym/GetPaymProviderInfo   -> MinAmount, MaxAmount
GET  /api/alphaPaym/DeleteStoredCard/{id}
POST /api/alphaPaym/SaveStoredCard        -> σώζει ΜΟΝΟ το Alias
```

`eOCardTypeMap = {0: other, 1: visa, 2: mastercard, 3: maestro, 4: amex, 5: diners}`

Κατάσταση κάρτας, όπως το `getEffectiveState()` του portal — **η λήξη νικά**:

| | |
| --- | --- |
| 1 active | ενεργή και μη ληγμένη |
| 2 inactive | `Active == false` |
| 3 expired | `ExpiryDate < now` |

Η σελίδα πληρωμής φιλτράρει `ExpiryDate >= now` και προεπιλέγει την πρώτη.

> **Η πρώτη χρέωση πρέπει να γίνει στο portal.** Το `SaveStoredCard` δεν δέχεται
> στοιχεία κάρτας — το `Token` το δημιουργεί η τράπεζα κατά την πραγματική
> πληρωμή. Άρα δεν υπάρχει τρόπος «προσθήκης κάρτας» από το Home Assistant.

## Τα πεδία της φόρμας

40 hidden inputs. Το `digest` είναι HMAC πάνω σε αυτά, οπότε **κάθε υπογεγραμμένη
τιμή που στέλνουμε στη φόρμα πρέπει να είναι ίδια με αυτή που στείλαμε στο
`PrepAlphaPayment`**. Αυτο-συνέπεια είναι το μόνο που μετράει — δεν χρειάζεται
να μαντέψουμε «σωστές» τιμές.

| Πεδίο | Τιμή | Από πού |
| --- | --- | --- |
| `version` | `2` | σταθερό |
| `deviceCategory` | `0` | σταθερό |
| `lang` | `el` / `en` | γλώσσα HA |
| `currency` | `EUR` | σταθερό |
| `mid` | `MerchantId` | PrepAlphaPayment |
| `orderid`, `orderDesc` | `OrderId`, `OrderDescription` | PrepAlphaPayment |
| `orderAmount`, `orderAmountOriginal` | το ποσό ως string | δικό μας |
| `payerEmail` | email λογαριασμού | GetAccount |
| `payerPhone` | κενό | ο SPA δεν το γεμίζει |
| `billCountry` | `GR` | `getCountryCode()` — default ήδη `GR` |
| `billCity`, `billZip`, `billAddress` | Mailing\* ή Billing\* | δες παρακάτω |
| `billState` | κενό | σταθερό |
| `confirmUrl`, `cancelUrl` | `SuccessUrl`, `FailUrl` | **ταυτόσημα στην πράξη** |
| `extTokenOptions` | `110` | αποθηκευμένη κάρτα (`100` = νέα + αποθήκευση) |
| `extToken` | `Token` κάρτας | GetStoredCards |
| `digest` | HMAC | PrepAlphaPayment |
| `agreedToTOS` | `on` | **είναι μέσα στη φόρμα, υποβάλλεται** |
| `trType`, `payMethod`, `cssUrl`, `blockScore`, `maxPayRetries`, `reject3dsU`, `weight`, `dimensions`, `ship*`, `addFraudScore`, `extInstallment*`, `extRecurring*`, `var1`–`var5` | **όλα κενά** | σταθερά |

### Διεύθυνση χρέωσης

Τα `Billing*` πεδία του λογαριασμού είναι συχνά `null`. Ο portal κάνει:

```js
populateBillingAddress() {
  if (account.SameBillingAsMailingAddress) {
    account.BillingAddress    = account.MailingAddress;
    account.BillingCity       = account.MailingCity;
    account.BillingCountryID  = account.MailingCountryID;
    account.BillingPostalCode = account.MailingPostalCode;
  }
}
```

Και περνά κάθε τιμή από `sanitizeForPayment()`: newlines σε space, `"` σε `'`,
HTML entities σε `&`/`-`/`'`, αφαίρεση NUL. Το `payment.py` το αναπαράγει
**ακριβώς** — όχι «βελτιωμένο» — γιατί το digest υπολογίζεται πάνω σε αυτά τα
strings.

## Πώς παίρνεις capture χωρίς να χρεωθείς

Χρήσιμο αν αλλάξουν τα πεδία. Ο portal καλεί
`this.paymForm.nativeElement.submit()`, οπότε αντικατάσταση του
`HTMLFormElement.prototype.submit` το σταματά πριν φύγει:

```javascript
(() => { HTMLFormElement.prototype.submit = function () {
  window.__epass = { action: this.action, fields: Object.fromEntries(new FormData(this)) };
  console.log('BLOCKED', window.__epass); }; })();
```

Έλεγχος πριν πατήσεις: `HTMLFormElement.prototype.submit.toString().includes('__epass')`
πρέπει να δώσει `true`. Μετά `copy(JSON.stringify(window.__epass, null, 2))`.

> Το κουμπί πληρωμής είναι **disabled** μέχρι να ισχύει
> `readyToProcess() = accLoaded && agreedToTOS && !isNaN(amount2submit) && !amountError`.
> Χωρίς τσεκαρισμένο το checkbox όρων, το κλικ δεν κάνει τίποτα.

Θα δημιουργηθεί ένα order που δεν ολοκληρώνεται. Είναι κανονικό — το ίδιο
συμβαίνει κάθε φορά που κάποιος εγκαταλείπει πληρωμή.

## Η ροή στο Home Assistant

```
select  Κάρτα πληρωμής     ->  ποια αποθηκευμένη κάρτα
number  Ποσό ανανέωσης     ->  όρια από GetPaymProviderInfo (0.01 - 5000)
button  Προετοιμασία        ->  PrepAlphaPayment, δημοσιεύει one-shot link
        ↓ event attiki_odos_epass_payment_ready {amount, card, order_id, link}
GET  /api/attiki_odos_epass/pay/{nonce}   σελίδα επιβεβαίωσης, ΔΕΝ υποβάλλει
POST (το κλικ)                            καταναλώνει το order, υποβάλλει στην τράπεζα
```

Το view είναι `requires_auth = False` επίτηδες, ώστε το link να ανοίγει με ένα
tap από Telegram σε κινητό χωρίς HA session. Τι το προστατεύει:

- nonce 128-bit από `secrets.token_urlsafe`
- **μία χρήση** — το `POST` καταναλώνει το order
- λήξη σε 10 λεπτά
- ποσό και κάρτα είναι **κλειδωμένα στην υπογραφή**, το link δεν μπορεί να
  τροποποιηθεί σε άλλη χρέωση
- το χειρότερο που κάνει διαρροή link είναι ανανέωση του **δικού σου** υπολοίπου

Η σελίδα **δεν** κάνει auto-submit: το κλικ είναι το τελευταίο σημείο ακύρωσης.
