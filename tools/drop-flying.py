#!/usr/bin/env python3
"""
Remove Flying from the pages — the product was withdrawn from the site.

    python3 tools/drop-flying.py [--check]

Run AFTER localise.py and link-faq.py, and BEFORE prerender.py: this edits the
Design Canvas DICT, and prerender.py is what turns the edited DICT into the
static copy a crawler reads. Running it after prerender leaves the rendered
block still advertising the product.

Re-run after a re-export. The copy lives in the Canvas source, so an export
brings Flying back — the same reason tools/privacy-cookies.py exists.

Three shapes of edit, because Flying appears in three shapes:

  * a bullet in the home page's second pillar — one line of the DICT;
  * a whole group on the solutions page — title plus five items;
  * clauses inside sentences, on the solutions and about pages.

The first two are removals, and both carry quotes and newlines. The DICT is
inside a JSON-encoded template, where those are escaped, so they cannot be
matched as plain text the way privacy-cookies.py matches its paragraph. The
template is decoded, edited and re-encoded instead — escaping "</", which
json.dumps does not do and which would otherwise end the enclosing <script>
early and truncate the page.

The sentence edits are plain text: none of those strings carries a quote or a
newline, so one replacement reaches both the DICT and the prerendered copy.

What the sentences had to say differently. The solutions section grouped its
delivery guarantees under "Across both", which had two systems to be across;
with Flying gone there is one, so the heading no longer describes anything.
The section's footnote and the about page's story paragraph each named Flying
in a list of two, and now name one.

The <head> is not touched. Titles, descriptions and the JSON-LD offer catalogue
are written by seo-inject.py out of content/i18n, so removing Flying there is
what takes it out of the metadata on all eighteen pages.

The Arabic follows the sentence shapes already in the file.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAGES = ["", "solutions", "about"]
LOCALES = [""] + [c for c in ("zh", "ar") if (ROOT / c / "index.html").exists()]

TEMPLATE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)

# The home pillar bullet: one line of the DICT, removed with it.
BULLETS = [
    "Flying — a cross-border trading system for construction and interior fit-out, "
    "delivered as a tailored solution that matches how each business actually trades",
    "Flying —— 面向建筑装饰行业的跨境贸易系统，以定制化方式交付，贴合各家企业实际的贸易流程",
    "فلاينغ — نظام تجارة عابرة للحدود لقطاع المقاولات والتشطيبات، يُسلَّم كحلّ مفصّل يطابق طريقة عمل كل شركة في تجارتها",
]

# The solutions group: title plus its items, in any of the three languages.
GROUP = re.compile(r'\n *\{ title: "(?:Flying|فلاينغ)[^"]*", items: \[\n.*?\n *\]\},', re.S)

# Sentences that named Flying as one of two.
TEXT = [
    ("Across both", "In every case"),
    ("两个系统共通", "无论哪种方式"),
    ("مشترك بين النظامين", "في جميع الأحوال"),

    ("CarSaas is in development and expected to launch shortly. Flying is delivered as a "
     "tailored solution and can be adapted to how a particular business trades and runs its "
     "projects — tell us about your operation and we will say what would carry over.",
     "CarSaas is in development and expected to launch shortly — tell us about your operation "
     "and we will say what would carry over."),
    ("CarSaas 目前处于研发阶段，预计近期上线。Flying 以定制化方式交付，可根据企业实际的贸易与项目流程调整——欢迎与我们沟通具体场景。",
     "CarSaas 目前处于研发阶段，预计近期上线——欢迎与我们沟通具体场景。"),
    ("كار ساس قيد التطوير ويُتوقّع إطلاقه قريبًا. أما فلاينغ فيُسلَّم كحلّ مفصّل يمكن تكييفه مع طريقة الشركة في تجارتها وإدارة مشاريعها — حدّثنا عن عملياتكم وسنوضّح ما الذي ينطبق منها.",
     "كار ساس قيد التطوير ويُتوقّع إطلاقه قريبًا — حدّثنا عن عملياتكم وسنوضّح ما الذي ينطبق منها."),

    ("including CarSaas for automotive trading and Flying for cross-border fit-out trading;",
     "including CarSaas for automotive trading;"),
    ("行业管理方案（面向汽贸的 CarSaas 与面向建筑装饰跨境贸易的 Flying）",
     "行业管理方案（面向汽贸的 CarSaas）"),
    ("ومنها كار ساس لتجارة السيارات وفلاينغ للتجارة العابرة للحدود في التشطيبات؛",
     "ومنها كار ساس لتجارة السيارات؛"),
]

# A replacement carrying a quote, a backslash or a "</" would have to be
# escaped to match how the template is written; none of these does.
for _, new in TEXT:
    if any(c in new for c in '"\\<>&'):
        sys.exit(f"replacement contains a character that needs escaping: {new[:40]!r}")


def edit_template(html):
    """Remove the bullet and the group from the DICT, inside the encoded template."""
    match = TEMPLATE.search(html)
    if not match:
        return html, 0, 0
    template = json.loads(match.group(2))

    bullets = 0
    for bullet in BULLETS:
        template, n = re.subn(r'\n *"' + re.escape(bullet) + r'",', "", template)
        bullets += n

    template, groups = GROUP.subn("", template)
    if not bullets and not groups:
        return html, 0, 0

    encoded = json.dumps(template, ensure_ascii=False).replace("</", "<\\/")
    return html[:match.start(2)] + encoded + html[match.end(2):], bullets, groups


def main():
    checking = "--check" in sys.argv
    print(f"\n  {'page':<22} {'bullet':>6} {'group':>6} {'text':>6}")
    print("  " + "-" * 44)

    touched, stale = 0, []
    for locale in LOCALES:
        for page in PAGES:
            path = ROOT / locale / page / "index.html"
            if not path.exists():
                continue
            label = "/" + "/".join(p for p in (locale, page) if p)
            html = original = path.read_text(encoding="utf-8")

            html, bullets, groups = edit_template(html)
            text = 0
            for old, new in TEXT:
                html, n = html.replace(old, new), html.count(old)
                text += n

            if html == original:
                print(f"  {label:<22} {'—':>6} {'—':>6} {'—':>6}   already done")
                continue
            if checking:
                stale.append(label)
            else:
                path.write_text(html, encoding="utf-8")
            print(f"  {label:<22} {bullets:>6} {groups:>6} {text:>6}"
                  + ("   would change" if checking else "   rewritten"))
            touched += 1

    left = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*/index.html")
            if ".claude" not in p.relative_to(ROOT).parts
            and re.search(r"Flying|فلاينغ", p.read_text(encoding="utf-8"))
            and "content" not in p.parts]
    if left and not checking:
        # seo-inject.py owns the head; until it reruns, the metadata still
        # lists the product. Say so rather than let it look finished.
        print(f"\n  Still naming Flying (head only, until seo-inject.py reruns):"
              f"\n    {', '.join(left)}")

    if checking and stale:
        sys.exit(f"\n  Out of date: {', '.join(stale)}\n")
    print(f"\n  {touched} page(s) {'would be ' if checking else ''}rewritten."
          f" Run prerender.py next.\n")


if __name__ == "__main__":
    main()
