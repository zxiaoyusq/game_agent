#!/usr/bin/env python3
"""Convert a flat ImageGen chroma background to transparency."""

import argparse
import sys
from pathlib import Path

from PIL import Image


def parse_hex_color(value):
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError("key color must be a 6 digit hex color, for example #00ff00")
    try:
        return tuple(int(value[index:index + 2], 16) for index in range(0, 6, 2))
    except ValueError as error:
        raise ValueError("key color must be hexadecimal") from error


def remove_chroma_key(source_path, output_path, key_color=(0, 255, 0), tolerance=28, softness=34):
    if tolerance < 0 or softness <= 0:
        raise ValueError("tolerance must be non-negative and softness must be positive")
    with Image.open(source_path) as source:
        image = source.convert("RGBA")
    pixels = image.load()
    max_distance = tolerance + softness
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            distance = ((red - key_color[0]) ** 2 + (green - key_color[1]) ** 2 + (blue - key_color[2]) ** 2) ** 0.5
            if distance <= tolerance:
                pixels[x, y] = (red, green, blue, 0)
            elif distance < max_distance:
                retained = round(alpha * (distance - tolerance) / softness)
                pixels[x, y] = (red, green, blue, retained)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Remove a flat chroma background from an image")
    parser.add_argument("--input", required=True, help="ImageGen output with a flat chroma background")
    parser.add_argument("--output", required=True, help="RGBA PNG to write")
    parser.add_argument("--key", default="#00ff00", help="Background key color, default #00ff00")
    parser.add_argument("--tolerance", type=float, default=28, help="Color distance removed completely")
    parser.add_argument("--softness", type=float, default=34, help="Soft alpha transition width")
    args = parser.parse_args(argv)
    try:
        remove_chroma_key(args.input, args.output, parse_hex_color(args.key), args.tolerance, args.softness)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
