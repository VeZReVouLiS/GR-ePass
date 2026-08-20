"""Generate the English dashboard card from the Greek one.

The card's labels are literal strings, not entity translations, so a Greek card
shows Greek to everyone. Rather than maintain two files by hand, the English
variant is derived here: edit dashboard-portal-card.yaml, re-run this, and the
two stay in step.

    python tools/make_en_card.py

Anything not in REPLACEMENTS is left alone, and the script fails loudly if a
phrase it expects to translate has disappeared -- otherwise a rename on the
Greek side would silently leak Greek into the English card.
"""

from __future__ import annotations

import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "dashboard-portal-card.yaml"
DST = pathlib.Path(__file__).resolve().parent.parent / "dashboard-portal-card.en.yaml"

# Longest first, so a short phrase cannot eat part of a longer one.
REPLACEMENTS: list[tuple[str, str]] = [
    # headings and labels
    ("### Συνδρομητικός Λογαριασμός", "### Subscription account"),
    ("Υπόλοιπο Συνδρομητικού Λογαριασμού", "Account balance"),
    ("Συνδρομητικό Πρόγραμμα", "Subscription plan"),
    ("Κόστος διελεύσεων μήνα", "Toll cost this month"),
    ("Ημερομηνία πληρωμής", "Payment date"),
    ("Κατάσταση συνδρομής", "Account status"),
    ("Τελευταία πληρωμή", "Last payment"),
    ("Πομποδέκτες e-PASS", "e-PASS transponders"),
    ("Όριο ειδοποίησης", "Warning threshold"),
    ("Όριο άκυρου λογαριασμού", "No-pass limit"),
    ("Διελεύσεις μήνα", "Passes this month"),
    ("Πληρωμές μήνα", "Payments this month"),
    ("Κάρτα πληρωμής", "Payment card"),
    ("Ποσό ανανέωσης", "Top-up amount"),
    ("Τελευταία διέλευση", "Last pass"),
    ("— Αττική Οδός", "— Attiki Odos"),
    ("— Άλλα δίκτυα", "— Other networks"),
    ("Κινήσεις", "Activity"),
    ("Πληρωμή", "Pay"),
    # donut states, inside the button-card JS
    ("'Κλειστός'", "'Closed'"),
    ("'Έγκυρος'", "'Valid'"),
    ("'Χαμηλός'", "'Low'"),
    ("'Άκυρος'", "'Invalid'"),
    ("Χωρίς δεδομένα", "No data"),
    # The portal writes credit as "13,79 € Π" and debit as "... Χ". That
    # notation only exists in Greek, so the English card drops the suffix and
    # keeps the sign, which reads the same way to everyone.
    ("""}) + ' € ' + (bal >= 0 ? 'Π' : 'Χ');""", """}) + ' €';"""),
    ("'el-GR'", "'en-GB'"),
    # template rows
    ("'active': 'Ενεργή',", "'active': 'Active',"),
    ("'active_partial': 'Μερικώς ενεργή',", "'active_partial': 'Partially active',"),
    ("'inactive': 'Ανενεργή',", "'inactive': 'Inactive',"),
    ("'incomplete': 'Ημιτελής',", "'incomplete': 'Incomplete',"),
    ("'closed': 'Κλειστή' } %}", "'closed': 'Closed' } %}"),
    # last-pass markdown
    ("or 'Σταθμός ?' }} · λωρίδα", "or 'Plaza ?' }} · lane"),
    ("Καμία διέλευση καταγεγραμμένη.", "No pass recorded yet."),
    ("_Διέλευση σε άλλο δίκτυο (διαλειτουργικότητα)._",
     "_Pass on another network, via interoperability._"),
    (" · λήξη {{", " · expires {{"),
    ("Καμία αποθηκευμένη κάρτα", "No stored card"),
    # the no-card warning
    ("⚠️ **Δεν υπάρχει αποθηκευμένη κάρτα.**",
     "⚠️ **No stored card.**"),
    ("Η πρώτη χρέωση πρέπει να γίνει στη σελίδα του my e-PASS, τσεκάροντας\n"
     "        την «αποθήκευση κάρτας». Για λόγους ασφαλείας το token της κάρτας το\n"
     "        δημιουργεί η τράπεζα κατά την πληρωμή — δεν μπορεί να προστεθεί από το\n"
     "        Home Assistant.",
     "The first charge has to happen on the my e-PASS site, with \"save card\"\n"
     "        ticked. For security the card token is minted by the bank during a real\n"
     "        payment, so a card cannot be added from Home Assistant."),
]

HEADER_NOTE = """# English variant of dashboard-portal-card.yaml.
#
# GENERATED -- do not edit by hand. Change dashboard-portal-card.yaml and run:
#     python tools/make_en_card.py
#
"""


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    missing = [src for src, _ in REPLACEMENTS if src not in text]
    if missing:
        print("Αυτές οι φράσεις δεν βρέθηκαν στο ελληνικό αρχείο:", file=sys.stderr)
        for item in missing:
            print("  " + item.replace("\n", "\\n"), file=sys.stderr)
        raise SystemExit(1)

    for src, dst in REPLACEMENTS:
        text = text.replace(src, dst)

    DST.write_text(HEADER_NOTE + text, encoding="utf-8", newline="\n")
    print(f"wrote {DST.name}")

    # Greek left in a rendered position is a translation we forgot. Comments are
    # skipped on purpose -- both YAML (#) and the JS ones inside the button-card
    # block (//) stay in Greek, since this file is generated from the Greek one
    # and that is where the explanations belong.
    leftovers = [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), 1)
        if not line.lstrip().startswith(("#", "//"))
        and any("Ͱ" <= ch <= "῿" for ch in line)
    ]
    if leftovers:
        print(f"ΠΡΟΣΟΧΗ, {len(leftovers)} γραμμές με ελληνικά σε ορατή θέση:")
        for number, line in leftovers[:15]:
            print(f"   {number}: {line[:100]}")
        raise SystemExit(1)
    print("καμία ελληνική λέξη σε ορατή θέση")


if __name__ == "__main__":
    main()
