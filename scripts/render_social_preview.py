#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1280
HEIGHT = 640
BACKGROUND = "#FFFFFF"
INK = "#111111"
MUTED = "#4B5563"
ACCENT = "#D9DDE3"

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "assets"
PNG_PATH = OUT_DIR / "social-preview.png"
SVG_PATH = OUT_DIR / "social-preview.svg"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SANS = "/System/Library/Fonts/SFNS.ttf"


def draw_png() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    title_font = font(SERIF, 74)
    headline_font = font(SANS, 34)
    body_font = font(SANS, 21)
    stat_font = font(SANS, 18)
    small_font = font(SANS, 16)

    x = 92
    y = 82

    draw.text((x, y), "YAO", fill=INK, font=title_font)
    y += 90
    draw.text((x, y), "Yielding AI Outcomes", fill=INK, font=headline_font)
    y += 60
    draw.text(
        (x, y),
        "A rigorous engineering, evaluation, governance, and portability system",
        fill=INK,
        font=body_font,
    )
    y += 34
    draw.text(
        (x, y),
        "for reusable agent skills.",
        fill=INK,
        font=body_font,
    )

    y += 62
    draw.line((x, y, WIDTH - 92, y), fill=ACCENT, width=2)
    y += 34

    score_box_w = 250
    score_box_h = 118
    draw.rounded_rectangle(
        (x, y, x + score_box_w, y + score_box_h),
        radius=18,
        outline=ACCENT,
        width=2,
        fill=BACKGROUND,
    )
    draw.text((x + 22, y + 18), "Weighted Score", fill=MUTED, font=stat_font)
    draw.text((x + 22, y + 48), "91.5", fill=INK, font=font(SERIF, 42))
    draw.text((x + 124, y + 62), "/ 100", fill=MUTED, font=stat_font)
    draw.text(
        (x + 22, y + 88),
        "Method 9.5 · Eval 9.5 · Governance 9.5",
        fill=MUTED,
        font=small_font,
    )

    pillar_x = x + score_box_w + 36
    pillar_y = y + 4
    pillars = [
        ("Engineering", "Unified CLI, CI, validation, reporting, and packaging."),
        ("Evaluation", "Holdouts, route confusion, judge-backed blind evals."),
        ("Governance", "Lifecycle, maturity, promotion, and review evidence."),
        ("Portability", "Neutral metadata, adapters, contracts, and degradation."),
    ]

    box_w = 400
    box_h = 68
    gap_x = 24
    gap_y = 18
    for idx, (label, desc) in enumerate(pillars):
        col = idx % 2
        row = idx // 2
        bx = pillar_x + col * (box_w + gap_x)
        by = pillar_y + row * (box_h + gap_y)
        draw.rounded_rectangle(
            (bx, by, bx + box_w, by + box_h),
            radius=16,
            outline=ACCENT,
            width=2,
            fill=BACKGROUND,
        )
        draw.text((bx + 18, by + 14), label, fill=INK, font=stat_font)
        draw.text((bx + 18, by + 38), desc, fill=MUTED, font=small_font)

    footer_y = HEIGHT - 84
    draw.line((x, footer_y - 26, WIDTH - 92, footer_y - 26), fill=ACCENT, width=2)
    draw.text(
        (x, footer_y),
        "Reusable agent skills with explicit boundaries, strict evaluation, visible governance, and local reliability.",
        fill=MUTED,
        font=small_font,
    )

    image.save(PNG_PATH)


def draw_svg() -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BACKGROUND}"/>
  <text x="92" y="142" font-family="Georgia, serif" font-size="74" fill="{INK}">YAO</text>
  <text x="92" y="206" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="34" fill="{INK}">Yielding AI Outcomes</text>
  <text x="92" y="266" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="21" fill="{INK}">A rigorous engineering, evaluation, governance, and portability system</text>
  <text x="92" y="300" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="21" fill="{INK}">for reusable agent skills.</text>
  <line x1="92" y1="362" x2="1188" y2="362" stroke="{ACCENT}" stroke-width="2"/>
  <rect x="92" y="396" width="250" height="118" rx="18" fill="{BACKGROUND}" stroke="{ACCENT}" stroke-width="2"/>
  <text x="114" y="430" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="18" fill="{MUTED}">Weighted Score</text>
  <text x="114" y="478" font-family="Georgia, serif" font-size="42" fill="{INK}">91.5</text>
  <text x="228" y="492" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="18" fill="{MUTED}">/ 100</text>
  <text x="114" y="514" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="16" fill="{MUTED}">Method 9.5 · Eval 9.5 · Governance 9.5</text>

  <rect x="378" y="400" width="400" height="68" rx="16" fill="{BACKGROUND}" stroke="{ACCENT}" stroke-width="2"/>
  <text x="396" y="428" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="18" fill="{INK}">Engineering</text>
  <text x="396" y="452" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="16" fill="{MUTED}">Unified CLI, CI, validation, reporting, and packaging.</text>

  <rect x="802" y="400" width="400" height="68" rx="16" fill="{BACKGROUND}" stroke="{ACCENT}" stroke-width="2"/>
  <text x="820" y="428" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="18" fill="{INK}">Evaluation</text>
  <text x="820" y="452" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="16" fill="{MUTED}">Holdouts, route confusion, judge-backed blind evals.</text>

  <rect x="378" y="486" width="400" height="68" rx="16" fill="{BACKGROUND}" stroke="{ACCENT}" stroke-width="2"/>
  <text x="396" y="514" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="18" fill="{INK}">Governance</text>
  <text x="396" y="538" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="16" fill="{MUTED}">Lifecycle, maturity, promotion, and review evidence.</text>

  <rect x="802" y="486" width="400" height="68" rx="16" fill="{BACKGROUND}" stroke="{ACCENT}" stroke-width="2"/>
  <text x="820" y="514" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="18" fill="{INK}">Portability</text>
  <text x="820" y="538" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="16" fill="{MUTED}">Neutral metadata, adapters, contracts, and degradation.</text>

  <line x1="92" y1="530" x2="1188" y2="530" stroke="transparent"/>
  <line x1="92" y1="556" x2="1188" y2="556" stroke="{ACCENT}" stroke-width="2"/>
  <text x="92" y="598" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="16" fill="{MUTED}">Reusable agent skills with explicit boundaries, strict evaluation, visible governance, and local reliability.</text>
</svg>
"""
    SVG_PATH.write_text(svg, encoding="utf-8")


def main() -> None:
    draw_png()
    draw_svg()
    print(f"Wrote {PNG_PATH}")
    print(f"Wrote {SVG_PATH}")


if __name__ == "__main__":
    main()
