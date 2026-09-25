#!/usr/bin/env python3
"""
converter.py — embeds photos as base64 data URIs directly into the
IMAGES block of erasmus.html. This is a build-time tool, run on your
own machine; it is not part of the shipped single-file website.

Usage:
    python3 converter.py --html erasmus.html --manifest manifest.json

manifest.json maps photo ids (must already exist in GALLERY_STRUCTURE /
IMAGES inside erasmus.html) to a source file on disk:

    {
      "home-1": "photos/airport.jpg",
      "leipzig-3": "photos/leipzig_altstadt.png"
    }

Any id not listed in the manifest is left untouched (its src stays "").
To add a photo beyond the current 5-per-gallery seed, first add its id
to both GALLERY_STRUCTURE and IMAGES in erasmus.html (and a matching
caption/blurb/alt entry per language in I18N), then list it here.

Requires Pillow:
    pip install pillow --break-system-packages
"""
import argparse
import base64
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

MAX_DIMENSION = 1600   # long edge in px — the main lever on base64 weight
JPEG_QUALITY = 70      # 70-85 is a reasonable range; lower = smaller file
START_MARKER = "/* ===== IMAGES:START ===== */"
END_MARKER = "/* ===== IMAGES:END ===== */"


def encode_image(path: Path) -> tuple[str, int]:
    """Resize/compress an image and return (data URI, encoded byte size)."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # respect phone camera orientation
    img = img.convert("RGB")
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    data = buf.getvalue()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{b64}", len(data)


def embed(html: str, manifest: dict[str, str]) -> tuple[str, int, int]:
    start = html.index(START_MARKER) + len(START_MARKER)
    end = html.index(END_MARKER)
    block = html[start:end]

    total_bytes = 0
    updated = 0
    for photo_id, path_str in manifest.items():
        path = Path(path_str)
        if not path.exists():
            print(f"  ! skip {photo_id}: {path} not found", file=sys.stderr)
            continue

        uri, size = encode_image(path)
        total_bytes += size

        pattern = re.compile(r'"' + re.escape(photo_id) + r'":\s*\{\s*src:\s*"[^"]*"\s*\}')
        new_block, n = pattern.subn(f'"{photo_id}": {{ src:"{uri}" }}', block, count=1)
        if n == 0:
            print(f'  ! id "{photo_id}" not found in IMAGES — add it to GALLERY_STRUCTURE/IMAGES first', file=sys.stderr)
            continue

        block = new_block
        updated += 1
        print(f"  {photo_id}: {path.name} -> {size / 1024:.0f} KB")

    return html[:start] + block + html[end:], updated, total_bytes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html", required=True, help="path to erasmus.html")
    ap.add_argument("--manifest", required=True, help="path to manifest.json")
    args = ap.parse_args()

    html_path = Path(args.html)
    html = html_path.read_text(encoding="utf-8")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))

    new_html, updated, total_bytes = embed(html, manifest)
    html_path.write_text(new_html, encoding="utf-8")

    mb = total_bytes / (1024 * 1024)
    print(f"\nEmbedded {updated} photo(s), {mb:.2f} MB of image data "
          f"(base64 text itself is ~33% larger than that).")
    if total_bytes > 15 * 1024 * 1024:
        print("Warning: getting large for a single HTML file — "
              "lower MAX_DIMENSION or JPEG_QUALITY and re-run.")


if __name__ == "__main__":
    main()
