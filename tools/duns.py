#!/usr/bin/env python3
"""
Print the D-U-N-S number on /about/, so the structured data may carry it too.

    python3 tools/duns.py

Run after prerender.py and BEFORE seo-inject.py, which reads the number from
content/company.json and emits it as Organization.duns — but may only do so
because this puts it on the page first. seo-inject.py's rule, and Google's
structured data policy behind it, is that every value in the markup has a
visible counterpart in the page. The three registry numbers already there
(trade licence, commercial register, Dubai Chamber) each satisfy that; a
D-U-N-S emitted without this edit would have been the first that did not.

It goes in the "Company information" table on /about/, immediately after the
Dubai Chamber membership row, which keeps the registry identifiers together
and ahead of the address and contact rows.

Two edits per page, the same two the FAQ link needed: the row goes into each
language's `fields` array inside the template's DICT, so it follows whatever
language the page is showing, and again into the prerendered copy in that
page's own language, because that copy is what a crawler that does not run
JavaScript reads — which is most of the AI crawlers this site is written for.

The DICT rows are edited as text rather than by decoding the template. The
payload is JSON, so the array reads [\\"label\\", \\"value\\", \\"ltr\\"] with the
quotes escaped, and matching that directly avoids a re-encode — the step where
an unescaped "</" truncates the page. Nothing inserted here contains one.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["about/index.html", "zh/about/index.html", "ar/about/index.html"]
LOCALE_OF = {"about/index.html": "en", "zh/about/index.html": "zh", "ar/about/index.html": "ar"}

# The row this one follows: the last of the registry identifiers.
AFTER = {"en": "Dubai Chamber membership", "zh": "迪拜商会会员号", "ar": "عضوية غرفة تجارة دبي"}
AFTER_VALUE = "698189"

LABEL = {"en": "D-U-N-S® Number", "zh": "D-U-N-S® 编号", "ar": "رقم D-U-N-S®"}

TEMPLATE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)


def dict_row(label, value):
    """A `fields` entry as it appears inside the JSON-encoded template."""
    return f'[\\"{label}\\", \\"{value}\\", \\"ltr\\"],'


def prerendered_row(html, label):
    """The rendered <div> for one field, matched so it can be cloned."""
    return re.compile(
        r'<div data-dc-tpl="58"[^>]*>\s*'
        r'<span data-dc-tpl="59"[^>]*><span class="sc-interp">' + re.escape(label) + r'</span></span>\s*'
        r'<span data-dc-tpl="60"[^>]*><span class="sc-interp">' + AFTER_VALUE + r'</span></span>\s*'
        r'</div>(\s*)', re.S).search(html)


def main():
    duns = json.loads((ROOT / "content/company.json").read_text(encoding="utf-8"))["dunsNumber"]
    if not re.fullmatch(r"\d{9}", duns or ""):
        sys.exit(f"\n  content/company.json has no usable dunsNumber ({duns!r}).\n")

    print(f"\n  D-U-N-S {duns}\n")
    print(f"  {'page':<24} {'dict rows':>9} {'prerendered':>12}")
    print("  " + "-" * 50)

    failed = []
    for rel in PAGES:
        path = ROOT / rel
        html = path.read_text(encoding="utf-8")
        if duns in html:
            print(f"  {rel:<24} {'already on the page':>22}")
            continue

        added = 0
        for code, label in LABEL.items():
            anchor = dict_row(AFTER[code], AFTER_VALUE)
            if html.count(anchor) != 1:
                continue
            html = html.replace(anchor, anchor + " " + dict_row(label, duns), 1)
            added += 1

        # The prerendered copy is in this page's language only.
        own = LOCALE_OF[rel]
        match = prerendered_row(html, AFTER[own])
        cloned = 0
        if match:
            block, gap = match.group(0)[:match.group(0).rindex("</div>") + 6], match.group(1)
            clone = block.replace(f'>{AFTER[own]}</span>', f'>{LABEL[own]}</span>')
            clone = clone.replace(f'>{AFTER_VALUE}</span>', f'>{duns}</span>')
            html = html[:match.start()] + block + gap + clone + gap + html[match.end():]
            cloned = 1

        if added != 3 or cloned != 1:
            print(f"  {rel:<24} {added:>9} {cloned:>12}   <- expected 3 and 1")
            failed.append(rel)
            continue

        path.write_text(html, encoding="utf-8")

        # The template must still round-trip: a stray "</" would have ended the
        # script element early and silently truncated the page.
        reread = path.read_text(encoding="utf-8")
        try:
            template = json.loads(TEMPLATE.search(reread).group(2))
        except Exception as exc:
            print(f"  {rel:<24} template no longer decodes: {exc}")
            failed.append(rel)
            continue
        if template.count(duns) != 3:
            print(f"  {rel:<24} {template.count(duns)} DICT rows after write, expected 3")
            failed.append(rel)
            continue

        print(f"  {rel:<24} {added:>9} {cloned:>12}")

    if failed:
        sys.exit(f"\n  Failed: {', '.join(failed)} — the about page's field table changed.\n")
    print("\n  Now run tools/seo-inject.py to put it in the structured data.\n")


if __name__ == "__main__":
    main()
