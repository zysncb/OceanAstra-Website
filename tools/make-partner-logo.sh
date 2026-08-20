#!/bin/bash
# Compose a partner logo for the 3:1 slot on the homepage partners cards.
#
#   tools/make-partner-logo.sh <source.png> <name> <trim-h> <trim-w>
#
# Vendor logo files come with generous canvas padding — Lark's artwork occupies
# only 643x184 of a 766x400 canvas — so scaling by canvas height renders the
# artwork at a fraction of the intended size. Trim to the artwork first, scale
# the artwork itself to a fixed height, then pad to the slot ratio, so both
# partners' marks end up optically the same size.
#
# <trim-h>/<trim-w> are the centre-crop that removes the padding. Measure them
# rather than guessing, and when side padding is uneven, take the SMALLER side
# doubled so the crop cannot eat into the artwork:
#
#   Lark  artwork 643x184 in 766x400, sides 52/71  ->  184 662
#   Amap  artwork 754x252 in 800x418, sides 23/23  ->  252 754
#
# Verify a new logo against the rendered card before shipping it; a mark with a
# second line of small type (Amap has 高德地图) loses that line if scaled down.

set -euo pipefail
[ $# -eq 4 ] || { sed -n '2,20p' "$0"; exit 1; }

SRC=$1; NAME=$2; TRIM_H=$3; TRIM_W=$4
ART_HEIGHT=56          # artwork height inside the 80px canvas
CANVAS="80 240"        # 2x of the 120x40 slot
PLATE=F2F2F0           # the identity's light tone; both marks are dark wordmarks
OUT="assets/img/partners/${NAME}.png"

mkdir -p assets/img/partners
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cp "$SRC" "$TMP/0.png"
sips -c "$TRIM_H" "$TRIM_W" "$TMP/0.png" --out "$TMP/1.png" >/dev/null
sips --resampleHeight "$ART_HEIGHT" "$TMP/1.png" --out "$TMP/2.png" >/dev/null
sips --padToHeightWidth $CANVAS --padColor "$PLATE" "$TMP/2.png" --out "$OUT" >/dev/null

echo "$OUT  $(sips -g pixelWidth -g pixelHeight "$OUT" | tail -2 | awk '{printf "%s", $2"x"}' | sed 's/x$//')  $(ls -lh "$OUT" | awk '{print $5}')"
