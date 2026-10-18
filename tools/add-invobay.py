#!/usr/bin/env python3
"""
Put Invobay into the pages, inside the industry management line.

    python3 tools/add-invobay.py [--check]

Run AFTER drop-flying.py and BEFORE prerender.py. Order matters both ways:
drop-flying.py leaves the anchors this tool inserts against, and prerender.py
is what turns the edited DICT into the static copy a crawler reads.

Re-run after a re-export. Design Canvas has never heard of Invobay, so an
export produces the industry line with CarSaas alone.

Where the copy comes from. Everything inserted is read at run time from
content/i18n/{en,zh,ar}.json — the bullet, the two groups, the summary, the
lede, the extra paragraph, the group heading and the footnote. The copy is
therefore written once, in the file that is the source of truth for it, and
this tool only decides where it goes. ANCHORS below holds the page's own
previous wording, which is what the replacements are matched against; those
strings are history and do not exist in content/ any more.

Why Invobay sits in line 02 rather than a line of its own: the company's
decision, 2026-10-18. It does change what the line is about — CarSaas is an
industry system a business chooses, while UAE e-invoicing is one it is
required to run, and nothing about Invobay is AI. The line's summary, lede and
an added paragraph say so, rather than letting the AI framing quietly cover a
product that makes no such claim. For the same reason the delivery guarantees
at the end of the section are now headed as being about the industry systems:
they describe how CarSaas is delivered, and several of them — AI teammates, a
deployment on your own infrastructure — are not true of Invobay, which is a
hosted product at invobay.com.

The <head> is not this tool's business — seo-inject.py writes titles,
descriptions and the JSON-LD offer catalogue out of the same content/i18n
files, and rerunning it is what updates them. A replacement does reach the
copy of the line's summary that the offer catalogue carries, which costs
nothing and keeps the page from disagreeing with itself in between.
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

# The page's own earlier wording, which the new copy replaces. Kept here
# because content/ no longer has it: a re-export restores these, so matching
# them is what lets this tool run again.
ANCHORS = {
 "en": {
  "summary": "Either AI teammates who hold defined roles, or AI assistance layered onto existing work — a new way to manage the operations of a specific industry, and a way to bring AI to the systems that industry already runs.",
  "lede": "Either AI teammates who hold defined roles, or AI assistance layered onto existing work — a new operating model for a specific industry, and AI capability for the systems it already runs.",
  "footnote": "CarSaas is in development and expected to launch shortly — tell us about your operation and we will say what would carry over.",
  "delivery": "In every case",
  "about": ("including CarSaas for automotive trading; and integration partnerships",
            "including CarSaas for automotive trading and Invobay for UAE e-invoicing; and integration partnerships"),
 },
 "zh": {
  "summary": "以 AI 职员或 AI 辅助两种方式，在具体行业里构建 AI 业务管理的新范式，也为行业既有的系统方案增强 AI 能力。",
  "lede": "以 AI 职员或 AI 辅助两种方式，构建垂直行业的 AI 业务管理新范式，也为行业的传统系统方案增强 AI 能力。",
  "footnote": "CarSaas 目前处于研发阶段，预计近期上线——欢迎与我们沟通具体场景。",
  "delivery": "无论哪种方式",
  "about": ("行业管理方案（面向汽贸的 CarSaas），以及",
            "行业管理方案（面向汽贸的 CarSaas 与面向阿联酋电子发票的 Invobay），以及"),
 },
 "ar": {
  "summary": "إمّا زملاء رقميون يشغلون أدوارًا محدّدة، أو ذكاء اصطناعي مساند يُضاف إلى العمل القائم — نموذج جديد لإدارة عمليات قطاع بعينه، وقدرة ذكاء اصطناعي تُضاف إلى أنظمته الحالية.",
  "lede": "إمّا زملاء رقميون يشغلون أدوارًا محدّدة، أو ذكاء اصطناعي مساند يُضاف إلى العمل القائم — نموذج تشغيل جديد لقطاع بعينه، وقدرات ذكاء اصطناعي لأنظمته الحالية.",
  "footnote": "كار ساس قيد التطوير ويُتوقّع إطلاقه قريبًا — حدّثنا عن عملياتكم وسنوضّح ما الذي ينطبق منها.",
  "delivery": "في جميع الأحوال",
  "about": ("ومنها كار ساس لتجارة السيارات؛ وحلول التكامل",
            "ومنها كار ساس لتجارة السيارات وإنفوباي (Invobay) للفوترة الإلكترونية في الإمارات؛ وحلول التكامل"),
 },
}


def copy_for(lang):
    """The pieces to insert, out of content/i18n."""
    d = I18N[lang]
    pillar = d["home"]["pillars"]["items"][1]
    section = d["solutions"]["sections"][1]
    bullet = next(p for p in pillar["points"] if p.startswith(("Invobay", "إنفوباي")))
    return {
        "bullet": bullet,
        "link": pillar.get("link"),
        "linkLabel": pillar.get("linkLabel"),
        "summary": pillar["summary"],
        "lede": section["lede"],
        "para": section["body"][2],
        "groups": section["groups"][1:3],
        "delivery": section["groups"][-1]["title"],
        "footnote": section["note"],
    }


def js_string(text):
    """How the DICT writes a string. Refuses anything needing an escape."""
    if any(c in text for c in '"\\\n'):
        sys.exit(f"copy needs escaping, which this tool does not do: {text[:48]!r}")
    return f'"{text}"'


def render_group(group):
    items = ",\n".join(f"            {js_string(i)}" for i in group["items"])
    tail = ""
    if group.get("link"):
        tail = (f', link: {js_string(group["link"])}'
                f', linkLabel: {js_string(group["linkLabel"])}')
    return (f'          {{ title: {js_string(group["title"])}, items: [\n{items}\n'
            f'          ]{tail} }},')


# The solutions groups render their items and nothing else, so a bare
# "invobay.com" in an item was only ever text — the runtime escapes everything
# it interpolates, as a page built with an <a> inside a string shows. A link
# has to be markup, which is why this is injected rather than written in the
# copy. Only a group carrying a link renders one, so the three that do not are
# untouched. The styling is the one the contact page's map link already uses.
GROUP_CLOSE = ('                </sc-for>\n'
               '              </div>\n'
               '            </div>\n'
               '          </sc-for>\n')

# The home page's cards are the same story: the points loop renders text, so
# the link is markup here too. It hangs off the line rather than off one
# bullet, which is why the label names the destination outright instead of
# saying "read more" — CarSaas's bullet sits in the same card.
LINE_CLOSE = ('                </sc-for>\n'
              '              </div>\n'
              '            </div>\n'
              '          </div>\n'
              '        </sc-for>\n')

LINE_LINK = ('                </sc-for>\n'
             '              </div>\n'
             '              <sc-if value="{{ ln.link }}">\n'
             '                <a href="{{ ln.link }}" target="_blank" rel="noopener" '
             'style="align-self:flex-start; font-size:14px; color:#5B6CFF;" '
             'style-hover="color:#8B98FF;">{{ ln.linkLabel }}</a>\n'
             '              </sc-if>\n'
             '            </div>\n'
             '          </div>\n'
             '        </sc-for>\n')

# The card's display objects are built by a .map() that names every field it
# keeps, so a link left in the DICT would never reach the markup.
LINE_MAP = ('        summary: l.summary,\n'
            '        points: l.points\n'
            '      })),')
LINE_MAP_NEW = ('        summary: l.summary,\n'
                '        points: l.points,\n'
                '        link: l.link,\n'
                '        linkLabel: l.linkLabel\n'
                '      })),')

GROUP_LINK = ('                </sc-for>\n'
              '              </div>\n'
              '              <sc-if value="{{ g.link }}">\n'
              '                <a href="{{ g.link }}" target="_blank" rel="noopener" '
              'style="align-self:flex-start; font-size:14px; color:#5B6CFF;" '
              'style-hover="color:#8B98FF;">{{ g.linkLabel }}</a>\n'
              '              </sc-if>\n'
              '            </div>\n'
              '          </sc-for>\n')


def edit_template(html):
    """Insert the bullet, the paragraph and the two groups into the DICT."""
    match = TEMPLATE.search(html)
    if not match:
        return html, 0
    template = json.loads(match.group(2))
    inserts = 0

    # The markup that turns a group's link into an anchor, on the one page
    # whose sections have groups at all.
    if "{{ g.link }}" not in template and GROUP_CLOSE in template:
        template = template.replace(GROUP_CLOSE, GROUP_LINK, 1)
        inserts += 1
    if "{{ ln.link }}" not in template and LINE_CLOSE in template:
        template = template.replace(LINE_CLOSE, LINE_LINK, 1)
        inserts += 1
    if LINE_MAP in template:
        template = template.replace(LINE_MAP, LINE_MAP_NEW, 1)
        inserts += 1

    for lang in LANGS:
        c = copy_for(lang)

        # The bullet goes under CarSaas, in the home page's second pillar.
        # Anchored on this language's own summary, which sits immediately above
        # its points: the DICT holds all three languages, and a pattern that
        # only matched "the first CarSaas bullet" put every language's bullet
        # into whichever block comes first.
        if c["bullet"] not in template:
            template, n = re.subn(
                r'(summary: ' + re.escape(js_string(c["summary"]))
                + r',\n          points: \[\n            "[^"]*",\n)',
                lambda m: m.group(1) + f'            {js_string(c["bullet"])},\n',
                template, count=1)
            inserts += n

        # The line's link, appended to its points array in the DICT.
        if c["link"] and f'link: {js_string(c["link"])}' not in template.split(
                js_string(c["summary"]))[-1][:600]:
            template, n = re.subn(
                r'(summary: ' + re.escape(js_string(c["summary"]))
                + r',\n          points: \[\n(?:[^\n]*\n)*?          \])(\n        \})',
                lambda m: (m.group(1) + f',\n          link: {js_string(c["link"])}'
                           f',\n          linkLabel: {js_string(c["linkLabel"])}'
                           + m.group(2)),
                template, count=1)
            inserts += n

        # The extra paragraph closes the section's own prose.
        if c["para"] not in template:
            # Anchored on this language's own lede, for the same reason.
            rx = re.compile(
                r'(lede: ' + re.escape(js_string(c["lede"])) + r',\n        paras: \[\n)'
                r'((?:[^\n]*\n)*?)(        \],)')

            def add_para(m):
                body = m.group(2).rstrip("\n")
                return m.group(1) + body + f',\n          {js_string(c["para"])}\n' + m.group(3)

            template, n = rx.subn(add_para, template, count=1)
            inserts += n

        # Invobay's group and the role boundary go above the delivery group.
        blocks = "\n".join(render_group(g) for g in c["groups"])
        if blocks not in template:
            existing = re.compile(
                r'\n          \{ title: ' + re.escape(js_string(c["groups"][0]["title"]))
                + r', items: \[\n.*?\n          \][^\n]*\},'
                r'\n          \{ title: ' + re.escape(js_string(c["groups"][1]["title"]))
                + r', items: \[\n.*?\n          \][^\n]*\},', re.S)
            if existing.search(template):
                template, n = existing.subn("\n" + blocks, template, count=1)
            else:
                template, n = re.subn(
                    r'(?=\n          \{ title: "' + re.escape(ANCHORS[lang]["delivery"]) + r'",)',
                    "\n" + blocks, template, count=1)
            inserts += n

    if not inserts:
        return html, 0
    encoded = json.dumps(template, ensure_ascii=False).replace("</", "<\\/")
    return html[:match.start(2)] + encoded + html[match.end(2):], inserts


def main():
    checking = "--check" in sys.argv
    print(f"\n  {'page':<22} {'insert':>6} {'text':>6}")
    print("  " + "-" * 38)

    touched, stale = 0, []
    for locale in LOCALES:
        for page in PAGES:
            path = ROOT / locale / page / "index.html"
            if not path.exists():
                continue
            label = "/" + "/".join(p for p in (locale, page) if p)
            html = original = path.read_text(encoding="utf-8")

            html, inserts = edit_template(html)

            text = 0
            for lang in LANGS:
                c, a = copy_for(lang), ANCHORS[lang]
                for key in ("summary", "lede", "footnote", "delivery"):
                    text += html.count(a[key])
                    html = html.replace(a[key], c[key])
                text += html.count(a["about"][0])
                html = html.replace(*a["about"])

            if html == original:
                print(f"  {label:<22} {'—':>6} {'—':>6}   already done")
                continue
            if checking:
                stale.append(label)
            else:
                path.write_text(html, encoding="utf-8")
            print(f"  {label:<22} {inserts:>6} {text:>6}"
                  + ("   would change" if checking else "   rewritten"))
            touched += 1

    if checking and stale:
        sys.exit(f"\n  Out of date: {', '.join(stale)}\n")
    print(f"\n  {touched} page(s) {'would be ' if checking else ''}rewritten."
          f" Run prerender.py next.\n")


if __name__ == "__main__":
    main()
