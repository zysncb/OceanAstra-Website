#!/usr/bin/env python3
"""
Bake a rendered copy of each page into the HTML, for crawlers that run no JS.

    python3 tools/prerender.py [--check]

Design Canvas ships a client-rendered bundle: the HTML carries the head, ~200 KB
of JavaScript, and fifteen characters of visible text. Googlebot executes
JavaScript and gets there eventually; the crawlers behind AI answer engines —
GPTBot, ClaudeBot, PerplexityBot — generally do not, and see "OA Unpacking...".

So each page is rendered once at build time and the result is inserted as a
static block, *alongside the original bundle rather than instead of it*. On
load the bundle parses its template and swaps the root element, discarding this
block and rendering as it always did. Nothing about the live page changes.

Two things that must not be repeated — an earlier version of this script did
both, and shipped them:

  1. RENDER AT A DESKTOP WIDTH. The export has no responsive CSS; only four
     media queries, all prefers-reduced-motion and print. Its layout is chosen
     in JavaScript from the window width. Rendering at Chrome's default 800x600
     and dropping the bundle froze the mobile header at every viewport, with no
     way back.
  2. STRIP blob: SCRIPTS. The runtime mints blob URLs against whatever origin
     rendered the page, so a dumped DOM carries srcs like
     blob:http://127.0.0.1:53780/… — dead everywhere but the machine that built
     it.

Verify with tools/compare-viewports.sh, which renders before and after at three
widths. Comparing the output against itself proves nothing; the earlier failure
looked fine that way.
"""

import http.server
import re
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["", "solutions", "about", "contact", "privacy", "terms"]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Wide enough to be unambiguously the desktop branch of the layout.
VIEWPORT = (1440, 900)

OPEN = "<!-- prerendered: static copy for crawlers; the bundle replaces it -->"
CLOSE = "<!-- /prerendered -->"

BLOB_SCRIPT = re.compile(r'<script[^>]*src="blob:[^"]*"[^>]*>\s*</script>\s*', re.I)
INERT_DATA = re.compile(r'<script[^>]*type="text/x-dc"[^>]*>.*?</script>\s*', re.S | re.I)
NOSCRIPT = re.compile(r'<noscript>\s*<style>#__bundler_loading[^<]*</style>.*?</noscript>\s*', re.S)
PAYLOAD = re.compile(re.escape(OPEN) + r".*?" + re.escape(CLOSE) + r"\s*", re.S)


def serve(directory):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(directory), **kw)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def visible_text(html):
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    body = body.group(1) if body else html
    body = re.sub(r"<script.*?</script>", "", body, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def render(port, page):
    url = f"http://127.0.0.1:{port}/{page + '/' if page else ''}"
    out = subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         f"--window-size={VIEWPORT[0]},{VIEWPORT[1]}",
         "--virtual-time-budget=15000", "--dump-dom", url],
        capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError(f"chrome exited {out.returncode} for {url}")
    return out.stdout


def bake(original, rendered):
    """Insert the rendered body into the original, ahead of its scripts."""
    body = re.search(r"<body[^>]*>(.*)</body>", rendered, re.S)
    if not body:
        raise RuntimeError("rendered output has no <body>")

    fragment = BLOB_SCRIPT.sub("", body.group(1))
    fragment = INERT_DATA.sub("", fragment)
    # The loading scaffolding belongs to the bundle, not to the content.
    fragment = re.sub(r'<div id="__bundler_(?:thumbnail|loading)".*?</div>\s*', "",
                      fragment, flags=re.S)

    if "blob:" in fragment:
        raise RuntimeError("blob: URL survived stripping — refusing to write")

    out = PAYLOAD.sub("", original)          # idempotent: drop any earlier bake
    out = NOSCRIPT.sub("", out)              # the page no longer needs JS to read

    # Ahead of the bundle's scripts but inside <body> — searching the whole
    # document finds the head's scripts first and buries the content there,
    # where it is not part of the page at all.
    body_at = out.index("<body")
    index = out.index("<script", body_at)
    return out[:index] + f"{OPEN}\n{fragment}\n{CLOSE}\n" + out[index:]


def main():
    check_only = "--check" in sys.argv
    if not Path(CHROME).exists():
        sys.exit(f"Chrome not found at {CHROME}")

    httpd, port = serve(ROOT)
    try:
        print(f"\n  rendering at {VIEWPORT[0]}x{VIEWPORT[1]}\n")
        print(f"  {'page':<12} {'text before':>12} {'text after':>11}   status")
        print("  " + "-" * 50)
        failed = []

        for page in PAGES:
            path = ROOT / (f"{page}/index.html" if page else "index.html")
            original = path.read_text(encoding="utf-8")
            before = len(visible_text(PAYLOAD.sub("", original)))

            rendered = render(port, page)
            if any(m in rendered for m in ("__bundler_thumbnail", "__bundler_placeholder")):
                failed.append((page or "/", "render did not complete"))
                print(f"  {page or '/':<12} {before:>12} {'-':>11}   FAILED")
                continue

            baked = bake(original, rendered)
            after = len(visible_text(baked))
            if after < 500:
                failed.append((page or "/", f"only {after} characters"))
                print(f"  {page or '/':<12} {before:>12} {after:>11}   FAILED")
                continue

            if not check_only:
                path.write_text(baked, encoding="utf-8")
            print(f"  {page or '/':<12} {before:>12} {after:>11}   ok")

        if failed:
            print("\n  Not written:")
            for page, why in failed:
                print(f"    {page}: {why}")
            sys.exit(1)

        print(f"\n  {'Checked' if check_only else 'Wrote'} {len(PAGES)} pages.")
        print("  Verify with tools/compare-viewports.sh before pushing.\n")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
