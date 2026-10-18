#!/usr/bin/env python3
"""
Correct the third credential on the home page — the language line.

    python3 tools/credential-language.py

Run any time after prerender.py. Re-run after a re-export: the text lives in
the Design Canvas DICT, so an export brings an old wording back.

What was wrong. The card said "Delivery languages · English · Arabic · Chinese",
and the Arabic said the same. OceanAstra stopped promising three-language
delivery and support on 2026-08-21 — that is a staffing commitment — while
keeping the three languages as a property of the software. Everywhere else on
the site was brought in line at the time (see COPY_EDITS in prepare-export.py);
this card was missed, so the home page went on promising in a headline slot
exactly what the rest of the site had withdrawn. It now names the thing that is
actually true: the product interfaces come in three languages.

The three languages had also drifted apart. prepare-export.py replaced the
export's "10+" claims one language at a time, and the Chinese one landed
somewhere else entirely — "出海中东 · 中东本地交付", a claim about local
delivery with no mention of language. A visitor switching languages saw a
different third credential, which is the failure mode the COPY_EDITS comment
warns about. All three now say the same thing.

LABEL, VALUE and SENTENCE each hold every wording that slot has carried,
newest last, and all of them map to the new one. That list is the point of the
tool: a re-export restores the *export's* wording, not whatever the site said
yesterday, so matching only the current text would leave the tool unable to fix
the one case it exists for. Revising this card means adding a wording here.

SENTENCE is the same credential as content/i18n carries it — prose rather than
a label/value pair, because that file predates the card.

The Arabic is a translation of the new English following the sentence shapes
already in the file, and should be read by a native speaker before it is
relied on.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Only the home page carries the credential strip; content/i18n holds the same
# strings as the source of truth for the next export and the next translation.
FILES = ["index.html", "zh/index.html", "ar/index.html",
         "content/i18n/en.json", "content/i18n/zh.json", "content/i18n/ar.json"]

LANGS = ("en", "zh", "ar")

# Listed per language rather than per revision: the export's "10+" claims were
# corrected one language at a time, so the three have not shared a wording
# since. "出海中东" is where the Chinese drifted to; "交付语言" is what
# content/i18n recorded for it, which the page never actually showed.
LABEL_PRIOR = {"en": ["Delivery languages"],
               "zh": ["出海中东", "交付语言"],
               "ar": ["لغات التنفيذ"]}
LABEL_NEW = {"en": "Interface languages", "zh": "界面语言", "ar": "لغات الواجهة"}

# The value. English and Arabic already listed the three languages and keep
# doing so; the Chinese did not, and the Arabic listed them in a different
# order in content/i18n than the page shipped.
VALUE_PRIOR = {"en": ["10+ languages"],
               "zh": ["10+ 年中东本地经验", "中东本地交付"],
               "ar": ["أكثر من 10 لغات", "الإنجليزية · العربية · الصينية"]}
VALUE_NEW = {"en": "English · Arabic · Chinese", "zh": "英文 · 阿拉伯文 · 中文",
             "ar": "العربية · الإنجليزية · الصينية"}

# The same credential as a sentence, in content/i18n only.
SENTENCE_PRIOR = {"en": ["Delivery in English, Arabic and Chinese"],
                  "zh": ["支持英文、阿拉伯文、中文交付"],
                  "ar": ["التنفيذ والدعم بالعربية والإنجليزية والصينية"]}
SENTENCE_NEW = {"en": "Product interfaces in English, Arabic and Chinese",
                "zh": "产品界面提供英文、阿拉伯文与中文",
                "ar": "واجهات المنتج بالعربية والإنجليزية والصينية"}

SLOTS = [("label", LABEL_PRIOR, LABEL_NEW),
         ("value", VALUE_PRIOR, VALUE_NEW),
         ("sentence", SENTENCE_PRIOR, SENTENCE_NEW)]

# The template is JSON-encoded, so a replacement carrying a quote, a backslash
# or a "</" would have to be escaped to match how the payload is written. None
# of these does; this refuses rather than silently truncating a page.
for _, _, new in SLOTS:
    for code, text in new.items():
        if any(c in text for c in '"\\<>&'):
            sys.exit(f"{code}: replacement contains a character that needs escaping")


def main():
    print(f"\n  {'file':<26} {'label':>6} {'value':>6} {'sent':>6}   status")
    print("  " + "-" * 60)

    changed, done, failed = 0, 0, []
    for rel in FILES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")

        counts = {}
        for name, prior, new in SLOTS:
            counts[name] = sum(text.count(p) for c in LANGS for p in prior[c]
                               if p != new[c])

        if not any(counts.values()):
            already = sum(text.count(new[c]) for _, _, new in SLOTS for c in LANGS)
            status = "already done" if already else "NOT FOUND"
            print(f"  {rel:<26} {'—':>6} {'—':>6} {'—':>6}   {status}")
            if already:
                done += 1
            else:
                failed.append(rel)
            continue

        for name, prior, new in SLOTS:
            for code in LANGS:
                for p in prior[code]:
                    if p != new[code]:
                        text = text.replace(p, new[code])
        path.write_text(text, encoding="utf-8")

        # Nothing of an old wording may survive anywhere in the file — the
        # prerendered copy carries it as well as the DICT, and a page that
        # disagrees with itself is worse than one that is merely out of date.
        after = path.read_text(encoding="utf-8")
        leftover = sum(after.count(p) for _, prior, new in SLOTS
                       for c in LANGS for p in prior[c] if p != new[c])
        row = " ".join(f"{counts[n]:>6}" for n, _, _ in SLOTS)
        if leftover:
            print(f"  {rel:<26} {row}   {leftover} left behind")
            failed.append(rel)
            continue
        print(f"  {rel:<26} {row}   replaced")
        changed += 1

    if failed:
        sys.exit(f"\n  Failed: {', '.join(failed)} — the wording changed upstream.\n")
    print(f"\n  {changed} file(s) rewritten, {done} already current.\n")


if __name__ == "__main__":
    main()
