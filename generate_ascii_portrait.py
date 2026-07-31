from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


GRID_WIDTH = 150
GRID_HEIGHT = 170
CELL_SIZE = 2
ANIMATION_GROUPS = 12


def crop_to_aspect(image: Image.Image, target_aspect: float) -> Image.Image:
    """Crop around the upper-center area while matching the SVG aspect ratio."""
    width, height = image.size
    current_aspect = width / height

    if current_aspect > target_aspect:
        new_width = int(height * target_aspect)
        left = (width - new_width) // 2
        return image.crop((left, 0, left + new_width, height))

    new_height = int(width / target_aspect)

    # Keep slightly more of the upper portion for face/upper-body portraits.
    available = height - new_height
    top = max(0, int(available * 0.25))
    top = min(top, available)

    return image.crop((0, top, width, top + new_height))


def prepare_image(photo_path: Path) -> Image.Image:
    image = Image.open(photo_path)
    image = ImageOps.exif_transpose(image).convert("RGB")

    target_aspect = GRID_WIDTH / GRID_HEIGHT
    image = crop_to_aspect(image, target_aspect)

    resampling = getattr(Image, "Resampling", Image).LANCZOS
    image = image.resize((GRID_WIDTH, GRID_HEIGHT), resampling)

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)

    # Dark areas become visible SVG pixels.
    ink = ImageOps.invert(gray)

    # Suppress weak background noise.
    ink = ink.point(
        lambda value: 0 if value < 24 else min(255, int(value * 1.18))
    )

    dither = getattr(Image, "Dither", Image).FLOYDSTEINBERG
    return ink.convert("1", dither=dither)


def make_path_for_group(bitmap: Image.Image, group_index: int) -> str:
    commands: list[str] = []

    for y in range(GRID_HEIGHT):
        # Interlaced groups progressively assemble the entire portrait.
        if y % ANIMATION_GROUPS != group_index:
            continue

        x = 0

        while x < GRID_WIDTH:
            active = bitmap.getpixel((x, y)) != 0

            if not active:
                x += 1
                continue

            start_x = x

            while x < GRID_WIDTH and bitmap.getpixel((x, y)) != 0:
                x += 1

            run_length = x - start_x

            svg_x = start_x * CELL_SIZE
            svg_y = y * CELL_SIZE
            svg_width = run_length * CELL_SIZE

            # Draw a compact horizontal rectangle.
            commands.append(
                f"M{svg_x} {svg_y}"
                f"h{svg_width}"
                f"v{CELL_SIZE}"
                f"h-{svg_width}z"
            )

    return "".join(commands)


def build_svg_group(bitmap: Image.Image) -> str:
    output: list[str] = [
        '<g transform="translate(50,86) scale(1.2400,1.4471)" '
        'fill="url(#asciiGrad)" shape-rendering="crispEdges">',
        '  <set attributeName="opacity" to="0" begin="3.2s"/>',
    ]

    for index in range(ANIMATION_GROUPS):
        path_data = make_path_for_group(bitmap, index)

        if not path_data:
            continue

        begin = 0.20 + index * 0.055

        output.extend(
            [
                '  <g opacity="0">',
                (
                    '    <animate attributeName="opacity" values="0;1" '
                    f'dur="0.9s" begin="{begin:.2f}s" fill="freeze" '
                    'calcMode="spline" keyTimes="0;1" '
                    'keySplines=".4 0 .2 1"/>'
                ),
                f'    <path d="{path_data}"/>',
                "  </g>",
            ]
        )

    output.append("</g>")
    return "\n".join(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a portrait photo into an animated SVG pixel portrait."
    )
    parser.add_argument("photo", type=Path, help="Path to the JPG or PNG photo")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("portrait_group.svg"),
        help="Generated SVG group output",
    )
    args = parser.parse_args()

    if not args.photo.exists():
        raise FileNotFoundError(f"Photo not found: {args.photo}")

    bitmap = prepare_image(args.photo)
    svg_group = build_svg_group(bitmap)

    args.output.write_text(svg_group, encoding="utf-8")

    print(f"Generated: {args.output}")
    print("Replace the old animated portrait group in dark.svg with this output.")


if __name__ == "__main__":
    main()
