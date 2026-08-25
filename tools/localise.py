#!/usr/bin/env python3
"""
Publish the Chinese and Arabic sites at their own URLs.

    python3 tools/localise.py

Run AFTER prepare-export.py and BEFORE prerender.py.

The export is already trilingual. Its runtime carries a complete DICT for zh
and ar, handles right-to-left for Arabic on its own, and the header switcher
works — it sets component state and the page re-renders in the chosen language.
None of that needed building.

What was missing is a URL. Language lived in client state only, so:

  - crawlers never saw anything but English, because they do not click;
  - an AI answer engine had no Arabic text to retrieve for an Arabic question,
    despite the Arabic existing in the bundle it downloaded;
  - a reader could not link anyone to the Chinese page, because there wasn't one.

So this copies the six English pages to /zh/ and /ar/ and changes which language
they boot in. The component resolves it as

    this.state.lang || this.props.defaultLang || "en"

and props come from the schema in data-props on the <x-dc> script. Setting that
schema's default is the whole edit. The home page ships the attribute already;
the inner pages have no props of their own, so it is added.

The head is the other half. A copied page inherits the English <title>,
description and Open Graph pair prepare-export.py wrote, so a Chinese page
announced itself in English to everything that reads metadata rather than
prose — search results, link previews, answer engines. The translations were
always there: content/i18n/{zh,ar}.json carry a title and a description per
page, the same file seo-inject.py reads for English. This writes them in.

Both heads need it. The template carries its own document element and replaces
the served one on load, so the served <head> is what a crawler reads and the
template's is what a browser ends up with; either one left in English is a
locale that lies to half its audience.

Internal links need no rewriting: the export emits them relative ("solutions/",
"../about/"), so they resolve within whichever locale directory they are served
from. The switcher keeps working client-side; it just no longer has to.
"""

import html as H
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["", "solutions", "about", "contact", "privacy", "terms"]
TARGETS = ["zh", "ar"]

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

DIRECTION = {"zh": "ltr", "ar": "rtl"}
HTML_LANG = {"zh": "zh-Hans", "ar": "ar"}

# Per-page title and description, keyed by slug — "" is "home". The same
# translations tools/seo-inject.py reads for the English pages.
I18N = {c: json.loads((ROOT / f"content/i18n/{c}.json").read_text(encoding="utf-8"))
        for c in TARGETS}

# The editor schema the runtime reads its props from.
SCHEMA = {
    "defaultLang": {"editor": "enum", "options": ["en", "zh", "ar"],
                    "default": "en", "tsType": "'en'|'zh'|'ar'", "section": "Site"},
    "showHeroMark": {"editor": "boolean", "default": False,
                     "tsType": "boolean", "section": "Site"},
}

# Non-greedy up to </script> is safe only because the payload escapes its own
# nested </script> as <\/script>; see the note in localise().
TEMPLATE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)
XDC_OPEN = re.compile(r'<script type="text/x-dc"[^>]*>')


def props_attr(locale):
    schema = json.loads(json.dumps(SCHEMA))
    schema["defaultLang"]["default"] = locale
    return 'data-props="' + H.escape(json.dumps(schema, separators=(",", ":")), quote=True) + '"'


def set_default_lang(template, locale):
    """Point the component at `locale`, adding the props schema if absent."""
    match = XDC_OPEN.search(template)
    if not match:
        raise RuntimeError("no <script type=\"text/x-dc\"> in template")

    tag = match.group(0)
    if "data-props=" in tag:
        rebuilt = re.sub(r'data-props="[^"]*"', props_attr(locale), tag)
    else:
        rebuilt = tag[:-1].rstrip() + " " + props_attr(locale) + ">"
    return template[:match.start()] + rebuilt + template[match.end():]


def retitle(doc, locale, page):
    """Replace the inherited English title and description with this locale's.

    prepare-export.py writes one seo_block() into the served <head> and the
    same text into the template's, so the substitutions below serve both.
    Only these four tags are ours: canonical, og:url and hreflang belong to
    seo-inject.py, which runs afterwards and rewrites them per locale.
    """
    meta = I18N[locale][page or "home"]
    title, desc = meta["title"], meta["description"]
    esc = lambda s: H.escape(s, quote=True)

    edits = [
        (r"<title>.*?</title>", f"<title>{H.escape(title)}</title>"),
        (r'<meta name="description" content="[^"]*">',
         f'<meta name="description" content="{esc(desc)}">'),
        (r'<meta property="og:title" content="[^"]*">',
         f'<meta property="og:title" content="{esc(title)}">'),
        (r'<meta property="og:description" content="[^"]*">',
         f'<meta property="og:description" content="{esc(desc)}">'),
    ]
    for pattern, replacement in edits:
        # A function replacement, so a backslash or a \g in the translation is
        # not read as a group reference.
        doc, hits = re.subn(pattern, lambda m: replacement, doc, count=1, flags=re.S)
        if not hits:
            raise RuntimeError(f"/{locale}/{page}: nothing matched {pattern}")
    return doc


OG_LOCALE = re.compile(r'\s*<meta property="og:locale" content="[^"]*">')


def set_og_locale(template, lang):
    """Declare the locale inside the template head.

    The export writes no og:locale anywhere, and seo-inject.py adds one only to
    the served <head> — it never opens the template. But the template replaces
    that head on load, so without this the document a browser actually holds
    declares no locale at all. Idempotent: any existing tag is dropped first.
    """
    template = OG_LOCALE.sub("", template)
    tag = f'\n<meta property="og:locale" content="{lang}">'
    template, hits = re.subn(r'<meta property="og:url" content="[^"]*">',
                             lambda m: m.group(0) + tag, template, count=1)
    if not hits:
        raise RuntimeError("no og:url in template to hang og:locale on")
    return template


def localise(html, locale, page):
    lang, direction = HTML_LANG[locale], DIRECTION[locale]

    def patch(m):
        template = json.loads(m.group(2))
        template = set_default_lang(template, locale)
        template = retitle(template, locale, page)
        template = set_og_locale(template, lang)
        # The template carries its own document element and replaces the served
        # one on load, so the served <html> alone is not enough.
        template = re.sub(r'<html lang="[^"]*" dir="[^"]*">',
                          f'<html lang="{lang}" dir="{direction}">', template, count=1)
        # The template string contains a nested </script>. JSON does not
        # require escaping "/", but leaving it literal ends the enclosing
        # <script> element early and truncates the template — which is why the
        # export writes it as <\/script>. Re-encoding has to do the same.
        encoded = json.dumps(template, ensure_ascii=False).replace("</", "<\\/")
        return m.group(1) + encoded + m.group(3)

    html = TEMPLATE.sub(patch, html, count=1)
    # The served head, whose og:locale seo-inject.py writes for every locale.
    html = retitle(html, locale, page)
    return re.sub(r'<html lang="[^"]*" dir="[^"]*">',
                  f'<html lang="{lang}" dir="{direction}">', html, count=1)


def rendered_heading(url):
    out = subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--window-size=1440,900",
         "--virtual-time-budget=12000", "--dump-dom", url],
        capture_output=True, text=True, timeout=120)
    m = re.search(r"<h1[^>]*>(.*?)</h1>", out.stdout, re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


SCRIPT = {"zh": re.compile(r"[一-鿿]"), "ar": re.compile(r"[؀-ۿ]")}


def main():
    for locale in TARGETS:
        shutil.rmtree(ROOT / locale, ignore_errors=True)

    print(f"\n  {'locale':<8} {'page':<12}   status")
    print("  " + "-" * 34)
    for locale in TARGETS:
        for page in PAGES:
            rel = f"{page}/index.html" if page else "index.html"
            source = (ROOT / rel).read_text(encoding="utf-8")
            out = ROOT / locale / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(localise(source, locale, page), encoding="utf-8")
        print(f"  {locale:<8} {'(' + str(len(PAGES)) + ' pages)':<12}   written")

    print("\n  Verifying each locale actually boots in its own language:")
    failures = []
    for locale in TARGETS:
        heading = rendered_heading(f"http://localhost:4173/{locale}/")
        ok = bool(heading and SCRIPT[locale].search(heading))
        print(f"    /{locale}/  {'ok ' if ok else 'FAILED'}  h1: {heading[:46]}")
        if not ok:
            failures.append(locale)

    if failures:
        print(f"\n  {', '.join(failures)} did not switch — nothing downstream will be right.\n")
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
