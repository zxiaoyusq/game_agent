#!/usr/bin/env python3
"""Remove white/bright matte contamination from the edge of RGBA cutouts."""

import argparse
from collections import deque
import sys
from pathlib import Path

from PIL import Image


NEIGHBORS = (
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
)


def edge_decontaminate(image):
    """Bleed trusted interior colours into alpha-edge pixels without changing alpha."""
    image = image.convert("RGBA")
    width, height = image.size
    pixels = list(image.getdata())
    alpha = [pixel[3] for pixel in pixels]

    def index(x, y):
        return y * width + x

    def has_lower_alpha_neighbor(x, y):
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                return True
            if alpha[index(nx, ny)] < 255:
                return True
        return False

    trusted = []
    for y in range(height):
        for x in range(width):
            current = index(x, y)
            if alpha[current] == 255 and not has_lower_alpha_neighbor(x, y):
                trusted.append(current)
    if not trusted:
        trusted = [current for current, value in enumerate(alpha) if value == 255]
    if not trusted:
        return image

    nearest_colour = [None] * len(pixels)
    queue = deque(trusted)
    for current in trusted:
        nearest_colour[current] = pixels[current][:3]

    while queue:
        current = queue.popleft()
        x = current % width
        y = current // width
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            neighbor = index(nx, ny)
            if alpha[neighbor] == 0 or nearest_colour[neighbor] is not None:
                continue
            nearest_colour[neighbor] = nearest_colour[current]
            queue.append(neighbor)

    result = list(pixels)
    for y in range(height):
        for x in range(width):
            current = index(x, y)
            if alpha[current] == 0:
                continue
            replace_colour = alpha[current] < 255 or has_lower_alpha_neighbor(x, y)
            if replace_colour and nearest_colour[current] is not None:
                red, green, blue = nearest_colour[current]
                result[current] = (red, green, blue, alpha[current])

    cleaned = Image.new("RGBA", image.size)
    cleaned.putdata(result)
    return cleaned


def decontaminate_file(source_path, output_path):
    with Image.open(source_path) as source:
        if source.mode != "RGBA":
            raise ValueError(f"source must be RGBA, got {source.mode}")
        cleaned = edge_decontaminate(source)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cleaned.save(output_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Remove white matte contamination from RGBA cutout edges")
    parser.add_argument("--input", required=True, help="RGBA PNG to clean")
    parser.add_argument("--output", required=True, help="Cleaned RGBA PNG")
    args = parser.parse_args(argv)
    try:
        decontaminate_file(args.input, args.output)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
