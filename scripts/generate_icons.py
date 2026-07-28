#!/usr/bin/env python3
"""Generate all icon sizes and formats from the master SVG source.

One-time script — run after creating or modifying assets/icon.svg.
Generates:
  - 8 PNG sizes (16, 32, 48, 64, 128, 180, 192, 512) in assets/icons/
  - Multi-res favicon.ico in assets/
  - 1200×630 Open Graph social preview image in assets/

Requires: cairosvg, pillow (pip install cairosvg pillow)
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_SOURCE = ROOT / "assets" / "icon.svg"
OUTPUT_DIR = ROOT / "assets" / "icons"
FAVICON_PATH = ROOT / "assets" / "favicon.ico"
OG_IMAGE_PATH = ROOT / "assets" / "og-image.png"

SIZES = [16, 32, 48, 64, 128, 180, 192, 512]


def generate_pngs() -> None:
    """Rasterize SVG to PNG at each required size."""
    try:
        import cairosvg  # noqa: F401 — imported inside to fail gracefully
    except ImportError:
        print("❌ cairosvg not installed. Run: pip install cairosvg")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for size in SIZES:
        out_path = OUTPUT_DIR / f"icon-{size}x{size}.png"
        cairosvg.svg2png(
            url=str(SVG_SOURCE),
            write_to=str(out_path),
            output_width=size,
            output_height=size,
        )
        print(f"  ✓ {out_path.name}")

    print(f"✅ Generated {len(SIZES)} PNG sizes in {OUTPUT_DIR}/")


def generate_ico() -> None:
    """Create a multi-resolution .ico file from the 32px PNG."""
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("❌ Pillow not installed. Run: pip install Pillow")
        sys.exit(1)

    img = Image.open(OUTPUT_DIR / "icon-32x32.png")
    img.save(
        FAVICON_PATH,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    print(f"  ✓ {FAVICON_PATH.name}")


def generate_og_image() -> None:
    """Create a 1200×630 Open Graph social share preview image."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    except ImportError:
        print("❌ Pillow not installed. Run: pip install Pillow")
        sys.exit(1)

    img = Image.new("RGB", (1200, 630), "#0a0a0f")
    draw = ImageDraw.Draw(img)

    # Paste the icon at center-top
    icon_path = OUTPUT_DIR / "icon-512x512.png"
    if icon_path.exists():
        icon = Image.open(icon_path).resize((200, 200))
        # Use alpha channel as mask if present
        mask = icon.split()[3] if icon.mode == "RGBA" else None
        img.paste(icon, (500, 80), mask)

    # Try to use a system font, fall back to default
    title_font = None
    subtitle_font = None
    font_candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                title_font = ImageFont.truetype(fp, 52)
                subtitle_font = ImageFont.truetype(fp, 28)
                break
            except OSError:
                continue

    if title_font is None:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # Title
    bbox = draw.textbbox((0, 0), "GA4 Insight Explorer", font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((1200 - tw) // 2, 340), "GA4 Insight Explorer", fill="#f0f0f5", font=title_font)

    # Subtitle
    bbox = draw.textbbox((0, 0), "Analyze GA4 data with natural language — powered by Gemini AI", font=subtitle_font)
    sw = bbox[2] - bbox[0]
    draw.text(((1200 - sw) // 2, 420), "Analyze GA4 data with natural language — powered by Gemini AI", fill="#9898b0", font=subtitle_font)

    img.save(OG_IMAGE_PATH)
    print(f"  ✓ {OG_IMAGE_PATH.name}")


def main() -> None:
    print("🎨 Generating app icons from assets/icon.svg ...\n")
    generate_pngs()
    generate_ico()
    generate_og_image()
    print(f"\n✅ All done! Icons ready in {OUTPUT_DIR}/ and {ROOT / 'assets'}/")


if __name__ == "__main__":
    main()
