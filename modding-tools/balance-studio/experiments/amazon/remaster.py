"""Build a higher-detail Amazon that follows the stock art and animation rig."""

import argparse
from io import BytesIO
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import dds
import pn
import skm


def normalize(vectors):
    return vectors / np.maximum(np.linalg.norm(vectors, axis=-1, keepdims=True), 1e-12)


def make_rigid(part, positions, normals, uv, indices, starts):
    vertices = np.empty(len(positions), skm.V32)
    vertices["p"] = positions
    vertices["n"] = normals
    vertices["uv"] = uv
    return dict(part, v=vertices, idx=np.asarray(indices, dtype="<u2"),
                mats=[dict(material, start=start) for material, start in zip(part["mats"], starts)])


# Atlas coordinates for the existing pauldron's center ridge and two embossed fields.
PAULDRON_RIDGE = [(443.5, 246), (449.5, 254), (454, 265), (451, 277), (443.5, 285),
                  (436.5, 277), (433, 265), (437.5, 254), (443.5, 246)]
PAULDRON_RIVETS = [(443.5, 238), (421, 251), (466, 251), (427, 280), (460, 280),
                   (433, 304), (455, 304), (444, 317)]


def refine_shoulder(part, steps):
    v = part["v"]
    mesh = dict(P=v["p"].astype(float), N=v["n"].astype(float), UV=v["uv"].astype(float),
                bi=np.zeros((len(v), 4), dtype=int), bw=np.tile([1., 0., 0., 0.], (len(v), 1)),
                nbones=1, idx=part["idx"], mats=part["mats"])
    detail = pn.refine(mesh, level=steps)
    # Raise the ridge and stamped fields from the underlying curved metal.
    x, y = (detail["UV"] * 512).T
    ridge = np.exp(-((x - 443.5) / 4) ** 2 - ((y - 263) / 19) ** 2) * .014
    boss = np.exp(-((x - 443.5) / 9) ** 2 - ((y - 299) / 6) ** 2) * .011
    welded = pn.weld(detail["P"])
    offset = np.zeros((int(welded.max()) + 1, 3))
    np.add.at(offset, welded, detail["N"] * (ridge + boss)[:, None])
    detail["P"] += (offset / np.bincount(welded)[:, None])[welded]
    return make_rigid(part, detail["P"], detail["N"], detail["UV"], detail["idx"],
                      [material["start"] for material in detail["mats"]])


def rebuild_spear(part, detailed):
    # Original bounds and grip axis in the spear's animated local coordinates.
    tip = 2.62158
    bottom = -2.24428
    segments = 12 if detailed else 8
    positions, normals, uv, indices = [], [], [], []

    def surface(rings, sides):
        start = len(positions)
        points = np.array([point for ring in rings for point, _ in ring])
        positions.extend(points)
        uv.extend(np.asarray([texel for ring in rings for _, texel in ring]) / 512)
        faces = []
        for row in range(len(rings) - 1):
            for side in range(sides):
                a = row * (sides + 1) + side
                b = a + sides + 1
                if not np.allclose(points[a], points[a + 1]):
                    faces.append((a, a + 1, b))
                if not np.allclose(points[b], points[b + 1]):
                    faces.append((a + 1, b + 1, b))
        faces = np.asarray(faces)
        indices.extend((faces + start).ravel().tolist())

        # Weld the cylindrical seam for lighting, including the two pole vertices.
        welded = pn.weld(points)
        normal = np.zeros((int(welded.max()) + 1, 3))
        p, q, r = (points[faces[:, axis]] for axis in range(3))
        cross = np.cross(q - p, r - p)
        for axis in range(3):
            np.add.at(normal, welded[faces[:, axis]], cross)
        normals.extend(normalize(normal[welded]))

    # Beveled spearhead with its raised central ridge and original leaf profile.
    section = [(1, 0), (.72, .44), (0, 1), (-.72, .44), (-1, 0),
               (-.72, -.44), (0, -1), (.72, -.44), (1, 0)]
    blade = [(1.46, .025, .028, 215, 3), (1.62, .081, .043, 199, 10.4),
             (2.01, .060, .029, 164, 8.7), (2.44, .032, .012, 132, 4.9),
             (tip, 0, 0, 113, 0)]
    if detailed:
        blade.insert(2, (1.78, .073, .039, 185, 9.7))
        blade.insert(-1, (2.54, .017, .007, 123, 2.8))
    surface([[((x * width, y * depth, z), (465.4 - x * span, v)) for x, y in section]
             for z, width, depth, v, span in blade], 8)
    shaft_start = len(indices)

    # Round shaft with rings at the brass socket and heel.
    ring_positions = [(bottom, 0), (-2.208, .035), (-2.171, .040), (-2.13, .038),
                      (1.40, .039), (1.427, .043), (1.525, .043), (1.578, .037), (1.585, 0)]
    angles = np.linspace(0, 2 * np.pi, segments + 1)
    surface([[((radius * np.cos(angle), radius * np.sin(angle), z),
               (489.4 + 21 * side / segments, np.interp(z, [bottom, -2.207, 1.578], [407, 402, 43])))
              for side, angle in enumerate(angles)] for z, radius in ring_positions], segments)
    return make_rigid(part, positions, normals, uv, indices, [0, shaft_start])


def refine_body(part):
    body = pn.refine(skm.unpack_skin(part), level=2)

    # Bring some of the wrap, leather and metal shaping into the mesh. Average
    # displacements at coincident vertices so UV seams stay joined in motion.
    u, v = (body["UV"] * 512).T
    belts = (u < 327) & (v > 274) & (v < 336)
    boots = (u > 340) & (u < 487) & (v > 322) & (v < 443)
    relief = np.where(belts, 0.0025 * np.cos(v * 1.7 + u * .1), 0)
    relief += np.where(boots, 0.0020 * np.cos(v * 1.25), 0)
    welded = pn.weld(body["P"])
    displacement = np.zeros((int(welded.max()) + 1, 3))
    np.add.at(displacement, welded, body["N"] * relief[:, None])
    body["P"] += (displacement / np.bincount(welded)[:, None])[welded]
    return skm.pack_skin(body)


def remaster_mesh(source, output, level, texture):
    stock = source.read_bytes()
    mesh = skm.read(stock)
    body, = mesh["skin"]
    shoulder, spear = mesh["rigid"]
    if [body["name"], shoulder["name"], spear["name"]] != [b"0Amazon", b"1Naplecnik", b"2Spear"]:
        raise ValueError(f"Unexpected object layout in {source}")
    if level < 2:
        body = refine_body(body)
    if level < 3:
        shoulder = refine_shoulder(shoulder, 3 if level == 0 else 2)
        spear = rebuild_spear(spear, detailed=level == 0)
    mesh["skin"] = [body]
    mesh["rigid"] = [shoulder, spear]
    for part in [body, shoulder, spear]:
        for material in part["mats"]:
            if material["tex"].lower() != b"amazon.dds":
                raise ValueError(f"Unexpected texture in {source}")
            material["tex"] = texture
    output.write_bytes(skm.write(mesh))
    rebuilt = skm.read(output.read_bytes())
    original = skm.read(stock)
    assert rebuilt["skin"][0]["bones"].shape == original["skin"][0]["bones"].shape
    assert [part["bone"] for part in rebuilt["rigid"]] == [part["bone"] for part in original["rigid"]]
    assert rebuilt["tail"] == original["tail"] and rebuilt["rest"] == original["rest"]
    print(f"{output.name}: {sum(len(part['idx']) // 3 for part in [body, shoulder, spear])} triangles")


def material_mask(size, outlines):
    mask = Image.new("L", (size, size))
    draw = ImageDraw.Draw(mask)
    for outline in outlines:
        draw.polygon([(x * size / 512, y * size / 512) for x, y in outline], fill=255)
    return np.asarray(mask.filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255


def engrave_metal(atlas):
    # Repaint the stamped brass detail while leaving the stock patina underneath.
    marks = Image.new("RGBA", atlas.size)
    draw = ImageDraw.Draw(marks)
    scale = atlas.width / 512

    def line(points, shade, width):
        draw.line([(x * scale, y * scale) for x, y in points], fill=shade,
                  width=round(width * scale), joint="curve")

    def chase(points):
        line(points, (35, 23, 13, 205), 1.7)
        line([(x - .4, y - .45) for x, y in points], (229, 188, 111, 198), .65)

    chase(PAULDRON_RIDGE)
    chase([(443.5, 251), (443.5, 281)])
    for y in (257, 263, 269, 275):
        span = 5.5 if y in (263, 269) else 4
        chase([(443.5 - span, y + 3), (443.5, y), (443.5 + span, y + 3)])
    chase([(429, 298), (436, 291), (443.5, 297), (451, 291), (458, 298), (451, 307),
           (443.5, 311), (436, 307), (429, 298)])
    for x, y in PAULDRON_RIVETS:
        draw.ellipse(tuple(v * scale for v in (x - 1.7, y - 1.7, x + 1.7, y + 1.7)),
                     fill=(139, 97, 51, 242), outline=(43, 28, 17, 230), width=2)
        draw.ellipse(tuple(v * scale for v in (x - 1.0, y - 1.1, x + .1, y)),
                     fill=(248, 218, 151, 234))

    # Add narrow chased lines to the blade's center ridge.
    line([(465.4, 122), (465.4, 202)], (228, 219, 178, 150), .55)
    line([(466.1, 133), (466.1, 201)], (55, 43, 30, 128), .6)
    result = Image.alpha_composite(atlas, marks)
    result.putalpha(atlas.getchannel("A"))
    return result


def remaster_texture(source, output):
    stock = Image.open(source).convert("RGBA")
    if stock.size != (512, 512):
        raise ValueError("Expected the stock 512×512 Amazon atlas")
    size = 2048
    atlas = stock.resize((size, size), Image.Resampling.LANCZOS)
    pixels = np.asarray(atlas, dtype=np.float32)
    rgb = pixels[:, :, :3].copy()
    luminance = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
    light = np.clip((luminance - 12) / 42, 0, 1)
    sharpened = np.asarray(atlas.filter(ImageFilter.UnsharpMask(radius=3, percent=105, threshold=3)),
                           dtype=np.float32)[:, :, :3]
    rgb += np.clip(sharpened - rgb, -14, 14) * .65

    y, x = np.ogrid[:size, :size]
    x, y = x.astype(np.float32), y.astype(np.float32)
    rng = np.random.default_rng(50)
    grain = rng.standard_normal((size, size), dtype=np.float32)
    leather = material_mask(size, [
        [(344, 325), (375, 301), (429, 313), (426, 371), (344, 373)],
        [(438, 324), (486, 322), (484, 391), (479, 443), (430, 444)],
        [(12, 279), (132, 283), (132, 337), (3, 337)],
        [(199, 272), (327, 272), (326, 338), (195, 330)],
    ])
    woven = np.sin(x * 0.78 + y * 0.46) * np.sin(y * .92 - x * .21)
    hide = (grain * 2.2 + woven * 3.2 + np.sin(x * .31 + y * .17) * 2)
    rgb += (leather * np.clip((165 - luminance) / 70, 0, 1) * light * hide)[:, :, None]

    metal = material_mask(size, [
        [(403, 240), (479, 240), (469, 269), (487, 303), (466, 324), (422, 324), (418, 293)],
        [(425, 445), (474, 445), (475, 510), (423, 510)],
        [(450, 153), (463, 113), (480, 152), (485, 200), (473, 225), (449, 216)],
        [(489, 44), (511, 44), (511, 405), (489, 405)],
    ])
    brushed = np.sin(x * 1.85 + y * .09) * 2.1 + grain * 1.6
    rgb += (metal * light * brushed)[:, :, None]
    hair = material_mask(size, [[(264, 371), (423, 370), (426, 506), (263, 505)]])
    strands = np.sin((x + .0011 * (y - 1720) ** 2) * 1.8 + np.sin(y * .031) * 1.7)
    rgb += (hair * light * strands * 3.8)[:, :, None]
    rgb += (light * grain * 0.48)[:, :, None]
    pixels[:, :, :3] = np.clip(np.rint(rgb), 0, 255)
    write_dds(output, engrave_metal(Image.fromarray(np.uint8(pixels))))


def write_dds(output, atlas):
    # Keep the full mip chain in a D3D9-compatible format at 5.3 MiB.
    levels = dds.mips(atlas)
    chunks = []
    for image in levels:
        buffer = BytesIO()
        image.save(buffer, format="DDS", pixel_format="DXT5")
        chunks.append(buffer.getvalue())
    header = bytearray(chunks[0][:128])
    flags, = struct.unpack_from("<I", header, 8)
    struct.pack_into("<I", header, 8, flags | 0x20000)
    struct.pack_into("<I", header, 28, len(levels))
    caps, = struct.unpack_from("<I", header, 108)
    struct.pack_into("<I", header, 108, caps | 0x400008)
    output.write_bytes(bytes(header) + b"".join(chunk[128:] for chunk in chunks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="directory containing amazon0–4.skm and amazon.dds")
    parser.add_argument("output", type=Path)
    parser.add_argument("--shared-texture", type=Path, help="DDS for a replacement under the stock shared names")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    stem = "amazon" if args.shared_texture else "bsamazon"
    texture = f"{stem}.dds"
    for level in range(5):
        remaster_mesh(args.source / f"amazon{level}.skm", args.output / f"{stem}{level}.skm",
                      level, texture.encode("ascii"))
    if args.shared_texture:
        (args.output / texture).write_bytes(args.shared_texture.read_bytes())
        return
    remaster_texture(args.source / "amazon.dds", args.output / texture)
    (args.output / "bsamazon.lskm").write_text(
        'LSKM = { "bsamazon", "bsamazon.dds", { "Amazon", { 0 } } }\n', encoding="ascii")


if __name__ == "__main__":
    main()
