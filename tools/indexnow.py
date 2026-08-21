#!/usr/bin/env python3
"""
Notify IndexNow that pages have changed.

    python3 tools/indexnow.py            # submit every URL in sitemap.xml
    python3 tools/indexnow.py /about/    # submit specific paths

IndexNow is a push protocol: instead of waiting for a crawler to come back on
its own schedule, the site tells it what changed. Bing, Yandex, Seznam and
Naver share one endpoint — submitting once reaches all of them. Google does not
participate.

Ownership is proved by hosting a file at the site root whose name is the key
and whose contents are the key. That file is committed to the repository; the
key is not a secret, it only demonstrates write access to the site.

A 200 or 202 means accepted. It does not mean indexed — it means the crawler
has been told, and will decide for itself.
"""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = "https://api.indexnow.org/indexnow"

STATUS = {
    200: "accepted",
    202: "accepted — key validation pending",
    400: "bad request — malformed URL list",
    403: "key not found or does not match the key file",
    422: "URLs do not belong to the declared host, or the key does not match",
    429: "rate limited — too many submissions",
}


def key_file():
    files = [p for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{8,128}", p.stem)]
    if not files:
        sys.exit("No IndexNow key file at the repository root.")
    if len(files) > 1:
        sys.exit(f"Several key files present, expected one: {[p.name for p in files]}")
    key = files[0].read_text(encoding="utf-8").strip()
    if key != files[0].stem:
        sys.exit(f"{files[0].name} must contain exactly its own name as contents.")
    return key, files[0].name


def sitemap_urls():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def main():
    company = json.loads((ROOT / "content/company.json").read_text(encoding="utf-8"))
    site = company["siteUrl"]
    host = company["domain"]
    key, filename = key_file()

    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    urls = [f"{site}{p}" for p in paths] if paths else sitemap_urls()

    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"{site}/{filename}",
        "urlList": urls,
    }

    print(f"\n  host        {host}")
    print(f"  key         {key}")
    print(f"  keyLocation {payload['keyLocation']}")
    print(f"  urls        {len(urls)}")
    for u in urls:
        print(f"                {u}")

    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            code, body = response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        code, body = e.code, e.read().decode(errors="replace")
    except urllib.error.URLError as e:
        sys.exit(f"\n  Could not reach {ENDPOINT}: {e.reason}\n")

    print(f"\n  HTTP {code} — {STATUS.get(code, 'unexpected response')}")
    if body.strip():
        print(f"  body: {body.strip()[:300]}")
    print()
    sys.exit(0 if code in (200, 202) else 1)


if __name__ == "__main__":
    main()
