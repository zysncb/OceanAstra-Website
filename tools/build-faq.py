#!/usr/bin/env python3
"""
Build /faq/ (and its zh and ar counterparts) as plain static pages.

    python3 tools/build-faq.py

Run AFTER prerender.py, which is where the header and footer markup comes from.

The FAQ is not part of the Design Canvas export and cannot be added to it
without a re-export. Rather than approximate the design by hand, this lifts the
already-rendered header and footer out of the privacy page — the closest
structural sibling, being long-form prose — and replaces the body between them.
The result is the same markup and the same computed styles, not a lookalike.

There is no bundle on these pages, which makes them the cheapest pages on the
site for a crawler to read: no JavaScript to execute, all text in the response.
The language switcher becomes real links across locales, which the bundle's
version cannot be.

FAQPage structured data is emitted from the same JSON that renders the visible
answers, so the two cannot drift apart. Google requires the markup to match what
a visitor sees; generating both from one source is how that stays true.
"""

import html as H
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CO = json.loads((ROOT / "content/company.json").read_text(encoding="utf-8"))
FAQ = json.loads((ROOT / "content/faq.json").read_text(encoding="utf-8"))
SITE = CO["siteUrl"]

LOCALES = ["en", "zh", "ar"]
HTML_LANG = {"en": "en", "zh": "zh-Hans", "ar": "ar"}
DIRECTION = {"en": "ltr", "zh": "ltr", "ar": "rtl"}
LABEL = {"en": "EN", "zh": "中文", "ar": "عربي"}

# Lifted verbatim from the rendered privacy page so the two pages agree.
WRAP = ('max-width: 820px; margin: 0px auto; '
        'padding: clamp(126px, 16vh, 168px) clamp(20px, 4vw, 48px) clamp(64px, 8vw, 96px);')
H1 = ('margin: 0px 0px 10px; font-size: clamp(28px, 4vw, 42px); line-height: 1.16; '
      'letter-spacing: -0.03em; font-variation-settings: "wdth" 100, "wght" 700;')
LEDE = ('margin: 18px 0px 0px; font-size: 15px; line-height: 1.8; '
        'color: rgb(154, 163, 184); text-wrap: pretty;')
GROUP = ('margin-top: clamp(40px, 5vw, 56px); padding-top: clamp(28px, 3.4vw, 36px); '
         'border-top: 1px solid rgb(26, 31, 46);')
GROUP_LABEL = ('display: block; margin: 0px 0px 26px; font-family: "JetBrains Mono", monospace; '
               'font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase; '
               'color: rgb(91, 108, 255);')
Q = ('margin: 0px 0px 12px; font-size: 19px; line-height: 1.3; letter-spacing: -0.016em; '
     'font-variation-settings: "wdth" 100, "wght" 600;')
A = ('margin: 0px 0px 34px; font-size: 15px; line-height: 1.8; '
     'color: rgb(195, 201, 214); text-wrap: pretty;')


def url(locale, page="faq"):
    root = "/" if locale == "en" else f"/{locale}/"
    return f"{root}{page}/" if page else root


def source_page(locale):
    rel = "privacy/index.html" if locale == "en" else f"{locale}/privacy/index.html"
    html = (ROOT / rel).read_text(encoding="utf-8")
    block = re.search(r"<!-- prerendered[^>]*-->(.*?)<!-- /prerendered -->", html, re.S)
    if not block:
        raise SystemExit(f"{rel} has no prerendered block — run tools/prerender.py first")
    return block.group(1)


def split(block):
    """Header / content / footer, cut at the privacy page's content wrapper."""
    start = block.find('<div data-dc-tpl="33"')
    if start < 0:
        raise SystemExit("content wrapper not found; the export's template ids changed")
    depth, i = 0, start
    while i < len(block):
        if block.startswith("<div", i):
            depth += 1
        elif block.startswith("</div>", i):
            depth -= 1
            if depth == 0:
                return block[:start], block[i + 6:]
        i += 1
    raise SystemExit("content wrapper is unbalanced")


def switcher_links(header, locale):
    """The bundle's buttons only set state; static pages need real links."""
    def convert(m):
        label = re.sub(r"<[^>]+>", "", m.group("inner")).strip()
        if label not in LABEL.values():
            return m.group(0)
        target = next(k for k, v in LABEL.items() if v == label)
        style = (re.search(r'style="([^"]*)"', m.group("attrs")) or [None, ""])[1]
        style += "; text-decoration: none; display: inline-block;"
        current = ' aria-current="true"' if target == locale else ""
        return (f'<a href="{url(target)}" hreflang="{target}" data-lang="{target}"'
                f'{current} style="{style}">{m.group("inner")}</a>')

    return re.sub(r'<(?P<tag>button|a)\b(?P<attrs>[^>]*)>(?P<inner>(?:(?!</?(?:button|a)\b).)*?)</(?P=tag)>',
                  convert, header, flags=re.S)


def body(locale):
    t = FAQ[locale]
    parts = [f'<div data-dc-tpl="33" style="{H.escape(WRAP, quote=True)}">',
             f'<h1 style="{H.escape(H1, quote=True)}">{H.escape(t["heading"])}</h1>',
             f'<p style="{H.escape(LEDE, quote=True)}">{H.escape(t["lede"])}</p>']
    for group in t["groups"]:
        parts.append(f'<section style="{H.escape(GROUP, quote=True)}">')
        parts.append(f'<span style="{H.escape(GROUP_LABEL, quote=True)}">{H.escape(group["title"])}</span>')
        for question, answer in group["items"]:
            parts.append(f'<h2 style="{H.escape(Q, quote=True)}">{H.escape(question)}</h2>')
            parts.append(f'<p style="{H.escape(A, quote=True)}">{H.escape(answer)}</p>')
        parts.append("</section>")
    parts.append("</div>")
    return "\n".join(parts)


def head(locale):
    t = FAQ[locale]
    page_url = SITE + url(locale)
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "@id": f"{page_url}#faq", "url": page_url,
             "name": t["title"], "description": t["description"],
             "inLanguage": HTML_LANG[locale],
             "isPartOf": {"@id": f"{SITE}/#website"},
             "about": {"@id": f"{SITE}/#organization"},
             "mainEntity": [
                 {"@type": "Question", "name": q,
                  "acceptedAnswer": {"@type": "Answer", "text": a}}
                 for g in t["groups"] for q, a in g["items"]
             ]}
        ],
    }
    ld = json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    alts = "\n".join(
        f'  <link rel="alternate" hreflang="{HTML_LANG[c]}" href="{SITE + url(c)}">'
        for c in LOCALES)
    esc = lambda s: H.escape(s, quote=True)
    return f"""<!DOCTYPE html>
<html lang="{HTML_LANG[locale]}" dir="{DIRECTION[locale]}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(t["title"])}</title>
  <meta name="description" content="{esc(t["description"])}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
  <link rel="canonical" href="{page_url}">
{alts}
  <link rel="alternate" hreflang="x-default" href="{SITE + url('en')}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{esc(CO['brand'])}">
  <meta property="og:title" content="{esc(t["title"])}">
  <meta property="og:description" content="{esc(t["description"])}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{SITE}/assets/img/og-image.png">
  <meta property="og:locale" content="{HTML_LANG[locale]}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{SITE}/assets/img/og-image.png">
  <meta name="theme-color" content="#07090f">
  <link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/fonts/fonts.css">
  <style>
    html {{ background: #07090F; }}
    body {{ margin: 0; background: #07090F; color: #F2F2F0;
           font-family: Archivo, "Noto Sans SC", "Noto Kufi Arabic", sans-serif;
           font-variation-settings: "wdth" 100, "wght" 400;
           -webkit-font-smoothing: antialiased; }}
    /* The bundle ships its own reset; without it the browser defaults show
       through as underlined nav links and bold headings at the wrong weight. */
    *, *::before, *::after {{ box-sizing: border-box; }}
    a {{ color: inherit; text-decoration: none; }}
    h1, h2 {{ font-weight: inherit; }}
    p {{ margin: 0; }}
    section > h2:first-of-type {{ margin-top: 0; }}
  </style>
  <script type="application/ld+json">{ld}</script>
</head>
<body>"""


def main():
    print(f"\n  {'locale':<8} {'path':<16} {'questions':>10}")
    print("  " + "-" * 38)
    for locale in LOCALES:
        header, footer = split(source_page(locale))
        header = switcher_links(header, locale)
        page = head(locale) + header + body(locale) + footer + "\n</body>\n</html>\n"

        out = ROOT / ("faq/index.html" if locale == "en" else f"{locale}/faq/index.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")

        count = sum(len(g["items"]) for g in FAQ[locale]["groups"])
        print(f"  {locale:<8} {str(out.relative_to(ROOT)):<16} {count:>10}")
    print()


if __name__ == "__main__":
    main()
