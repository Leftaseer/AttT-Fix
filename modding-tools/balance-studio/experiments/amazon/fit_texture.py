"""Prepare the generated Amazon atlas for the stock UVs on the remastered model."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from remaster import write_dds


def clean_hair_alpha(stock, repaint):
    # The transparent island is the hair card mask. The stock DDS stores
    # scattered binary texels there, which survive a regular upscale.
    size = repaint.size
    original = stock.getchannel("A")
    closed = original.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    guide = closed.filter(ImageFilter.GaussianBlur(1.2)).resize(size, Image.Resampling.BICUBIC)
    matte = np.asarray(guide, dtype=np.float32) / 255

    # Keep the solid core and use the repainted strands to guide the fringe.
    brightness = np.asarray(repaint)[:, :, :3].max(axis=2).astype(np.float32)
    strands = np.clip((brightness - 7) / 23, 0, 1)
    contour = matte + strands * np.clip((0.7 - matte) / 0.4, 0, 1) * 0.19
    alpha = np.clip((contour - 0.36) / 0.14, 0, 1)
    return Image.fromarray(np.rint(alpha * 255).astype(np.uint8))


def fit_atlas(stock, generated, *, clean_hair=False):
    size = (2048, 2048)
    if stock.width != stock.height or stock.width not in (512, 1024) or generated.width != generated.height:
        raise ValueError("Expected a stock square atlas and a square repaint")

    source = stock.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    repaint = generated.convert("RGBA").resize(size, Image.Resampling.LANCZOS)

    # The repaint preserves the UV layout, with small shifts next to black gutters.
    # Recover the original paint where those gutters encroach on a colored edge.
    old = np.asarray(source)[:, :, :3].max(axis=2).astype(np.float32)
    new = np.asarray(repaint)[:, :, :3].max(axis=2).astype(np.float32)
    nearby = np.asarray(Image.fromarray(old.astype(np.uint8)).filter(ImageFilter.MinFilter(17)))
    repair = np.clip((old - 30) / 20, 0, 1) * np.clip((20 - new) / 15, 0, 1)
    repair *= np.clip((13 - nearby.astype(np.float32)) / 10, 0, 1)
    mask = Image.fromarray(np.rint(repair * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))
    atlas = Image.composite(source, repaint, mask)
    alpha = clean_hair_alpha(stock.convert("RGBA"), repaint) if clean_hair else source.getchannel("A")
    atlas.putalpha(alpha)
    return atlas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path, help="stock Amazon DDS")
    parser.add_argument("generated", type=Path, help="generated square texture atlas")
    parser.add_argument("output", type=Path, help="output directory")
    parser.add_argument("--clean-hair", action="store_true", help="rebuild the hair cutout mask")
    args = parser.parse_args()
    atlas = fit_atlas(Image.open(args.stock), Image.open(args.generated), clean_hair=args.clean_hair)
    args.output.mkdir(parents=True, exist_ok=True)
    atlas.save(args.output / "Amazon-Generated-Atlas.png")
    write_dds(args.output / "bsamazon.dds", atlas)


if __name__ == "__main__":
    main()
