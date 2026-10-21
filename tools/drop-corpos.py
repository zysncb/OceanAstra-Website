#!/usr/bin/env python3
"""
Turn line 01 from CorpOS into the Lark digital workplace.

    python3 tools/drop-corpos.py [--check]

Run AFTER drop-flying.py and add-invobay.py, and BEFORE prerender.py: this
edits the Design Canvas DICT, and prerender.py is what turns the edited DICT
into the static copy a crawler reads.

Re-run after a re-export. Design Canvas still has CorpOS as line 01 and has
never heard of the reseller agreement, so every export brings the old line
back — the same reason tools/drop-flying.py and tools/add-invobay.py exist.

What changed, and why it is one tool rather than two. CorpOS was withdrawn
from the site (company decision, 2026-10-21) while it is unreleased. It was
not one product inside line 01; it was the whole of that line's "Solutions"
group, so removing it alone would have left a line with a heading, an
audience and nothing in between. Lark moved up from a bullet in line 03 into
line 01 in its place, which is what the signed reseller agreement makes it:
the line the company actually sells today. The site therefore still has three
lines, and line 03 keeps Amap and the platforms assessed case by case.

Where the copy comes from. Everything written into line 01 is read at run
time from content/i18n/{en,zh,ar}.json — title, badge, summary, points, lede,
paragraphs, groups and footnote — so the copy is written once, in the file
that is the source of truth for it, and this tool only decides where it goes.
The same is true of line 03's bullets, the integration footnote and the about
page's story paragraph. ANCHORS holds the page's own previous wording, which
is what the replacements are matched against; those strings are history and do
not exist in content/ any more.

TEXT is the exception: three sentences that frame the three lines in prose
rather than listing them — the home page's "what we do" lede and its about
card, and the solutions hero — live only in the Canvas source, so both sides
of each replacement are written here. All three named line 01 by what it used
to be ("how a company is organised", "from the organisation to the industry").

Two claims deliberately not made. The copy says Lark is supplied under a
signed reseller agreement and invoiced in AED against a purchase order; it
does not promise VAT on the invoice, which waits on VAT registration, and it
does not promise support in any particular language — the company withdrew the
trilingual delivery and support promise on 2026-08-21 and nothing here puts it
back. Both are service commitments that need people and paperwork behind them,
not product facts.

The <head> is not this tool's business. Titles, descriptions and the JSON-LD
offer catalogue are written by seo-inject.py out of content/i18n, and
rerunning it is what takes CorpOS out of the metadata on all eighteen pages.
A replacement does reach the copy of the line title the catalogue carries,
which costs nothing and keeps the page from disagreeing with itself in
between.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAGES = ["", "solutions", "about"]
LOCALES = [""] + [c for c in ("zh", "ar") if (ROOT / c / "index.html").exists()]
LANGS = ("en", "zh", "ar")

TEMPLATE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)

I18N = {L: json.loads((ROOT / f"content/i18n/{L}.json").read_text(encoding="utf-8"))
        for L in LANGS}

# The page's own earlier wording. Kept here because content/ no longer has it:
# a re-export restores these, so matching them is what lets this tool run again.
ANCHORS = {
 "en": {
  "priorTitles": ["AI Organisation Solutions", "Digital Workplace"],
  "badge": "CorpOS in active development",
  "line2": "Industry Management Solutions",
  "line3": "Integration Partnerships",
  "larkBullet": "Lark — deployment and integration of the all-in-one digital workplace across the region",
  "larkItem": "Lark — messaging, documents, approvals, calendar and company directory brought together as a single digital workplace",
  "footnote": "Lark and Amap are trademarks",
  "story": "We work across three lines: ",
 },
 "zh": {
  "priorTitles": ["AI 组织方案", "数字化办公平台"],
  "badge": "CorpOS 研发进行中",
  "line2": "行业管理方案",
  "line3": "集成合作方案",
  "larkBullet": "Lark —— 一体化数字办公平台的中东落地与集成",
  "larkItem": "Lark（飞书国际版）—— 即时消息、文档、审批、日历与组织通讯录一体化的数字办公平台",
  "footnote": "Lark 与 Amap 为其各自权利人的商标。",
  "story": "我们的业务分为三条线：",
 },
 "ar": {
  "priorTitles": ["حلول التنظيم بالذكاء الاصطناعي", "بيئة العمل الرقمية"],
  "badge": "كورب أو إس قيد التطوير",
  "line2": "حلول الإدارة القطاعية",
  "line3": "حلول التكامل والشراكات",
  "larkBullet": "لارك — نشر وتكامل بيئة العمل الرقمية المتكاملة في المنطقة",
  "larkItem": "لارك (Lark) — المراسلة والمستندات والاعتمادات والتقويم ودليل الشركة مجتمعة في بيئة عمل رقمية واحدة",
  "footnote": "لارك (Lark) وأماب (Amap) علامتان تجاريتان",
  "story": "نعمل عبر ثلاثة خطوط: ",
 },
}

# Sentences that frame the three lines in prose. These live only in the Canvas
# source, so unlike everything else here both sides are written out. Each named
# line 01 by what it used to be, and each entry carries every wording the page
# has shipped — the export's own, and the ones this tool wrote on earlier runs
# — so the sentence can be corrected again without stranding the pages that
# already took the previous correction. tools/credential-language.py keeps its
# PRIOR list for the same reason.
TEXT = [
    (["From how a company is organised, to the systems an industry runs on",
      "From the platform a company works on, to the systems an industry runs on"],
     "From the platform a company works on, to the systems an industry runs on"),
    (["从组织方式，到行业系统", "从日常办公平台，到行业系统"], "从日常办公平台，到行业系统"),
    (["من طريقة تنظيم الشركة، إلى الأنظمة التي يقوم عليها القطاع",
      "من المنصّة التي تعمل عليها الشركة، إلى الأنظمة التي يقوم عليها القطاع"],
     "من المنصّة التي تعمل عليها الشركة، إلى الأنظمة التي يقوم عليها القطاع"),

    # The same sentence's tail. CorpOS was what carried the company's own AI
    # claim; with it gone the three lines needed to say the word themselves.
    (["all three point at the same thing: advanced productivity that is genuinely used inside enterprises here."],
     "all three point at the same thing: AI and advanced productivity genuinely used inside enterprises here."),
    (["三条线指向同一件事：让先进生产力在中东企业里真正用起来。"],
     "三条线指向同一件事：让 AI 与先进生产力在中东企业里真正用起来。"),
    (["تشير الخطوط الثلاثة إلى الغاية نفسها: إنتاجية متقدّمة تُستخدم فعلًا داخل مؤسسات المنطقة."],
     "تشير الخطوط الثلاثة إلى الغاية نفسها: ذكاء اصطناعي وإنتاجية متقدّمة يُستخدمان فعلًا داخل مؤسسات المنطقة."),

    (["We provide AI organisation solutions, industry management solutions",
      "We provide the digital workplace, industry management solutions"],
     "We provide the AI workplace, industry management solutions"),
    (["提供 AI 组织方案、行业管理方案与集成合作方案", "提供数字化办公平台、行业管理方案与集成合作方案"],
     "提供 AI 办公平台、行业管理方案与集成合作方案"),
    (["نقدّم حلول التنظيم بالذكاء الاصطناعي، وحلول الإدارة القطاعية",
      "نقدّم بيئة العمل الرقمية، وحلول الإدارة القطاعية"],
     "نقدّم بيئة العمل بالذكاء الاصطناعي، وحلول الإدارة القطاعية"),

    (["From the organisation to the industry, AI that actually lands.",
      "From the workplace to the industry, technology that actually lands."],
     "From the workplace to the industry, AI that actually lands."),
    (["从组织到行业，让 AI 真正落地。", "从日常办公到行业系统，让技术真正落地。"],
     "从日常办公到行业系统，让 AI 真正落地。"),
    (["من المؤسسة إلى القطاع، ذكاء اصطناعي يصل إلى أرض الواقع.",
      "من بيئة العمل إلى القطاع، تقنية تصل إلى أرض الواقع."],
     "من بيئة العمل إلى القطاع، ذكاء اصطناعي يصل إلى أرض الواقع."),
]

# A replacement carrying a quote, a backslash or a "</" would have to be
# escaped to match how the template is written; none of these does.
for _, new in TEXT:
    if any(c in new for c in '"\\<>&'):
        sys.exit(f"replacement contains a character that needs escaping: {new[:40]!r}")


def copy_for(lang):
    """The new line 01, and the three other pieces, out of content/i18n."""
    d = I18N[lang]
    return {
        "pillar": d["home"]["pillars"]["items"][0],
        "section": d["solutions"]["sections"][0],
        "line3points": d["home"]["pillars"]["items"][2]["points"],
        "footnote": d["solutions"]["sections"][2]["note"],
        "story": d["about"]["story"]["paragraphs"][2],
    }


def js_string(text):
    """How the DICT writes a string. Refuses anything needing an escape."""
    if any(c in text for c in '"\\\n'):
        sys.exit(f"copy needs escaping, which this tool does not do: {text[:48]!r}")
    return f'"{text}"'


def link_tail(c, indent):
    """The link and its label, in the shape add-invobay.py's markup reads. Only
    an entry carrying a link renders an anchor, so the rest are unaffected."""
    if not c.get("link"):
        return ""
    return (f',\n{indent}link: {js_string(c["link"])}'
            f',\n{indent}linkLabel: {js_string(c["linkLabel"])}')


def render_pillar(c):
    """The home page's line object: eight spaces in, points twelve."""
    points = ",\n".join(f"            {js_string(p)}" for p in c["points"])
    return (f"        {{\n"
            f"          title: {js_string(c['title'])},\n"
            f"          tag: {js_string(c['badge'])},\n"
            f"          summary: {js_string(c['summary'])},\n"
            f"          points: [\n{points}\n"
            f"          ]{link_tail(c, '          ')}\n"
            f"        }},\n")


def render_section(c):
    """The solutions page's line object: six spaces in, group items twelve."""
    paras = ",\n".join(f"          {js_string(p)}" for p in c["body"])
    groups = ",\n".join(
        "          {{ title: {}, items: [\n{}\n          ]{} }}".format(
            js_string(g["title"]),
            ",\n".join(f"            {js_string(i)}" for i in g["items"]),
            (f', link: {js_string(g["link"])}, linkLabel: {js_string(g["linkLabel"])}'
             if g.get("link") else ""))
        for g in c["groups"])
    return (f"      {{\n"
            f"        title: {js_string(c['title'])}, tag: {js_string(c['badge'])},\n"
            f"        lede: {js_string(c['lede'])},\n"
            f"        paras: [\n{paras}\n        ],\n"
            f"        groups: [\n{groups}\n        ],\n"
            f"        footnote: {js_string(c['note'])}\n"
            f"      }},\n")


def replace_string(template, prefix, new):
    """Swap the whole DICT string that opens with prefix. None of them
    carries a quote, so the next one closes the string."""
    rx = re.compile(r'"' + re.escape(prefix) + r'[^"]*"')
    return rx.subn(js_string(new), template, count=1)


def edit_template(html):
    """Rewrite line 01, and the four places that named it, inside the DICT."""
    match = TEMPLATE.search(html)
    if not match:
        return html, 0
    template = json.loads(match.group(2))
    edits = 0

    for lang in LANGS:
        c, a = copy_for(lang), ANCHORS[lang]

        # Every title this line has carried, the one in content/i18n included,
        # so a run both converts an export and re-applies a later copy change.
        titles = "(?:%s)" % "|".join(
            re.escape(t) for t in a["priorTitles"] + [c["pillar"]["title"]])

        # Line 01 on the home page, replaced whole. Anchored on the line that
        # follows it, because the DICT holds all three languages and the first
        # closing brace at that indent is not reliably this line's.
        template, n = re.subn(
            r'(\n      lines: \[\n)'
            r'        \{\n          title: "' + titles + r'",\n.*?\n        \},\n'
            r'(?=        \{\n          title: "' + re.escape(a["line2"]) + r'",)',
            lambda m: m.group(1) + render_pillar(c["pillar"]),
            template, count=1, flags=re.S)
        edits += n

        # Line 01 on the solutions page, which is the same object with prose.
        template, n = re.subn(
            r'(\n    lines: \[\n)'
            r'      \{\n        title: "' + titles + r'", tag: "[^"]*",\n.*?\n      \},\n'
            r'(?=      \{\n        title: "' + re.escape(a["line2"]) + r'",)',
            lambda m: m.group(1) + render_section(c["section"]),
            template, count=1, flags=re.S)
        edits += n

        # Line 03's bullets on the home page: Lark left, so the line now leads
        # with Amap and says outright that the rest is assessed case by case.
        if a["larkBullet"] in template:
            points = ",\n".join(f"            {js_string(p)}" for p in c["line3points"])
            template, n = re.subn(
                r'(title: "' + re.escape(a["line3"]) + r'",\n          tag: "",\n'
                r'          summary: "[^"]*",\n          points: \[\n)'
                r'(?:[^\n]*\n)*?(          \])',
                lambda m: m.group(1) + points + "\n" + m.group(2),
                template, count=1)
            edits += n

        # Lark's entry in the platforms group, one line of the DICT.
        template, n = re.subn(
            r'\n *"' + re.escape(a["larkItem"]) + r'",', "", template)
        edits += n

        # The integration footnote now says where Lark went.
        template, n = replace_string(template, a["footnote"], c["footnote"])
        edits += n

        # The about page's story paragraph, which lists the three lines.
        template, n = replace_string(template, a["story"], c["story"])
        edits += n

    for olds, new in TEXT:
        for old in olds:
            if old == new:
                continue
            edits += template.count(old)
            template = template.replace(old, new)

    # Whatever still names line 01 by its old title — the footer's solutions
    # list, and the offer catalogue until seo-inject.py reruns.
    for lang in LANGS:
        a, c = ANCHORS[lang], copy_for(lang)
        for old in a["priorTitles"] + [a["badge"]]:
            new = c["pillar"]["badge"] if old == a["badge"] else c["pillar"]["title"]
            if old == new:
                continue
            edits += template.count(old)
            template = template.replace(old, new)

    if not edits:
        return html, 0
    encoded = json.dumps(template, ensure_ascii=False).replace("</", "<\\/")
    return html[:match.start(2)] + encoded + html[match.end(2):], edits


def main():
    checking = "--check" in sys.argv
    print(f"\n  {'page':<22} {'edits':>6}")
    print("  " + "-" * 30)

    touched, stale = 0, []
    for locale in LOCALES:
        for page in PAGES:
            path = ROOT / locale / page / "index.html"
            if not path.exists():
                continue
            label = "/" + "/".join(p for p in (locale, page) if p)
            html = original = path.read_text(encoding="utf-8")

            html, edits = edit_template(html)

            if html == original:
                print(f"  {label:<22} {'—':>6}   already done")
                continue
            if checking:
                stale.append(label)
            else:
                path.write_text(html, encoding="utf-8")
            print(f"  {label:<22} {edits:>6}"
                  + ("   would change" if checking else "   rewritten"))
            touched += 1

    left = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*/index.html")
            if ".claude" not in p.relative_to(ROOT).parts
            and re.search(r"CorpOS|كورب أو إس", p.read_text(encoding="utf-8"))
            and "content" not in p.parts]
    if left and not checking:
        # seo-inject.py owns the head; until it reruns, the metadata still
        # names the product. Say so rather than let it look finished.
        print(f"\n  Still naming CorpOS (head only, until seo-inject.py reruns):"
              f"\n    {', '.join(left)}")

    if checking and stale:
        sys.exit(f"\n  Out of date: {', '.join(stale)}\n")
    print(f"\n  {touched} page(s) {'would be ' if checking else ''}rewritten."
          f" Run prerender.py next.\n")


if __name__ == "__main__":
    main()
