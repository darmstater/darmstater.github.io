#!/bin/bash
DST="D:/CODE/BIN/ANNIV_OPT/asset/anniv"

compress() {
  local src="$1"
  local out="$2"
  local fname=$(basename "$src")
  local sb=$(stat -c%s "$src")
  echo "=== $fname ($(($sb/1024/1024))MB) ==="

  # Try with audio first
  ffmpeg -y -i "$src" \
    -vf "scale=-2:720" \
    -c:v libx264 -crf 28 -preset fast \
    -c:a aac -b:a 128k \
    -movflags +faststart \
    "$out" 2>/dev/null

  local sa=$(stat -c%s "$out" 2>/dev/null || echo 0)
  if [ "$sa" -lt 1000 ]; then
    echo "  Retry: no audio..."
    ffmpeg -y -i "$src" \
      -vf "scale=-2:720" \
      -c:v libx264 -crf 28 -preset fast \
      -an \
      -movflags +faststart \
      "$out" 2>/dev/null
    sa=$(stat -c%s "$out" 2>/dev/null || echo 0)
  fi

  if [ "$sa" -lt 1000 ]; then
    echo "  Retry: copy + rescale..."
    ffmpeg -y -i "$src" \
      -vf "scale=-2:720" \
      -c:v libx264 -crf 28 -preset fast \
      -c:a copy \
      -movflags +faststart \
      -fflags +genpts \
      "$out" 2>/dev/null
    sa=$(stat -c%s "$out" 2>/dev/null || echo 0)
  fi

  if [ "$sa" -lt 1000 ]; then
    echo "  FAILED - copying original"
    cp "$src" "$out"
    sa=$(stat -c%s "$out")
  fi

  echo "  Result: $(($sb/1024/1024))MB -> $(($sa/1024/1024))MB"
}

# Videos that failed
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20250517_063252.mp4"  "$DST/VID_20250517_063252.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20250529_224354.mp4"  "$DST/VID_20250529_224354.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20250927_090016.mp4"  "$DST/VID_20250927_090016.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20251018_162914.mp4"  "$DST/VID_20251018_162914.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20251102_200032.mp4"  "$DST/VID_20251102_200032.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20251129_225936.mp4"  "$DST/VID_20251129_225936.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20251206_134456.mp4"  "$DST/VID_20251206_134456.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20260208_164914.mp4"  "$DST/VID_20260208_164914.mp4"
compress "D:/CODE/BIN/ANNIV/asset/anniv/VID_20260315_202049.mp4"  "$DST/VID_20260315_202049.mp4"
compress "D:/CODE/BIN/ANNIV/asset/video/gereja.mp4"               "D:/CODE/BIN/ANNIV_OPT/asset/video/gereja.mp4"

echo ""
echo "=== DONE ==="
du -sh "D:/CODE/BIN/ANNIV_OPT/"
