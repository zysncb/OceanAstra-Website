#!/usr/bin/env python3
"""
Bake the rendered DOM back into each page as static HTML.

    python3 tools/prerender.py [--check]

Design Canvas exports a client-rendered bundle: the shipped HTML carries the
head, ~200 KB of JavaScript, and fifteen characters of visible text. Googlebot
executes JavaScript and eventually sees the page; the crawlers behind AI answer
engines — GPTBot, ClaudeBot, PerplexityBot, Bingbot's non-JS path — generally do
not. To them the site reads as "OA Unpacking...".

So we render each page in headless Chrome once, at build time, and write the
resulting DOM back over the file. The visual result is identical because it IS
the result the browser produces; the difference is that the text now arrives in
the HTTP response instead of being assembled afterwards.

Run this AFTER prepare-export.py — it must see the finished head, and its output
would otherwise be overwritten.

--check re-renders into memory and reports the text each page would serve
without executing any JavaScript, changing nothing on disk.
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

# The bundler's own boot scaffolding. It removes these itself once it has
# rendered, so they are normally absent from the dump — but a render that is
# cut short would bake the loading state in permanently, which is worse than
# shipping nothing. Their presence is treated as a failed render, not tidied.
BOOT_MARKERS = ("__bundler_thumbnail", "__bundler_placeholder", "__bundler_loading")


def serve(directory):
    """A quiet static server on an ephemeral port, for Chrome to render from."""
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
    body = body.group(1) if body else ""
    body = re.sub(r"<script.*?</script>", "", body, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def render(port, page):
    url = f"http://127.0.0.1:{port}/{page + '/' if page else ''}"
    out = subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--virtual-time-budget=15000", "--dump-dom", url],
        capture_output=True, text=True, timeout=120,
    )
    if out.returncode != 0:
        raise RuntimeError(f"chrome exited {out.returncode} for {url}\n{out.stderr[:400]}")
    return out.stdout


def main():
    check_only = "--check" in sys.argv
    if not Path(CHROME).exists():
        sys.exit(f"Chrome not found at {CHROME}")

    httpd, port = serve(ROOT)
    try:
        print(f"\n  {'page':<12} {'before':>10} {'after':>10}   status")
        print("  " + "-" * 46)
        failures = []

        for page in PAGES:
            path = ROOT / (f"{page}/index.html" if page else "index.html")
            before = len(visible_text(path.read_text(encoding="utf-8")))
            html = render(port, page)
            after = len(visible_text(html))

            stalled = [m for m in BOOT_MARKERS if m in html]
            if stalled or after < 500:
                failures.append((page or "/", stalled or f"only {after} chars"))
                print(f"  {page or '/':<12} {before:>10} {after:>10}   FAILED")
                continue

            if not check_only:
                path.write_text(html, encoding="utf-8")
            print(f"  {page or '/':<12} {before:>10} {after:>10}   ok")

        if failures:
            print("\n  Renders that did not complete — nothing written for these:")
            for page, why in failures:
                print(f"    {page}: {why}")
            sys.exit(1)

        print(f"\n  {'Checked' if check_only else 'Wrote'} {len(PAGES)} pages.\n")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
