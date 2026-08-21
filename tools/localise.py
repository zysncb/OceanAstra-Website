#!/usr/bin/env python3
"""
Derive the Chinese and Arabic sites from the rendered English pages.

    python3 tools/localise.py

NOT CURRENTLY IN THE PIPELINE, and it will not work as written.

It was built against a prerender step that replaced the bundle, so rewriting
the served HTML was enough. The bundle now stays — it parses its template and
swaps the root element on load — which means every substitution here is
discarded the instant JavaScript runs. Crawlers would see Chinese; visitors
would see English.

Making the switcher work for real visitors means translating the template JSON
in <script type="__bundler/template">, which is what the bundle actually
renders from. The translations in content/i18n/zh.json and ar.json are complete
and keyed identically to en.json, so the copy is ready; it is the injection
point that has to change.

Design Canvas exports one language. Rather than maintain three exports that
drift apart, this takes the rendered English DOM and substitutes strings using
content/i18n/*.json, which already hold complete Chinese and Arabic copy under
identical keys.

Arabic gets a real right-to-left layout. That works because the export lays out
with flex and logical `text-align: start`, both of which mirror on their own —
the only thing pinning the page was a hardcoded dir="ltr" on the content
wrapper. Flipping it mirrors the whole page: logo to the right, nav to the
left, buttons reversed. There are 41 absolute `left:` offsets that do not
mirror, but they position decorative starfield elements, not content.

The language switcher is also rebuilt here. The export ships three <button>
elements that only rewrote <html lang>; they become real <a href> links, so
crawlers can follow them and the three language versions can reference each
other with hreflang.
"""

import html as H
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["", "solutions", "about", "contact", "privacy", "terms"]
LOCALES = ["en", "zh", "ar"]

# Label -> locale, as the switcher renders them.
LABELS = {"EN": "en", "中文": "zh", "عربي": "ar"}

ACTIVE = "background: rgb(242, 242, 240); color: rgb(7, 9, 15);"
IDLE = "background: transparent; color: rgb(138, 147, 168);"


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


I18N = {c: flatten(json.loads((ROOT / f"content/i18n/{c}.json").read_text(encoding="utf-8")))
        for c in LOCALES}


def url(locale, page):
    root = "/" if locale == "en" else f"/{locale}/"
    return root if not page else f"{root}{page}/"


def translate(html, locale):
    """Substitute English strings for their counterparts in `locale`.

    Longest first, and that ordering is load-bearing: "Support" is a substring
    of several longer strings, so replacing it early would corrupt them. By the
    time the short labels run, every longer string containing them has already
    become Chinese or Arabic, leaving only standalone occurrences to match.

    Three characters is the floor. Below that a string is as likely to collide
    with markup as to be real copy.
    """
    en, target = I18N["en"], I18N[locale]
    pairs = sorted(
        ((e, target[k]) for k, e in en.items() if k in target and len(e) >= 3),
        key=lambda p: -len(p[0]),
    )
    done = 0
    for source, dest in pairs:
        if source == dest:
            continue
        for a, b in ((H.escape(source, quote=False), H.escape(dest, quote=False)),
                     (source, dest)):
            if a in html:
                html = html.replace(a, b)
                done += 1
                break
    return html, done


def relink(html, locale):
    """Point internal page links at the same page in this locale.

    The language switcher is left alone — it deliberately points across
    locales, which is the one case this must not rewrite.
    """
    if locale == "en":
        return html

    switcher_hrefs = {f'href="{url(c, p)}"' for c in LOCALES for p in PAGES}
    switcher_hrefs = {m.group(0) for m in re.finditer(r'href="[^"]*"', html)
                      if re.search(re.escape(m.group(0)) + r'[^>]*data-lang=', html)}

    def swap(m):
        href = m.group(1)
        if href.startswith(("/assets/", "/llms", "/robots", "/sitemap")):
            return m.group(0)
        if m.group(0) in switcher_hrefs:
            return m.group(0)
        page = href.strip("/")
        if page in PAGES or href == "/":
            return f'href="{url(locale, page)}"'
        return m.group(0)

    return re.sub(r'href="(/[^"]*)"', swap, html)


def switcher(html, locale, page):
    """Rewrite the three switcher controls as links, active state on `locale`.

    Matched by their label text, not by class or template id: the export gives
    the home page `data-dc-tpl="25" class="scp1"` and the inner pages
    `data-dc-tpl="24"` with no class at all, and a selector keyed to either one
    silently skips the other half of the site.

    Handles both <button> (as exported) and <a> (as produced here), so running
    the step twice is the same as running it once.
    """
    control = re.compile(
        r'<(?P<tag>button|a)\b(?P<attrs>[^>]*)>(?P<inner>(?:(?!</?(?:button|a)\b).)*?)</(?P=tag)>',
        re.S)

    def convert(m):
        label = re.sub(r"<[^>]+>", "", m.group("inner")).strip()
        if label not in LABELS:
            return m.group(0)

        target = LABELS[label]
        attrs = m.group("attrs")
        style = (re.search(r'style="([^"]*)"', attrs) or [None, ""])[1]

        # Normalise first — the control may already be active from a previous
        # run, so toggling relative to its current state is unreliable.
        style = style.replace(ACTIVE, IDLE)
        if target == locale:
            style = style.replace(IDLE, ACTIVE)
        if "text-decoration" not in style:
            style = style.replace("cursor: pointer;",
                                  "cursor: pointer; text-decoration: none; display: inline-block;")

        keep = " ".join(a for a in (
            (re.search(r'(data-dc-tpl="[^"]*")', attrs) or [None, ""])[1],
            (re.search(r'(class="[^"]*")', attrs) or [None, ""])[1],
        ) if a)
        aria = ' aria-current="true"' if target == locale else ""
        return (f'<a href="{url(target, page)}" hreflang="{target}" data-lang="{target}"'
                f'{aria} {keep} style="{style}">{m.group("inner")}</a>')

    return control.sub(convert, html)


def rtl(html):
    """Mirror the layout. The export pins its content wrapper to dir="ltr"."""
    html = html.replace('dir="ltr"', 'dir="rtl"')
    return html.replace('<html lang="en" dir="rtl">', '<html lang="ar" dir="rtl">', 1)


def build(locale):
    made = []
    for page in PAGES:
        src = ROOT / (f"{page}/index.html" if page else "index.html")
        html = src.read_text(encoding="utf-8")

        html, count = translate(html, locale)
        html = switcher(html, locale, page)   # sets its own hrefs …
        html = relink(html, locale)           # … which relink must not touch

        if locale == "ar":
            html = rtl(html)
        else:
            meta = json.loads((ROOT / f"content/i18n/{locale}.json").read_text(encoding="utf-8"))["meta"]
            html = html.replace('<html lang="en" dir="ltr">',
                                f'<html lang="{meta["htmlLang"]}" dir="{meta["dir"]}">', 1)

        out = ROOT / locale / (f"{page}/index.html" if page else "index.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        made.append((page or "/", count))
    return made


def main():
    for locale in ("zh", "ar"):
        shutil.rmtree(ROOT / locale, ignore_errors=True)

    print(f"\n  {'locale':<8} {'page':<12} {'strings replaced':>18}")
    print("  " + "-" * 42)
    for locale in ("zh", "ar"):
        for page, count in build(locale):
            print(f"  {locale:<8} {page:<12} {count:>18}")

    # English pages keep their own switcher, now as links rather than buttons.
    for page in PAGES:
        path = ROOT / (f"{page}/index.html" if page else "index.html")
        path.write_text(switcher(path.read_text(encoding="utf-8"), "en", page), encoding="utf-8")
    print(f"\n  English switcher rewritten as links on {len(PAGES)} pages\n")


if __name__ == "__main__":
    main()
