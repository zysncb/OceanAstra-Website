#!/usr/bin/env python3
"""
Move the published office address to Churchill Tower 1, Business Bay.

    python3 tools/address.py

Run after prerender.py and BEFORE seo-inject.py, which rebuilds the JSON-LD
and llms.txt from content/company.json. Re-run after a re-export: the address
lives in the Design Canvas DICT, so an export brings the old one back.

The office moved from Dubai Industrial City (Office 08, Building R.SH.038,
Saih Shuaib 2) to 3707, Churchill Tower 1, Business Bay on 2026-10-25. The
address was in twenty-six files and seventeen different shapes — a full line,
a street-only line for PostalAddress.streetAddress, an abbreviated "Dubai,
UAE" form in the company information table on /about/, the four separate
`lines` of content/company.json, a sentence of prose in the FAQ, and the map
link and geo coordinates — in three languages. All of them are listed below,
because an address that is only half moved is worse than one that is wholly
out of date: a visitor comparing the footer against the FAQ, or a verifier
comparing the page against the structured data, sees the company disagreeing
with itself about where it is.

FORMS holds every shape, each with every wording that shape has carried,
newest last. That list is the point of the tool: a re-export restores the
*export's* address, not whatever the site said yesterday, so matching only the
current text would leave the tool unable to fix the one case it exists for.
Moving again means adding a wording here, not editing one.

Replacements run longest-first, which is what makes the overlapping shapes
safe. The full line contains the street-only line, which contains line 1; the
Arabic full line contains both Arabic lines; the map URL contains both
coordinates. Replacing the longest match first consumes each outer shape
before its own parts can be matched out from under it.

The Chinese and Arabic renderings follow the shapes already in the file:
Chinese keeps the building name in English and names the district in Chinese
with the English in parentheses; Arabic translates both (برج تشرشل for
Churchill Tower, الخليج التجاري for Business Bay, the standard name). The
Arabic FAQ sentence uses Arabic-Indic digits, as it did for the old address.
Both should be read by a native speaker before they are relied on.

Coordinates are the Churchill Tower 1 place marker on Google Maps, from the
link the move was given with (https://maps.app.goo.gl/TS4c5Th98nBC1Zd19).

NOTE: the old address is the one printed on trade licence 1646635 and recorded
against D-U-N-S 851077092. Publishing this one puts the site ahead of both
registers until they are amended; see _needsReview in content/company.json.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every file the address appears in. The six Design Canvas pages carry it in
# three places each — the injected JSON-LD, the prerendered body, and the DICT
# inside __bundler/template — and the pages that only show it in the footer
# carry it in the first two. /faq/ carries the prose sentence, llms.txt the
# generated line, README.md the company information table in the docs.
FILES = [
    "index.html", "solutions/index.html", "about/index.html",
    "contact/index.html", "privacy/index.html", "terms/index.html",
    "zh/index.html", "zh/solutions/index.html", "zh/about/index.html",
    "zh/contact/index.html", "zh/privacy/index.html", "zh/terms/index.html",
    "ar/index.html", "ar/solutions/index.html", "ar/about/index.html",
    "ar/contact/index.html", "ar/privacy/index.html", "ar/terms/index.html",
    "faq/index.html", "zh/faq/index.html", "ar/faq/index.html",
    "content/company.json", "content/faq.json",
    "llms.txt", "README.md",
]

# name, [every prior wording, newest last], new wording.
FORMS = [
    # English. `full` is what the footer and the contact page print; `street`
    # is PostalAddress.streetAddress, which stops before the city; `uae`
    # abbreviates the country for the company information table on /about/.
    ("en.full", ["Office 08, Building R.SH.038, Saih Shuaib 2, Dubai Industrial City, Dubai, United Arab Emirates"],
     "3707, Churchill Tower 1, Business Bay, Dubai, United Arab Emirates"),
    ("en.uae", ["Office 08, Building R.SH.038, Saih Shuaib 2, Dubai Industrial City, Dubai, UAE"],
     "3707, Churchill Tower 1, Business Bay, Dubai, UAE"),
    ("en.street", ["Office 08, Building R.SH.038, Saih Shuaib 2, Dubai Industrial City"],
     "3707, Churchill Tower 1, Business Bay"),
    ("en.line1", ["Office 08, Building R.SH.038"], "3707, Churchill Tower 1"),
    ("en.line2", ["Saih Shuaib 2, Dubai Industrial City"], "Business Bay"),
    ("en.prose", ["OceanAstra is based in Dubai Industrial City, Dubai, United Arab Emirates, with its registered office at Office 08, Building R.SH.038, Saih Shuaib 2."],
     "OceanAstra is based in Business Bay, Dubai, United Arab Emirates, with its registered office at 3707, Churchill Tower 1."),

    # Chinese. The one-line form runs largest-to-smallest, as a Chinese
    # address does; line 1 is shared with the English and is replaced by
    # en.line1 above.
    ("zh.full", ["阿拉伯联合酋长国 迪拜 迪拜工业城 Saih Shuaib 2 R.SH.038 楼 08 室"],
     "阿拉伯联合酋长国 迪拜 商务湾 Churchill Tower 1 3707 室"),
    ("zh.line2", ["Saih Shuaib 2，迪拜工业城"], "商务湾（Business Bay）"),
    ("zh.prose", ["OceanAstra 位于阿拉伯联合酋长国迪拜的迪拜工业城，注册办公地址为 Saih Shuaib 2，R.SH.038 楼 08 室。"],
     "OceanAstra 位于阿拉伯联合酋长国迪拜的商务湾（Business Bay），注册办公地址为 Churchill Tower 1，3707 室。"),

    # Arabic. `short` is the company information table's form, which drops
    # رقم and the country; the prose sentence uses Arabic-Indic digits.
    ("ar.full", ["مكتب رقم 08، مبنى R.SH.038، سيح شعيب 2، مدينة دبي الصناعية، دبي، الإمارات العربية المتحدة"],
     "مكتب رقم 3707، برج تشرشل 1، الخليج التجاري، دبي، الإمارات العربية المتحدة"),
    ("ar.short", ["مكتب 08، مبنى R.SH.038، سيح شعيب 2، مدينة دبي الصناعية، دبي"],
     "مكتب 3707، برج تشرشل 1، الخليج التجاري، دبي"),
    ("ar.line1", ["مكتب رقم 08، مبنى R.SH.038"], "مكتب رقم 3707، برج تشرشل 1"),
    ("ar.line2", ["سيح شعيب 2، مدينة دبي الصناعية"], "الخليج التجاري"),
    ("ar.prose", ["يقع مقر أوشن أسترا في مدينة دبي الصناعية بدبي، الإمارات العربية المتحدة، وعنوانها المسجّل هو مكتب رقم ٠٨، مبنى R.SH.038، سيح شعيب ٢."],
     "يقع مقر أوشن أسترا في الخليج التجاري بدبي، الإمارات العربية المتحدة، وعنوانها المسجّل هو مكتب رقم ٣٧٠٧، برج تشرشل ١."),

    # The map link and the geo coordinates. The link is listed before the bare
    # numbers only for readability; the longest-first ordering is what makes
    # it safe.
    ("map", ["https://www.google.com/maps?q=24.8260152,55.1065874"],
     "https://www.google.com/maps?q=25.181282,55.2621665"),
    ("lat", ["24.8260152"], "25.181282"),
    ("lon", ["55.1065874"], "55.2621665"),
]

# Nothing of the old address may survive anywhere, in any shape. These are the
# fragments no wording of the new address contains, so a non-zero count after
# the rewrite means a shape was missed rather than that a file was skipped.
RESIDUE = ["R.SH.038", "Saih Shuaib", "Dubai Industrial City", "迪拜工业城",
           "سيح شعيب", "مدينة دبي الصناعية", "24.8260152", "55.1065874"]

# The template is JSON-encoded, so a replacement carrying a quote, a backslash
# or a "</" would have to be escaped to match how the payload is written. None
# of these does; this refuses rather than silently truncating a page.
for name, _, new in FORMS:
    if any(c in new for c in '"\\<>&'):
        sys.exit(f"{name}: replacement contains a character that needs escaping")

# Longest first, so an outer shape is consumed before its own parts.
PAIRS = sorted(((p, new) for _, prior, new in FORMS for p in prior if p != new),
               key=lambda pair: -len(pair[0]))


def main():
    print(f"\n  {'file':<28} {'edits':>6}   status")
    print("  " + "-" * 56)

    changed, done, failed = 0, 0, []
    for rel in FILES:
        path = ROOT / rel
        if not path.exists():
            print(f"  {rel:<28} {'—':>6}   MISSING")
            failed.append(rel)
            continue

        text = path.read_text(encoding="utf-8")
        edits = sum(text.count(p) for p, _ in PAIRS)

        if not edits:
            already = sum(text.count(new) for _, _, new in FORMS)
            status = "already moved" if already else "NOT FOUND"
            print(f"  {rel:<28} {'—':>6}   {status}")
            if already:
                done += 1
            else:
                failed.append(rel)
            continue

        for prior, new in PAIRS:
            text = text.replace(prior, new)
        path.write_text(text, encoding="utf-8")

        after = path.read_text(encoding="utf-8")
        leftover = {r: after.count(r) for r in RESIDUE if r in after}
        if leftover:
            print(f"  {rel:<28} {edits:>6}   left behind: {leftover}")
            failed.append(rel)
            continue
        print(f"  {rel:<28} {edits:>6}   rewritten")
        changed += 1

    if failed:
        sys.exit(f"\n  Failed: {', '.join(failed)} — the wording changed upstream.\n")
    print(f"\n  {changed} file(s) rewritten, {done} already current.\n")


if __name__ == "__main__":
    main()
