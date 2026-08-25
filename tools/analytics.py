#!/usr/bin/env python3
"""
Put the Cloudflare Web Analytics beacon on every page.

    python3 tools/analytics.py <token>     # add or update
    python3 tools/analytics.py --remove    # take it off again

Run last, after seo-inject.py. Idempotent: it strips its own previous block
before writing, so running it twice is the same as running it once, and
changing the token is the same command with a different argument.

Where it goes, and why that was worth checking first. The bundle replaces the
whole document element on load — the served <head> is gone from the DOM by the
time the page is interactive, which is where an analytics snippet would
normally live. Measured with a probe page mimicking the real snippet:

  - an inline script in the served <head> runs;
  - an external script loaded from it runs too, and is not cut off by the swap;
  - document.currentScript is readable, so a beacon can read the data-* config
    off its own tag;
  - a timer set before the swap still fires four seconds after it — closures
    and listeners survive, because only documentElement is replaced, not
    window or document;
  - only the tag itself disappears, which matters solely to scripts that read
    their own element again later. Cloudflare's does not.

So the served <head> works. It is also the only safe place: putting the beacon
in the template would make it run again after the swap and count every visit
twice, and the template is JSON-encoded, where an unescaped "</" truncates the
page. The literal string "</head>" appears exactly once per file — the
template writes its own as "<\\/head>" — so anchoring there cannot reach it.

The beacon sets no cookie and stores nothing on the device. That is the reason
this site can count visits without a consent banner, and the privacy policy
says so; tools/privacy-cookies.py owns that wording. If the beacon is ever
swapped for something that does set a cookie, that paragraph is wrong until it
is rewritten, and a banner is owed.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARK = "<!-- analytics -->"
END = "<!-- /analytics -->"
BLOCK = re.compile(re.escape(MARK) + r".*?" + re.escape(END) + r"\s*", re.S)

# Permissive on purpose: the exact shape of a beacon token is Cloudflare's to
# change, and rejecting a valid one is worse than passing a typo through to a
# dashboard that stays empty — which the browser check at the end would catch.
TOKEN = re.compile(r"^[A-Za-z0-9]{16,64}$")


def pages():
    """Every published page: the eighteen bundle pages and the three FAQs."""
    found = sorted(
        p for p in ROOT.glob("**/index.html")
        if ".claude" not in p.parts and "node_modules" not in p.parts
    )
    return found


def snippet(token):
    return (f'{MARK}\n'
            f'<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" '
            f'data-cf-beacon=\'{{"token": "{token}"}}\'></script>\n'
            f'{END}')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().split("\n\n")[1])
    arg = sys.argv[1]
    removing = arg == "--remove"
    if not removing and not TOKEN.match(arg):
        sys.exit(f"\n  {arg!r} does not look like a beacon token.\n")

    files = pages()
    if not files:
        sys.exit("\n  No pages found.\n")

    print(f"\n  {'page':<26} {'was':>6}  {'now':>6}")
    print("  " + "-" * 42)

    failed = []
    for path in files:
        html = path.read_text(encoding="utf-8")
        had = len(BLOCK.findall(html))
        html = BLOCK.sub("", html)

        # The template writes its own close as "<\/head>", so the literal tag
        # is the served head and nothing else. Anything other than exactly one
        # means the page is not shaped the way this tool assumes.
        heads = html.count("</head>")
        label = str(path.relative_to(ROOT).parent).replace(".", "/")
        if heads != 1:
            print(f"  {label:<26} {had:>6}  {'—':>6}   {heads} </head> tags, expected 1")
            failed.append(label)
            continue

        if not removing:
            html = html.replace("</head>", snippet(arg) + "\n</head>", 1)
        path.write_text(html, encoding="utf-8")

        now = len(BLOCK.findall(path.read_text(encoding="utf-8")))
        want = 0 if removing else 1
        print(f"  {label:<26} {had:>6}  {now:>6}" + ("" if now == want else "   <- expected " + str(want)))
        if now != want:
            failed.append(label)

    if failed:
        sys.exit(f"\n  Failed: {', '.join(failed)}\n")
    verb = "removed from" if removing else "on"
    print(f"\n  Beacon {verb} {len(files)} page(s).\n")


if __name__ == "__main__":
    main()
