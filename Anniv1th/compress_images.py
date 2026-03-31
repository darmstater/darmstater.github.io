import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

SRC = Path("D:/CODE/BIN/ANNIV/asset/anniv")
DST = Path("D:/CODE/BIN/ANNIV_OPT/asset/anniv")
DST.mkdir(parents=True, exist_ok=True)

MAX_SIZE = (1920, 1920)
QUALITY = 82
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".JPG", ".JPEG", ".PNG", ".WEBP", ".HEIC"}

files = list(SRC.iterdir())
images = [f for f in files if f.suffix.lower() in {e.lower() for e in IMG_EXTS}]
videos = [f for f in files if f.suffix.lower() in {".mp4", ".webm"}]

print(f"Images: {len(images)}, Videos: {len(videos)} (videos handled separately)")

total_before = 0
total_after = 0

for i, img_path in enumerate(sorted(images)):
    try:
        size_before = img_path.stat().st_size
        total_before += size_before

        img = Image.open(img_path)

        # Convert to RGB if needed
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if larger than max
        img.thumbnail(MAX_SIZE, Image.LANCZOS)

        # Output always as JPG
        out_name = img_path.stem + ".jpg"
        out_path = DST / out_name

        img.save(out_path, "JPEG", quality=QUALITY, optimize=True)

        size_after = out_path.stat().st_size
        total_after += size_after

        ratio = (1 - size_after / size_before) * 100
        print(f"[{i+1}/{len(images)}] {img_path.name} → {out_name}: {size_before//1024}KB → {size_after//1024}KB ({ratio:.0f}% smaller)")

    except Exception as e:
        print(f"ERROR {img_path.name}: {e}")

print(f"\nTotal images: {total_before/1024/1024:.1f}MB → {total_after/1024/1024:.1f}MB")
print(f"Saved: {(total_before-total_after)/1024/1024:.1f}MB ({(1-total_after/total_before)*100:.0f}%)")
