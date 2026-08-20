#!/usr/bin/env python3
"""
Turn a Claude Design Canvas export into the files this site actually ships.

    python3 tools/prepare-export.py <export-dir>

<export-dir> is the folder holding the exported docs/ tree — the six pages as
Design Canvas writes them. Everything below is applied on top, because the
export cannot produce any of it on its own:

  1. Numeric claims that conflict with the trade licence are corrected.
  2. SEO metadata (title, description, canonical, Open Graph, favicon) is
     injected, sourced from content/i18n/en.json.
  3. <html lang/dir> is set, and a listener keeps both in step with the
     in-page language switcher.
  4. Fonts and images move out of the inline manifest into content-addressed
     files under assets/, so the six pages share them and woff2 unicode-range
     subsetting starts working again.
  5. The 336 @font-face rules — identical on every page — become one shared
     stylesheet instead of 331 KB repeated six times.
  6. Loops the export left unwired are connected to their copy, and the empty
     partner logo slots are filled.
  7. Sections the company asked to drop are removed, copy included.
  8. sitemap.xml is regenerated.

Two things are deliberately NOT automated: image cropping/compression (a
judgement call about composition — see README) and anything inside content/.

Two traps worth knowing before editing this file:

  * A <script> injected into __bundler/template never runs — the runtime
    rebuilds the DOM via innerHTML — and its closing tag silently truncates
    the template. Scripts belong in the outer <head>.
  * When writing JSON back into a <script> block, escape </ as <\\/ or the
    payload closes its own tag.
"""

import base64
import hashlib
import html as H
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    ("index.html", "home", "/"),
    ("solutions/index.html", "solutions", "/solutions/"),
    ("about/index.html", "about", "/about/"),
    ("contact/index.html", "contact", "/contact/"),
    ("privacy/index.html", "privacy", "/privacy/"),
    ("terms/index.html", "terms", "/terms/"),
]

# The licence was issued in 2026 and the site ships three languages, so the
# export's "10+" claims contradict both the registration and the rest of the
# page. Re-check these after every export — the Canvas source still has them.
CLAIMS = [
    (r'[\"出海中东\", \"10+ 年中东本地经验\"]', r'[\"出海中东\", \"中东本地交付\"]'),
    (r'[\"Delivery languages\", \"10+ languages\"]',
     r'[\"Delivery languages\", \"English · Arabic · Chinese\"]'),
    (r'[\"لغات التنفيذ\", \"أكثر من 10 لغات\"]',
     r'[\"لغات التنفيذ\", \"العربية · الإنجليزية · الصينية\"]'),
]

EXT = {"font/woff2": ".woff2", "font/woff": ".woff", "image/jpeg": ".jpg",
       "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}

FONT_CSS = "assets/fonts/fonts.css"

LANG_SYNC = (
    '<script>(function(){var m={"EN":["en","ltr"],"中文":["zh-Hans","ltr"],'
    '"عربي":["ar","rtl"]};document.addEventListener("click",function(e){'
    'var b=e.target&&e.target.closest?e.target.closest("button"):null;if(!b)return;'
    'var v=m[(b.textContent||"").trim()];if(!v)return;'
    'document.documentElement.lang=v[0];document.documentElement.dir=v[1];},true);})();</script>'
)


def seo_block(title, desc, url):
    e = lambda s: H.escape(s, quote=True)
    return (
        f'<title>{H.escape(title)}</title>\n'
        f'<meta name="description" content="{e(desc)}">\n'
        f'<link rel="canonical" href="{url}">\n'
        f'<meta property="og:type" content="website">\n'
        f'<meta property="og:site_name" content="OceanAstra">\n'
        f'<meta property="og:title" content="{e(title)}">\n'
        f'<meta property="og:description" content="{e(desc)}">\n'
        f'<meta property="og:url" content="{url}">\n'
        f'<meta name="theme-color" content="#07090f">\n'
        f'<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">'
    )



# Loops the export left unwired -----------------------------------------------
#
# Design Canvas ships copy as positional arrays (["title", "body"]) and the page
# builds display objects from them — nav, langs and cards all get a .map(). Some
# sections never got one: their loop binds straight to the raw array while the
# markup reads r.title / r.body, so every row renders blank. The copy is present
# and correct; only the wiring is missing. Seen on About ("我们坚持的") and
# Contact ("How to reach us", "What to expect").
#
# Rather than name the known cases, find any loop that binds to a raw t.X.items
# whose body reads properties off the alias, and give it a mapped list.

FIELDS = ["title", "body"]   # the positional order Design Canvas writes


def wire_up_loops(template, page):
    fixed = []
    for section, alias in re.findall(
            r'<sc-for list="\{\{\s*t\.(\w+)\.items\s*\}\}" as="(\w+)"', template):
        props = set(re.findall(r'\{\{\s*' + alias + r'\.(\w+)', template))
        if not props:
            continue                      # binds to the array and uses it as one
        unknown = props - set(FIELDS)
        if unknown:
            sys.exit(f"{page}: t.{section}.items is read for {sorted(unknown)}, "
                     f"which this mapping does not cover — extend FIELDS deliberately, "
                     f"since the fix depends on positional order.")
        var = section + "Items"
        template = template.replace(f'list="{{{{ t.{section}.items }}}}"',
                                    f'list="{{{{ {var} }}}}"')
        mapping = ", ".join(f"{f}: o[{i}]" for i, f in enumerate(FIELDS))
        template = template.replace(
            "      nav: t.nav.map(",
            f"      {var}: (t.{section} && t.{section}.items || []).map(o => ({{ {mapping} }})),\n"
            f"      nav: t.nav.map(", 1)
        fixed.append(f"t.{section}.items")
    return template, fixed



# Partner logos ----------------------------------------------------------------
#
# The export leaves the partner logo slots empty — <image-slot> with a
# placeholder and no src. Both marks are black wordmarks on transparent or
# white ground, so dropping them straight onto the #0D111C card would make one
# a white block and the other near-invisible; they sit on a light plate
# instead, which also avoids recolouring anyone's trademark.
#
# The page already derives a logoId per partner (lowercased, non-alphanumerics
# stripped), and that lands on the same value in all three languages —
# "لارك (Lark)" reduces to "lark" — so it is a safe lookup key.

# Pre-composed at the slot's own 3:1 by tools/make-partner-logo.sh — the source
# files carry heavy canvas padding (Lark's artwork fills only 643x184 of a
# 766x400 canvas), so scaling them by canvas height rendered the artwork at
# less than half the intended size.
PARTNER_LOGOS = {
    "oa-logo-lark": "/assets/img/partners/lark.png",
    "oa-logo-amap": "/assets/img/partners/amap.png",
}

OLD_PARTNER_MAP = ('partnerItems: t.partners.items.map(i => ({ title: i[0], body: i[1], '
                   'logoId: "oa-logo-" + i[0].toLowerCase().replace(/[^a-z0-9]/g, "") })),')
NEW_PARTNER_MAP = ('partnerItems: t.partners.items.map(i => { '
                   'var logoId = "oa-logo-" + i[0].toLowerCase().replace(/[^a-z0-9]/g, ""); '
                   'return { title: i[0], body: i[1], logoId: logoId, '
                   'logo: PARTNER_LOGOS[logoId] || "" }; }),')

LOGO_MARKUP = ('<div style="height:40px; display:flex; align-items:center;">'
               '<sc-if value="{{ p.logo }}">'
               '<img src="{{ p.logo }}" alt="{{ p.title }}" loading="lazy" '
               'width="120" height="40" '
               'style="height:40px; width:auto; border-radius:5px; display:block;">'
               '</sc-if></div>')


def fill_partner_logos(template):
    if OLD_PARTNER_MAP not in template:
        return template, False
    decl = "const PARTNER_LOGOS = " + json.dumps(PARTNER_LOGOS) + ";\n"
    at = template.find("class ")
    if at < 0:
        at = template.find("function ")
    template = template[:at] + decl + template[at:]
    template = template.replace(OLD_PARTNER_MAP, NEW_PARTNER_MAP, 1)
    slot = re.search(r'<div style="width:120px; height:40px;">\s*<image-slot[^>]*>\s*</image-slot>\s*</div>',
                     template)
    if not slot:
        sys.exit("partner logo slot markup changed — re-check the export before shipping")
    return template[:slot.start()] + LOGO_MARKUP + template[slot.end():], True



# Sections the company does not want shipped ----------------------------------
#
# Contact's "How to reach us" duplicated the three contact cards above it and
# offered a telephone support line, which OceanAstra does not run. Dropped at
# the company's instruction, along with its copy, so the claim is not sitting
# in the page source either. The office note lost its "or call ahead" for the
# same reason.

DROP_SECTIONS = {
    "contact/index.html": ["reach"],
}

PHONE_WORDING = [
    ('note: "到访请提前预约。烦请先来信或来电，以便我们安排相关同事在场。"',
     'note: "到访请提前预约。烦请先来信，以便我们安排相关同事在场。"'),
    ('note: "Visits are by appointment. Please write or call ahead so we can make sure the right people are available."',
     'note: "Visits are by appointment. Please email ahead so we can make sure the right people are available."'),
    ('note: "الزيارات بموعد مسبق. يُرجى المراسلة أو الاتصال قبل الحضور حتى نضمن وجود الأشخاص المعنيين."',
     'note: "الزيارات بموعد مسبق. يُرجى المراسلة قبل الحضور حتى نضمن وجود الأشخاص المعنيين."'),
]


def _cut_data_block(text, key):
    """Delete `key: { ... },` by matching braces so nested objects survive."""
    out, cut = text, 0
    while True:
        i = out.find(key + ": {")
        if i < 0:
            return out, cut
        depth, j = 0, out.find("{", i)
        for k in range(j, len(out)):
            if out[k] == "{":
                depth += 1
            elif out[k] == "}":
                depth -= 1
                if depth == 0:
                    end = k + 1
                    if out[end:end + 1] == ",":
                        end += 1
                    while out[end:end + 1] in (" ", "\n"):
                        end += 1
                    out, cut = out[:i] + out[end:], cut + 1
                    break
        else:
            return out, cut


def drop_sections(template, page):
    """Remove unwanted sections: the markup, then the copy behind it."""
    dropped = []
    for key in DROP_SECTIONS.get(page, []):
        anchor = template.find("{{ t.%s.heading }}" % key)
        if anchor < 0:
            continue
        start = template.rfind('<div style="border-top:1px solid #1A1F2E;', 0, anchor)
        nxt = template.find('<div style="border-top:1px solid #1A1F2E;', anchor)
        if start < 0 or nxt < 0:
            sys.exit(f"{page}: could not bound the '{key}' section — check the export markup")
        template = template[:start] + template[nxt:]
        template, _ = _cut_data_block(template, key)
        dropped.append(key)

    for old, new in PHONE_WORDING:
        template = template.replace(old, new)
    return template, dropped


def block(doc, kind):
    """Locate a <script type="__bundler/KIND"> payload."""
    return re.search(rf'(<script type="__bundler/{kind}">)(.*?)(</script>)', doc, re.S)


def put(doc, match, value):
    """Replace a payload, escaping </ so it cannot close its own script tag."""
    return doc[:match.start(2)] + json.dumps(value).replace("</", r"<\/") + doc[match.end(2):]


def main(export_dir):
    en = json.load(open(os.path.join(ROOT, "content/i18n/en.json"), encoding="utf8"))
    company = json.load(open(os.path.join(ROOT, "content/company.json"), encoding="utf8"))
    site = company["siteUrl"]

    os.chdir(ROOT)
    global OVERRIDES, overridden
    ov_path = "tools/image-overrides.json"
    OVERRIDES = {k: v for k, v in json.load(open(ov_path, encoding="utf8")).items()
                 if not k.startswith("_")} if os.path.exists(ov_path) else {}
    overridden = set()

    store, faces_written, total = {}, False, 0

    for page, key, route in PAGES:
        src = os.path.join(export_dir, "index.html" if page == "index.html" else page)
        if not os.path.exists(src):
            sys.exit(f"missing page in export: {src}")
        doc = open(src, encoding="utf8").read()

        for old, new in CLAIMS:
            doc = doc.replace(old, new)

        meta = seo_block(en[key]["title"], en[key]["description"], site + route)
        doc = doc.replace("<title>Bundled Page</title>", meta, 1)
        doc = doc.replace("<html>", '<html lang="en" dir="ltr">', 1)
        doc = doc.replace("</head>", LANG_SYNC + "\n</head>", 1)
        doc = doc.replace(
            '<meta name="theme-color"',
            f'<link rel="preload" as="style" href="/{FONT_CSS}">\n'
            f'<link rel="stylesheet" href="/{FONT_CSS}">\n<meta name="theme-color"', 1)

        man_m, tpl_m = block(doc, "manifest"), block(doc, "template")
        manifest = json.loads(man_m.group(2))
        template = json.loads(tpl_m.group(2))
        template = template.replace("<html><head>", '<html lang="en" dir="ltr"><head>\n' + meta, 1)
        template, dropped = drop_sections(template, page)
        template, wired = wire_up_loops(template, page)
        template, logos_in = fill_partner_logos(template)

        # --- move fonts and images out of the manifest -----------------------
        moved = {}
        for uuid, entry in list(manifest.items()):
            if entry.get("compressed"):      # the runtime's own JS stays inline
                continue
            ext = EXT.get(entry.get("mime", ""))
            if not ext:
                continue
            raw = base64.b64decode(entry["data"])
            digest = hashlib.sha256(raw).hexdigest()[:16]
            sub = "assets/fonts" if entry["mime"].startswith("font/") else "assets/img"

            # A hand-optimised replacement wins over the exported original, so
            # re-exporting cannot quietly reinstate a multi-megabyte image.
            override = OVERRIDES.get(digest)
            if override:
                rel = f"assets/img/{override['use']}"
                if not os.path.exists(rel):
                    sys.exit(f"override for {digest} names a missing file: {rel}")
                overridden.add(digest)
            else:
                rel = f"{sub}/{digest}{ext}"
                if rel not in store:
                    os.makedirs(sub, exist_ok=True)
                    open(rel, "wb").write(raw)
                    store[rel] = len(raw)

            moved[uuid] = "/" + rel
            del manifest[uuid]
        for uuid, url in moved.items():
            template = template.replace(uuid, url)

        # --- lift the shared @font-face rules out of every page ---------------
        faces = re.findall(r"@font-face\s*\{[^}]*\}\s*", template)
        if faces and not faces_written:
            open(FONT_CSS, "w", encoding="utf8").write(
                "".join(f.strip() + "\n" for f in faces))
            faces_written = True
        template = re.sub(r"@font-face\s*\{[^}]*\}\s*", "", template)
        template = template.replace(
            "</head>", f'<link rel="stylesheet" href="/{FONT_CSS}">\n</head>', 1)

        doc = put(doc, tpl_m, template)
        doc = put(doc, block(doc, "manifest"), manifest)

        os.makedirs(os.path.dirname(page) or ".", exist_ok=True)
        open(page, "w", encoding="utf8").write(doc)
        total += len(doc)
        note = f"   接回空循环 {len(wired)}" if wired else ""
        if logos_in: note += "   合作伙伴 logo 已填入"
        if dropped: note += f"   移除板块 {','.join(dropped)}"
        print(f"  {page:<22} {len(doc)/1024:>6.0f} KB   资源外置 {len(moved):>3}{note}")

    urls = "".join(
        f"  <url>\n    <loc>{site}{r}</loc>\n    <changefreq>monthly</changefreq>\n"
        f'    <priority>{"1.0" if r == "/" else "0.7"}</priority>\n  </url>\n'
        for _, _, r in PAGES)
    open("sitemap.xml", "w", encoding="utf8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")

    fonts = sum(v for k, v in store.items() if "fonts" in k)
    imgs = sum(v for k, v in store.items() if "img" in k)
    print(f"\n  HTML 合计 {total/1048576:.2f} MB")
    print(f"  字体 {len([k for k in store if 'fonts' in k])} 个 / {fonts/1048576:.2f} MB")
    print(f"  图片 {len([k for k in store if 'img' in k])} 个新增 / {imgs/1024:.0f} KB"
          f"，套用既有优化 {len(overridden)} 张")

    unused = [k for k in OVERRIDES if k not in overridden]
    if unused:
        print(f"\n  注意：{len(unused)} 条 override 未被用到，可能这张图已从设计中移除：")
        for k in unused:
            print(f"    {k} -> {OVERRIDES[k]['use']}")

    fresh = [k for k in store if "img" in k and store[k] > 400_000]
    if fresh:
        print("\n  以下新配图超过 400 KB，按 README 手工压缩后登记进 image-overrides.json：")
        for k in fresh:
            print(f"    {k}  {store[k]/1024:.0f} KB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(os.path.abspath(sys.argv[1]))
