#!/usr/bin/env python3
"""
Make the language switcher change the URL, so the choice survives a click.

    python3 tools/lang-urls.py

Run AFTER localise.py and BEFORE prerender.py — the same window as link-faq.py.

localise.py published the Chinese and Arabic sites at /zh/ and /ar/, but left
the header switcher doing what the export always did:

    pick: () => this.setState({ lang: l.code, navOpen: false })

That re-renders the current page in the chosen language and changes nothing
else. The URL stays /, <html lang> stays "en", and every internal link is still
a relative link to the English copy. So the language held until the visitor
clicked anything — nav item, footer link, hero button — and then the next page
booted from the defaultLang baked into its own data-props and came back in
English. The switch worked; it just had a lifetime of one page.

The fix is to switch by navigating rather than by re-rendering: from /about/,
中文 goes to /zh/about/, and from there every relative link stays inside /zh/
on its own. Language is then carried by the URL, which means it also survives
a reload, a bookmark and a link sent to someone else, and <html lang> is right
because each locale directory ships it in the served HTML.

/faq/ already switches this way — build-faq.py writes /faq/, /zh/faq/ and
/ar/faq/ as real anchors. This makes the six exported pages agree with it.

Three edits per page, all inside the template's text/x-dc script:

  - localeHref(), which maps the current path to its equivalent under another
    locale by adding or removing the leading directory segment;
  - switchLang(), the click handler — it navigates, or just closes the mobile
    nav if the visitor picked the language already showing;
  - pick, repointed from setState to switchLang.

The state field it used to set stays where it is: `lang: null` in state and
`this.state.lang || this.props.defaultLang || "en"` in renderVals still work,
and a re-export that puts the old handler back will still run.

This is post-processing over generated code and a re-export will discard it,
which is true of everything the pipeline does — it is meant to be re-run.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["", "solutions", "about", "contact", "privacy", "terms"]
LOCALES = ["", "zh", "ar"]

TEMPLATE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)

LANGS_CONST = re.compile(r'const LANGS = \[.*?\];', re.S)
RENDER_VALS = re.compile(r'( *)renderVals\(\) \{')
PICK = re.compile(r'pick: \(\) => this\.setState\(\{ lang: l\.code, navOpen: false \}\)')

# Derives the locale directories from LANGS rather than hardcoding zh|ar, so a
# fourth language added in Design Canvas needs no edit here. "en" has no
# directory of its own: the English site is the root.
HELPER = '''

function localeHref(code) {
  const loc = window.location;
  const dirs = LANGS.map(l => l.code).filter(c => c !== "en");
  const seg = loc.pathname.split("/")[1];
  const bare = dirs.indexOf(seg) >= 0 ? loc.pathname.slice(seg.length + 1) || "/" : loc.pathname;
  return (code === "en" ? "" : "/" + code) + bare + loc.search + loc.hash;
}'''

METHOD = '''switchLang(code) {
{i}  const href = localeHref(code);
{i}  const here = window.location.pathname + window.location.search + window.location.hash;
{i}  if (href === here) { this.setState({ navOpen: false }); return; }
{i}  window.location.assign(href);
{i}}

{i}'''


def patch(template):
    """Return (template, [helper, method, pick]) counts."""
    counts = [0, 0, 0]

    template, counts[0] = LANGS_CONST.subn(lambda m: m.group(0) + HELPER, template, count=1)

    def method(m):
        indent = m.group(1)
        return indent + METHOD.replace("{i}", indent) + m.group(0).lstrip()

    template, counts[1] = RENDER_VALS.subn(method, template, count=1)
    template, counts[2] = PICK.subn("pick: () => this.switchLang(l.code)", template, count=1)
    return template, counts


def main():
    print(f"\n  {'page':<24} {'helper':>7} {'method':>7} {'pick':>6}")
    print("  " + "-" * 48)

    written, skipped, failed = 0, 0, []
    for locale in LOCALES:
        for page in PAGES:
            rel = f"{page}/index.html" if page else "index.html"
            path = ROOT / (rel if not locale else f"{locale}/{rel}")
            label = (locale + "/" if locale else "/") + (page or "")
            html = path.read_text(encoding="utf-8")

            match = TEMPLATE.search(html)
            if not match:
                print(f"  {label:<24} {'no __bundler/template':>22}")
                failed.append(label)
                continue

            template = json.loads(match.group(2))
            if "switchLang" in template:
                print(f"  {label:<24} {'already patched':>22}")
                skipped += 1
                continue

            template, counts = patch(template)
            if counts != [1, 1, 1]:
                print(f"  {label:<24} {counts[0]:>7} {counts[1]:>7} {counts[2]:>6}   <- expected 1 1 1")
                failed.append(label)
                continue

            # Re-encoding must escape "</" — the template contains a nested
            # </script> and leaving it literal ends the enclosing script
            # element early and truncates the page.
            encoded = json.dumps(template, ensure_ascii=False).replace("</", "<\\/")
            path.write_text(html[:match.start(2)] + encoded + html[match.end(2):], encoding="utf-8")

            # The truncation above is silent in the browser, so prove the file
            # still round-trips: a literal </script> would make this regex stop
            # short and json.loads fail on the fragment.
            reread = TEMPLATE.search(path.read_text(encoding="utf-8"))
            try:
                if "switchLang" not in json.loads(reread.group(2)):
                    raise ValueError("patch missing after write")
            except Exception as exc:
                print(f"  {label:<24} re-read failed: {exc}")
                failed.append(label)
                continue

            print(f"  {label:<24} {counts[0]:>7} {counts[1]:>7} {counts[2]:>6}")
            written += 1

    if failed:
        sys.exit(f"\n  Not patched: {', '.join(failed)} — the export's switcher changed.\n")
    print(f"\n  Patched {written} page(s), {skipped} already done.\n")


if __name__ == "__main__":
    main()
