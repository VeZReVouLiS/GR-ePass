"""Δομικός έλεγχος για το JS του panel, όπου δεν υπάρχει node.

Το `gr-epass-panel.js` σερβίρεται όπως είναι στον browser: ένα ασυμμετρικό
άγκιστρο δεν σκοτώνει μια γραμμή, σκοτώνει **όλη τη σελίδα**. Χωρίς node τοπικά,
αυτός ο tokenizer είναι ο μόνος έλεγχος πριν το commit.

Δεν είναι parser της JavaScript. Περπατά τον κώδικα χαρακτήρα-χαρακτήρα ξέροντας
από σχόλια, τα τρία είδη quotes, `${...}` μέσα σε template literals και regex
literals, και επιβεβαιώνει ότι κάθε άγκιστρο, παρένθεση και αγκύλη κλείνει. Αυτό
πιάνει την κατηγορία λάθους που κάνει ένα patch — όχι λάθη τύπων ή λογικής.

    python tools/jscheck.py custom_components/gr_epass/panel/gr-epass-panel.js

Έξοδος 0 αν είναι εντάξει, 1 με τα ευρήματα αν όχι.

Ο διαχωρισμός regex από διαίρεση γίνεται με τον προηγούμενο σημαντικό χαρακτήρα:
μια `/` ξεκινά regex μόνο όπου περιμένουμε τιμή. Χωρίς αυτό, το `/[&<>"]/g` στη
συνάρτηση esc() διαβαζόταν ως άνοιγμα string και όλα μετά έβγαιναν λάθος.
"""

import sys, pathlib

def check(path):
    src = pathlib.Path(path).read_text(encoding="utf-8")
    i, n, line = 0, len(src), 1
    stack, errors = [], []
    pairs = {"{": "}", "(": ")", "[": "]"}
    prev = ""            # last significant char, to tell regex from division
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1; i += 1; continue
        if c in " \t\r":
            i += 1; continue
        if src.startswith("//", i):
            j = src.find("\n", i); i = n if j < 0 else j; continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            line += src.count("\n", i, j if j > 0 else n)
            i = n if j < 0 else j + 2; continue
        # regex literal: a '/' can only start one where a value is expected
        if c == "/" and (prev == "" or prev in "(,=:[!&|?{};+*~^%<>"):
            i += 1; inclass = False
            while i < n:
                if src[i] == "\\": i += 2; continue
                if src[i] == "[": inclass = True
                elif src[i] == "]": inclass = False
                elif src[i] == "/" and not inclass: break
                elif src[i] == "\n": errors.append(f"line {line}: newline in regex"); break
                i += 1
            i += 1; prev = "/"; continue
        if c in "\"'":
            q, i = c, i + 1
            while i < n and src[i] != q:
                if src[i] == "\\": i += 1
                elif src[i] == "\n": errors.append(f"line {line}: newline in {q}-string"); break
                i += 1
            i += 1; prev = "x"; continue
        if c == "`":
            i += 1
            while i < n:
                if src[i] == "\\": i += 2; continue
                if src[i] == "\n": line += 1
                if src[i] == "`": break
                if src.startswith("${", i):
                    depth, i = 1, i + 2
                    while i < n and depth:
                        if src[i] == "{": depth += 1
                        elif src[i] == "}": depth -= 1
                        elif src[i] == "\n": line += 1
                        elif src[i] in "\"'":
                            q2, i = src[i], i + 1
                            while i < n and src[i] != q2:
                                i += 1 if src[i] != "\\" else 2
                        i += 1
                    continue
                i += 1
            i += 1; prev = "x"; continue
        if c in pairs:
            stack.append((c, line))
        elif c in pairs.values():
            if not stack:
                errors.append(f"line {line}: closing {c!r} with nothing open")
            else:
                o, ol = stack.pop()
                if pairs[o] != c:
                    errors.append(f"line {line}: {c!r} closes {o!r} from line {ol}")
        prev = c
        i += 1
    for o, ol in stack:
        errors.append(f"unclosed {o!r} opened on line {ol}")
    return src.count("\n") + 1, errors

lines, errors = check(sys.argv[1])
print(f"γραμμές: {lines}")
if errors:
    print("ΣΦΑΛΜΑΤΑ:")
    for e in errors[:10]: print("  -", e)
    sys.exit(1)
print("δομή OK — αγκύλες ισορροπημένες, strings/template literals/regex κλειστά")
