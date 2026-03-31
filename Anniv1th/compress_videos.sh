#!/bin/bash
SRC="D:/CODE/BIN/ANNIV/asset/anniv"
DST="D:/CODE/BIN/ANNIV_OPT/asset/anniv"

total_before=0
total_after=0

for vid in "$SRC"/*.mp4 "$SRC"/*.webm; do
  [ -f "$vid" ] || continue
  fname=$(basename "$vid")
  # output always as mp4
  outname="${fname%.*}.mp4"
  out="$DST/$outname"

  size_before=$(stat -c%s "$vid")
  total_before=$((total_before + size_before))

  echo "=== Compressing: $fname ($(($size_before / 1024 / 1024))MB) ==="

  ffmpeg -y -i "$vid" \
    -vf "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease" \
    -c:v libx264 -crf 28 -preset fast \
    -c:a aac -b:a 128k \
    -movflags +faststart \
    "$out" 2>&1 | tail -3

  if [ -f "$out" ]; then
    size_after=$(stat -c%s "$out")
    total_after=$((total_after + size_after))
    echo "Result: $(($size_before/1024/1024))MB -> $(($size_after/1024/1024))MB"
  fi
  echo ""
done

# Also compress main video
echo "=== Compressing: gereja.mp4 ==="
SRC2="D:/CODE/BIN/ANNIV/asset/video/gereja.mp4"
OUT2="D:/CODE/BIN/ANNIV_OPT/asset/video/gereja.mp4"
sb=$(stat -c%s "$SRC2")
ffmpeg -y -i "$SRC2" \
  -vf "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease" \
  -c:v libx264 -crf 28 -preset fast \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  "$OUT2" 2>&1 | tail -3
sa=$(stat -c%s "$OUT2")
echo "gereja.mp4: $(($sb/1024/1024))MB -> $(($sa/1024/1024))MB"

echo ""
echo "=== TOTAL VIDEO: $(($total_before/1024/1024))MB -> $(($total_after/1024/1024))MB ==="
