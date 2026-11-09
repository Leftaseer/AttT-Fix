"""Fit the generated body and head atlases to the starting hero's UVs."""

import argparse
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments/amazon"))
from fit_texture import fit_atlas
from remaster import write_dds


def restore_expression(stock, head, retouch):
    size = head.size
    original = stock.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    aligned = retouch.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    face = Image.blend(original, aligned, .48)

    # Use the stock face and the calmer repaint only on the facial skin.
    # The earlier head texture supplies the clean fringe, neck and eye atlas.
    region = [(165, 43), (183, 20), (232, 15), (256, 22), (283, 16),
              (328, 24), (351, 43), (362, 74), (373, 110), (367, 155),
              (350, 190), (318, 215), (264, 225), (211, 220), (171, 198),
              (150, 163), (143, 118), (151, 75)]
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).polygon([(x * size[0] / 512, y * size[1] / 512) for x, y in region], fill=255)
    result = Image.composite(face, head, mask.filter(ImageFilter.GaussianBlur(25)))
    result.putalpha(head.getchannel("A"))
    return result


def fit_textures(stock, body_input, head_input, output, face_retouch=None):
    output.mkdir(parents=True, exist_ok=True)
    body = fit_atlas(Image.open(stock / "warrior.dds"), Image.open(body_input))
    stock_head = Image.open(stock / "warriorhead.dds")
    head = fit_atlas(stock_head, Image.open(head_input), clean_hair=True)
    if face_retouch:
        head = restore_expression(stock_head, head, Image.open(face_retouch))
    for name, atlas in [("warriorhd", body), ("warriorheadhd", head)]:
        atlas.save(output / f"{name}.png")
        write_dds(output / f"{name}.dds", atlas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("body", type=Path)
    parser.add_argument("head", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--face-retouch", type=Path, help="stock-matched facial repaint")
    args = parser.parse_args()
    fit_textures(args.stock, args.body, args.head, args.output, args.face_retouch)


if __name__ == "__main__":
    main()
