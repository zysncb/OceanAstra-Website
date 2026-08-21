#!/usr/bin/env bash
# Render the working tree against a git ref at three widths and diff the images.
#
#   tools/compare-viewports.sh [ref] [path]
#
# The prerender step once froze the mobile layout into every page, and the
# output looked correct when compared against itself. It has to be compared
# against what the site rendered BEFORE the change — that is the whole point.
set -euo pipefail

REF="${1:-HEAD}"
PATH_="${2:-/}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTHS=(1440 768 375)
OUT=$(mktemp -d)
REPO=$(cd "$(dirname "$0")/.." && pwd)

# A pristine checkout of REF, served alongside the working tree.
BASE="$OUT/base"
mkdir -p "$BASE"
git -C "$REPO" archive "$REF" | tar -x -C "$BASE"

serve() { (cd "$1" && exec python3 -m http.server "$2" >/dev/null 2>&1) & echo $!; }
P1=$(serve "$BASE" 4801)
P2=$(serve "$REPO" 4802)
trap 'kill $P1 $P2 2>/dev/null || true' EXIT
sleep 1

printf '\n  %-8s %-12s %-12s %s\n' width before after verdict
printf '  %s\n' "----------------------------------------------"
status=0
for w in "${WIDTHS[@]}"; do
  for port in 4801 4802; do
    "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
      --window-size="$w",900 --virtual-time-budget=9000 \
      --screenshot="$OUT/$port-$w.png" "http://127.0.0.1:$port$PATH_" 2>/dev/null
  done
  a=$(shasum -a 256 "$OUT/4801-$w.png" | cut -c1-12)
  b=$(shasum -a 256 "$OUT/4802-$w.png" | cut -c1-12)
  if [ "$a" = "$b" ]; then verdict="identical"; else verdict="DIFFERS — inspect"; status=1; fi
  printf '  %-8s %-12s %-12s %s\n' "$w" "$a" "$b" "$verdict"
done

echo
echo "  images: $OUT"
echo "  (the starfield is randomised per render, so a diff is expected;"
echo "   open both images and check the layout, not the hash)"
exit $status
