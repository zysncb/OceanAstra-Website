#!/usr/bin/env python3
"""
Build the /lark/ sub-site as plain static pages, in all three languages.

    python3 tools/build-lark.py

Run AFTER prerender.py, which is where the header and footer markup comes from,
and in the same slot as build-faq.py — before seo-inject.py, which lists these
pages in sitemap.xml and llms.txt, and before analytics.py, because nothing
here carries the beacon.

Why a sub-site rather than more of the main site. The six exported pages are
Design Canvas bundles: adding a page means a re-export, and the bundle renders
one URL in whichever language the visitor picked, so Chinese and Arabic copy on
those pages is invisible to a crawler. The buyers for this line read Chinese and
Arabic. So these pages are generated here instead, the way /faq/ is — one real
URL per language, no JavaScript, every word in the response — and /zh/lark/ is a
page a search engine can actually index, which /zh/ is not.

Three pages per language, because they answer three different questions that
people type separately:

    /lark/             what it is, why buy through a reseller, what we do
    /lark/pricing/     how it is quoted and how it is actually purchased
    /lark/migration/   what carries across from Microsoft 365 or Google Workspace

The copy is read at run time from content/lark.json, which is the source of
truth for it. This file decides layout and nothing else.

How the chrome is borrowed. Like build-faq.py, the header and footer are lifted
out of the already-rendered privacy page for the same locale — the same markup
and the same computed styles, rather than a lookalike. Two things then have to
be fixed up:

  * the lifted header's links are relative and written for a page one level
    down ("../solutions/"), which breaks on /lark/pricing/ two levels down.
    Every relative href is therefore rewritten to an absolute path inside the
    locale, which is correct at any depth.
  * the language switcher is buttons that only set client-side state. They
    become real links to the same sub-site page in the other language, so the
    switch survives a click here as it does everywhere else on the site.

What is deliberately not claimed. The copy promises an invoice in AED against a
purchase order and says nothing about VAT, which waits on registration; it
promises no support in any particular language; it publishes no discount and no
multi-year price; and it names no Lark product that is not in Lark's own
published plan table. See the note at the top of content/lark.json.
"""

import html as H
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CO = json.loads((ROOT / "content/company.json").read_text(encoding="utf-8"))
LARK = json.loads((ROOT / "content/lark.json").read_text(encoding="utf-8"))
SITE = CO["siteUrl"]

LOCALES = ["en", "zh", "ar"]
PAGES = LARK["order"]
HTML_LANG = {"en": "en", "zh": "zh-Hans", "ar": "ar"}
DIRECTION = {"en": "ltr", "zh": "ltr", "ar": "rtl"}
LABEL = {"en": "EN", "zh": "中文", "ar": "عربي"}

I18N = {c: json.loads((ROOT / f"content/i18n/{c}.json").read_text(encoding="utf-8"))
        for c in LOCALES}

# Lifted verbatim from the rendered privacy page, as build-faq.py does, so the
# generated pages and the exported ones agree down to the pixel.
WRAP = ('max-width: 820px; margin: 0px auto; '
        'padding: clamp(126px, 16vh, 168px) clamp(20px, 4vw, 48px) clamp(64px, 8vw, 96px);')
EYEBROW = ('display: block; margin: 0px 0px 14px; font-family: "JetBrains Mono", monospace; '
           'font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase; '
           'color: rgb(91, 108, 255);')
H1 = ('margin: 0px 0px 10px; font-size: clamp(28px, 4vw, 42px); line-height: 1.16; '
      'letter-spacing: -0.03em; font-variation-settings: "wdth" 100, "wght" 700;')
LEDE = ('margin: 18px 0px 0px; font-size: 15px; line-height: 1.8; '
        'color: rgb(154, 163, 184); text-wrap: pretty;')
NAV = ('margin: 30px 0px 0px; display: flex; flex-wrap: wrap; gap: 10px 24px;')
NAV_LINK = ('font-family: "JetBrains Mono", monospace; font-size: 10.5px; '
            'letter-spacing: 0.16em; text-transform: uppercase; color: rgb(154, 163, 184);')
NAV_HERE = ('font-family: "JetBrains Mono", monospace; font-size: 10.5px; '
            'letter-spacing: 0.16em; text-transform: uppercase; color: rgb(91, 108, 255);')
GROUP = ('margin-top: clamp(40px, 5vw, 56px); padding-top: clamp(28px, 3.4vw, 36px); '
         'border-top: 1px solid rgb(26, 31, 46);')
GROUP_LABEL = ('display: block; margin: 0px 0px 26px; font-family: "JetBrains Mono", monospace; '
               'font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase; '
               'color: rgb(91, 108, 255);')
H2 = ('margin: 0px 0px 12px; font-size: 19px; line-height: 1.3; letter-spacing: -0.016em; '
      'font-variation-settings: "wdth" 100, "wght" 600;')
P = ('margin: 0px 0px 22px; font-size: 15px; line-height: 1.8; '
     'color: rgb(195, 201, 214); text-wrap: pretty;')
UL = 'margin: 0px 0px 10px; padding-inline-start: 20px;'
LI = ('margin: 0px 0px 10px; font-size: 15px; line-height: 1.8; '
      'color: rgb(195, 201, 214); text-wrap: pretty;')
MAIL = 'display: inline-block; margin-top: 4px; font-size: 15px; color: rgb(91, 108, 255);'

esc = lambda s: H.escape(s, quote=True)


def url(locale, page):
    root = "/" if locale == "en" else f"/{locale}/"
    return f"{root}lark/" if page == "index" else f"{root}lark/{page}/"


def out_path(locale, page):
    parts = ["lark"] if locale == "en" else [locale, "lark"]
    if page != "index":
        parts.append(page)
    return ROOT.joinpath(*parts, "index.html")


def source_page(locale):
    rel = "privacy/index.html" if locale == "en" else f"{locale}/privacy/index.html"
    html = (ROOT / rel).read_text(encoding="utf-8")
    block = re.search(r"<!-- prerendered[^>]*-->(.*?)<!-- /prerendered -->", html, re.S)
    if not block:
        raise SystemExit(f"{rel} has no prerendered block — run tools/prerender.py first")
    return block.group(1)


def split(block):
    """Header / footer, cut either side of the privacy page's content wrapper."""
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


def absolutise(block, locale):
    """Relative hrefs are written for a page one level down. These pages sit one
    OR two levels down, so depth-independent absolute paths are the only form
    that is right on both."""
    base = "/" if locale == "en" else f"/{locale}/"

    def fix(m):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "/")):
            return m.group(0)
        return f'href="{base}{re.sub(r"^(\\.\\./)+", "", href)}"'

    return re.sub(r'href="([^"]*)"', fix, block)


def switcher_links(header, locale, page):
    """The bundle's buttons only set state; static pages need real links, and
    they point at the same sub-site page in the other language."""
    def convert(m):
        label = re.sub(r"<[^>]+>", "", m.group("inner")).strip()
        if label not in LABEL.values():
            return m.group(0)
        target = next(k for k, v in LABEL.items() if v == label)
        style = (re.search(r'style="([^"]*)"', m.group("attrs")) or [None, ""])[1]
        style += "; text-decoration: none; display: inline-block;"
        current = ' aria-current="true"' if target == locale else ""
        return (f'<a href="{url(target, page)}" hreflang="{target}" data-lang="{target}"'
                f'{current} style="{style}">{m.group("inner")}</a>')

    return re.sub(r'<(?P<tag>button|a)\b(?P<attrs>[^>]*)>(?P<inner>(?:(?!</?(?:button|a)\b).)*?)</(?P=tag)>',
                  convert, header, flags=re.S)


def body(locale, page):
    t = LARK[locale]
    d = t["pages"][page]
    parts = [f'<div data-dc-tpl="33" style="{esc(WRAP)}">',
             f'<span style="{esc(EYEBROW)}">{H.escape(t["eyebrow"])}</span>',
             f'<h1 style="{esc(H1)}">{H.escape(d["heading"])}</h1>',
             f'<p style="{esc(LEDE)}">{H.escape(d["lede"])}</p>',
             f'<nav style="{esc(NAV)}">']
    for other in PAGES:
        label = H.escape(t["nav"][other])
        if other == page:
            parts.append(f'<span style="{esc(NAV_HERE)}" aria-current="page">{label}</span>')
        else:
            parts.append(f'<a href="{url(locale, other)}" style="{esc(NAV_LINK)}">{label}</a>')
    parts.append("</nav>")

    for section in d["sections"]:
        parts.append(f'<section style="{esc(GROUP)}">')
        parts.append(f'<span style="{esc(GROUP_LABEL)}">{H.escape(section["label"])}</span>')
        parts.append(f'<h2 style="{esc(H2)}">{H.escape(section["heading"])}</h2>')
        for para in section.get("paras", []):
            parts.append(f'<p style="{esc(P)}">{H.escape(para)}</p>')
        if section.get("items"):
            parts.append(f'<ul style="{esc(UL)}">')
            for item in section["items"]:
                parts.append(f'<li style="{esc(LI)}">{H.escape(item)}</li>')
            parts.append("</ul>")
        parts.append("</section>")

    mail = LARK["email"]
    parts += [f'<section style="{esc(GROUP)}">',
              f'<h2 style="{esc(H2)}">{H.escape(d["cta"]["heading"])}</h2>',
              f'<p style="{esc(P)}">{H.escape(d["cta"]["body"])}</p>',
              f'<a href="mailto:{mail}" style="{esc(MAIL)}">{mail}</a>',
              "</section>", "</div>"]
    return "\n".join(parts)


def head(locale, page):
    t = LARK[locale]
    d = t["pages"][page]
    page_url = SITE + url(locale, page)
    nav = I18N[locale]["nav"]

    crumbs = [(nav["home"], SITE + ("/" if locale == "en" else f"/{locale}/")),
              (t["nav"]["index"], SITE + url(locale, "index"))]
    if page != "index":
        crumbs.append((t["nav"][page], page_url))

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "@id": f"{page_url}#webpage", "url": page_url,
             "name": d["title"], "description": d["description"],
             "inLanguage": HTML_LANG[locale],
             "isPartOf": {"@id": f"{SITE}/#website"},
             "about": {"@id": f"{SITE}/#organization"},
             "breadcrumb": {"@id": f"{page_url}#breadcrumb"}},
            {"@type": "BreadcrumbList", "@id": f"{page_url}#breadcrumb",
             "itemListElement": [
                 {"@type": "ListItem", "position": i, "name": name, "item": href}
                 for i, (name, href) in enumerate(crumbs, 1)]},
        ],
    }
    ld = json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    alts = "\n".join(
        f'  <link rel="alternate" hreflang="{HTML_LANG[c]}" href="{SITE + url(c, page)}">'
        for c in LOCALES)

    return f"""<!DOCTYPE html>
<html lang="{HTML_LANG[locale]}" dir="{DIRECTION[locale]}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(d["title"])}</title>
  <meta name="description" content="{esc(d["description"])}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
  <link rel="canonical" href="{page_url}">
{alts}
  <link rel="alternate" hreflang="x-default" href="{SITE + url('en', page)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{esc(CO['brand'])}">
  <meta property="og:title" content="{esc(d["title"])}">
  <meta property="og:description" content="{esc(d["description"])}">
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
    print(f"\n  {'locale':<8} {'path':<28} {'sections':>8}")
    print("  " + "-" * 48)
    for locale in LOCALES:
        header, footer = split(source_page(locale))
        header, footer = absolutise(header, locale), absolutise(footer, locale)
        for page in PAGES:
            doc = (head(locale, page)
                   + switcher_links(header, locale, page)
                   + body(locale, page) + footer + "\n</body>\n</html>\n")
            out = out_path(locale, page)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(doc, encoding="utf-8")
            count = len(LARK[locale]["pages"][page]["sections"])
            print(f"  {locale:<8} {str(out.relative_to(ROOT)):<28} {count:>8}")
    print()


if __name__ == "__main__":
    main()
