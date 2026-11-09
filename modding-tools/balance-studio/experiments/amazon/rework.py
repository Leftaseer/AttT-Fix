"""Build the Amazon experiment from stock Amazon SKM and DDS assets."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# Load the original format and PN tools from the archived HD project.
import dds
import pn
import skm


def sculpt_rigid(part, pivot, scale, mask):
    vertices = part["v"]
    vertices["p"][mask] = pivot + (vertices["p"][mask] - pivot) * scale
    normals = vertices["n"][mask] / scale
    vertices["n"][mask] = normals / np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)


def rework_mesh(source, target, detail):
    mesh = skm.read(source.read_bytes())
    body, = mesh["skin"]
    shoulder, spear = mesh["rigid"]
    if [body["name"], shoulder["name"], spear["name"]] != [b"0Amazon", b"1Naplecnik", b"2Spear"]:
        raise ValueError(f"Unexpected object layout in {source}")
    if detail:
        body = skm.pack_skin(pn.refine(skm.unpack_skin(body), level=2))
        mesh["skin"][0] = body
    sculpt_rigid(shoulder, np.array([0.08, -0.03, -0.02]), np.array([1.22, 1.18, 1.17]), slice(None))
    sculpt_rigid(spear, np.zeros(3), np.array([2.8, 1.45, 1.0]), spear["v"]["p"][:, 2] > 1.48)
    for part in [body, shoulder, spear]:
        for material in part["mats"]:
            if material["tex"].lower() == b"amazon.dds":
                material["tex"] = b"bsamazon.dds"
    target.write_bytes(skm.write(mesh))
    print(f"{target.name}: {sum(len(part['idx']) // 3 for part in [body, shoulder, spear])} triangles")


def rework_texture(source, target):
    stock = Image.open(source).convert("RGBA")
    if stock.size != (512, 512):
        raise ValueError("Expected the stock 512×512 Amazon atlas")
    scale = 2
    atlas = stock.resize((1024, 1024), Image.Resampling.LANCZOS)
    pixels = np.array(atlas)
    luminance = pixels[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722])

    def dye(mask, dark, bright, reference=185):
        tones = np.clip(luminance[:, :, None] / reference, 0, 1.35)
        color = np.clip(np.array(dark) + (np.array(bright) - dark) * tones, 0, 255)
        weight = np.asarray(mask, dtype=np.float32)[:, :, None] / 255
        pixels[:, :, :3] = np.round(pixels[:, :, :3] * (1 - weight) + color * weight)

    # Dye the buckled skirt panels and keep the brighter hardware as metal.
    leather = Image.new("L", atlas.size)
    draw = ImageDraw.Draw(leather)
    draw.polygon([(x * scale, y * scale) for x, y in [(342, 317), (377, 299), (427, 309),
                                                       (426, 370), (343, 373)]], fill=255)
    draw.polygon([(x * scale, y * scale) for x, y in [(435, 324), (485, 318), (486, 388),
                                                       (479, 441), (430, 444)]], fill=255)
    hardware = np.clip((183 - luminance) / 50, 0, 1)
    dye(Image.fromarray(np.uint8(np.asarray(leather) * hardware)), [5, 18, 21], [57, 133, 136], 132)

    # Follow the torso UV island with a low cuirass, open neckline and a bronze rim.
    outline = [(9, 76), (67, 75), (105, 79), (139, 85), (165, 105), (190, 85),
               (222, 79), (267, 75), (314, 76), (314, 183), (263, 185), (221, 188),
               (193, 201), (165, 218), (137, 201), (109, 188), (65, 185), (9, 183)]
    shape = [(x * scale, y * scale) for x, y in outline]
    bodice = Image.new("L", atlas.size)
    ImageDraw.Draw(bodice).polygon(shape, fill=255)
    dye(bodice, [8, 23, 28], [45, 119, 125], 175)

    details = Image.new("RGBA", atlas.size)
    trim = ImageDraw.Draw(details)
    trim.line(shape + [shape[0]], fill=(103, 58, 29, 255), width=10, joint="curve")
    trim.line(shape + [shape[0]], fill=(224, 163, 83, 255), width=4, joint="curve")
    for shift in (0, 14, 28, 42):
        seam = [(x * scale, (y + shift) * scale) for x, y in
                [(14, 91), (68, 92), (105, 99), (142, 112), (165, 129),
                 (189, 112), (224, 99), (268, 92), (311, 91)]]
        trim.line(seam, fill=(6, 34, 39, 144), width=3, joint="curve")
    trim.polygon([(330, 312), (346, 333), (330, 354), (314, 333)], fill=(99, 57, 28),
                 outline=(247, 192, 104), width=3)
    trim.polygon([(330, 320), (338, 333), (330, 346), (322, 333)], fill=(122, 207, 196))

    enamel = Image.new("L", atlas.size)
    ImageDraw.Draw(enamel).polygon([(x * scale, y * scale) for x, y in
                                   [(426, 249), (472, 249), (464, 272), (455, 285),
                                    (465, 308), (452, 316), (433, 304), (440, 282)]], fill=255)
    dye(enamel, [10, 27, 30], [76, 141, 133], 182)

    # The spear blade occupies a narrow island alongside the shaft.
    blade = Image.new("L", atlas.size)
    ImageDraw.Draw(blade).polygon([(x * scale, y * scale) for x, y in
                                  [(462, 112), (475, 125), (482, 166), (481, 199),
                                   (470, 219), (450, 217), (446, 182), (449, 141)]], fill=255)
    dye(blade, [31, 37, 39], [190, 221, 213], 222)
    result = Image.alpha_composite(Image.fromarray(pixels), details)
    result.putalpha(atlas.getchannel("A"))
    dds.write_argb(target, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="directory containing amazon0–4.skm and amazon.dds")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for level in range(5):
        rework_mesh(args.source / f"amazon{level}.skm", args.output / f"bsamazon{level}.skm", level == 0)
    rework_texture(args.source / "amazon.dds", args.output / "bsamazon.dds")
    (args.output / "bsamazon.lskm").write_text(
        'LSKM = { "bsamazon", "bsamazon.dds", { "Amazon", { 0 } } }\n', encoding="ascii")


if __name__ == "__main__":
    main()
