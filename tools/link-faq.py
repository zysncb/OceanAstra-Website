#!/usr/bin/env python3
"""
Add the FAQ to the footer of every exported page.

    python3 tools/link-faq.py

Run AFTER localise.py and BEFORE prerender.py.

/faq/ is built by tools/build-faq.py and is not part of the Design Canvas
export, so nothing on the site links to it. A page reachable only from
sitemap.xml is an orphan: crawlers discount it, and a visitor cannot find it at
all. This puts it beside the privacy and terms links in the footer.

Only the home page of each locale carries those links — the inner pages ship a
footer holding a copyright line and nothing else — so that is where the link
goes. One link from the most authoritative page on the site is enough for
discovery; putting FAQ in the header nav would be better, and belongs in the
next Design Canvas export rather than in a patch over generated code.

Two edits per page, both inside the template:

  - the label goes into each language's `footer` object in DICT, so it follows
    the client-side language switcher rather than freezing in one language;
  - the anchor copies the relative prefix from the privacy link next to it,
    because the export writes "privacy/" at the root and "../privacy/" one level
    down, and a hardcoded path would 404 on five pages out of six.

This is post-processing over generated code and a re-export will discard it,
which is true of everything prepare-export.py does — the pipeline is meant to be
re-run.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["", "solutions", "about", "contact", "privacy", "terms"]
LOCALES = ["", "zh", "ar"]

LABEL = {"en": "FAQ", "zh": "常见问题", "ar": "الأسئلة الشائعة"}

TEMPLATE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)
FOOTER_OBJ = re.compile(r'(footer:\s*\{)')
PRIVACY_LINK = re.compile(r'<a href="((?:\.\./)*)privacy/"([^>]*)>\{\{ t\.footer\.privacy \}\}</a>')

# DICT entries open as `zh: { dir: "ltr", …`, which is what identifies the
# language a footer object belongs to. Sniffing the text near the object is not
# enough: the footer objects are short, and a fixed window runs past the end of
# one language block into the next — which put an Arabic label on the English
# page.
LANG_BLOCK = re.compile(r'\b(zh|en|ar):\s*\{\s*dir:')


def add_labels(template):
    """Insert `faq:` into every language's footer object in DICT."""
    blocks = [(m.start(), m.group(1)) for m in LANG_BLOCK.finditer(template)]
    if not blocks:
        return template, 0

    def language_at(pos):
        found = None
        for start, code in blocks:
            if start < pos:
                found = code
            else:
                break
        return found

    out, last, added = [], 0, 0
    for m in FOOTER_OBJ.finditer(template):
        code = language_at(m.start())
        if code is None:
            continue
        if re.match(r'\s*faq:', template[m.end():m.end() + 12]):
            continue
        out.append(template[last:m.end()])
        out.append(f' faq: "{LABEL[code]}",')
        last = m.end()
        added += 1
    out.append(template[last:])
    return "".join(out), added


def add_anchor(template):
    """Put the FAQ link before the privacy link, sharing its relative prefix."""
    def insert(m):
        prefix, attrs = m.group(1), m.group(2)
        return (f'<a href="{prefix}faq/"{attrs}>{{{{ t.footer.faq }}}}</a> ' + m.group(0))

    template, count = PRIVACY_LINK.subn(insert, template)
    return template, count


def main():
    print(f"\n  {'page':<24} {'labels':>7} {'anchor':>9}")
    print("  " + "-" * 44)
    total = 0
    for locale in LOCALES:
        for page in PAGES:
            rel = f"{page}/index.html" if page else "index.html"
            path = ROOT / (rel if not locale else f"{locale}/{rel}")
            html = path.read_text(encoding="utf-8")

            counts = [0, 0]

            def patch(m):
                template = json.loads(m.group(2))
                template, counts[0] = add_labels(template)
                template, counts[1] = add_anchor(template)
                # Re-encoding must escape "</" — the template contains a nested
                # </script> and leaving it literal truncates the page.
                encoded = json.dumps(template, ensure_ascii=False).replace("</", "<\\/")
                return m.group(1) + encoded + m.group(3)

            html = TEMPLATE.sub(patch, html, count=1)
            label = (locale + "/" if locale else "/") + (page or "")
            if counts[1] == 0:
                print(f"  {label:<24} {'—':>7} {'no slot':>9}")
                continue
            path.write_text(html, encoding="utf-8")
            print(f"  {label:<24} {counts[0]:>7} {counts[1]:>9}")
            total += 1
    if total == 0:
        sys.exit("\n  No page carried a privacy link — the export's footer changed.\n")
    print(f"\n  Linked from {total} page(s); inner pages have no footer link slot.\n")


if __name__ == "__main__":
    main()
