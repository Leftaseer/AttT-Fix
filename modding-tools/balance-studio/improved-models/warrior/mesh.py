"""Refine the starting hero's body, face and animated hair in the stock SKM rig."""

import argparse
from pathlib import Path

import numpy as np
import pn
import skm


def smoothstep(low, high, value):
    t = np.clip((value - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


def welded_average(values, groups):
    result = np.zeros((int(groups.max()) + 1, values.shape[1]))
    np.add.at(result, groups, values)
    return result / np.bincount(groups)[:, None]


def soften_body(mesh):
    points = mesh["P"]
    groups = pn.weld(points)
    welded = welded_average(points, groups)
    faces = groups[mesh["idx"].reshape(-1, 3)]
    edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges = np.unique(np.concatenate((edges, edges[:, ::-1])), axis=0)
    edges = edges[edges[:, 0] != edges[:, 1]]
    src, dst = edges.T
    counts = np.bincount(src, minlength=len(welded))

    # Use spatial masks on the welded surface so the face, torso and neck
    # stay connected across texture seams. Leave eye and nose landmarks firm.
    x, y, z = welded.T
    mid = 0.025
    face = smoothstep(3.30, 3.53, y) * (1 - smoothstep(3.77, 3.96, y))
    face *= 1 - smoothstep(-0.12, 0.13, z)
    nose = (1 - smoothstep(0.035, 0.078, np.abs(x - mid))) * (1 - smoothstep(-0.25, -0.19, z))
    eyes = smoothstep(3.68, 3.73, y) * (1 - smoothstep(3.77, 3.82, y))
    face *= (1 - .8 * nose) * (1 - .84 * eyes)
    torso = smoothstep(2.30, 2.52, y) * (1 - smoothstep(3.26, 3.43, y))
    torso *= 1 - smoothstep(.45, .68, np.abs(x - mid))
    shoulder = np.exp(-((np.abs(x - mid) - .46) / .22) ** 2 - ((y - 3.22) / .20) ** 2)
    intensity = np.maximum(.85 * face, .59 * torso + .34 * shoulder)
    for amount in (.49, -.45, .35):
        neighbors = np.zeros_like(welded)
        np.add.at(neighbors, src, welded[dst])
        delta = neighbors / np.maximum(counts[:, None], 1) - welded
        delta[counts == 0] = 0
        welded += delta * (intensity * amount)[:, None]

    # Shape the lower jaw and soften the squared edge into the chin.
    jaw = np.exp(-((y - 3.48) / .13) ** 2 - ((z + .135) / .125) ** 2)
    jaw *= smoothstep(.07, .16, np.abs(x - mid))
    welded[:, 0] -= .028 * jaw * np.sign(x - mid)
    welded[:, 1] += .012 * jaw
    chin = np.exp(-((y - 3.508) / .060) ** 2 - ((z + .228) / .041) ** 2)
    chin *= 1 - smoothstep(.08, .17, np.abs(x - mid))
    welded[:, 2] += .017 * chin
    welded[:, 1] += .012 * chin * smoothstep(.02, .10, np.abs(x - mid))

    # Give the mid-face a slightly rounder cheek contour without shifting the eyes.
    cheek = np.exp(-((np.abs(x - mid) - .12) / .049) ** 2
                   - ((y - 3.625) / .074) ** 2 - ((z + .15) / .104) ** 2)
    welded[:, 2] -= .012 * cheek
    delta = welded - welded_average(points, groups)
    mesh["P"] = points + delta[groups]

    # Blend the authored normals toward the rounded surface where it changed.
    corners = welded[faces]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    accum = np.zeros_like(welded)
    for k in range(3):
        np.add.at(accum, faces[:, k], normals)
    norm = accum[groups]
    norm /= np.maximum(np.linalg.norm(norm, axis=1, keepdims=True), 1e-12)
    stock = mesh["N"]
    amount = .45 * intensity[groups] * np.clip((np.sum(stock * norm, axis=1) - .35) / .45, 0, 1)
    blended = stock + (norm - stock) * amount[:, None]
    mesh["N"] = blended / np.maximum(np.linalg.norm(blended, axis=1, keepdims=True), 1e-12)


def fit_material_offsets(mesh):
    # Material offsets are 16-bit. Keep the face and its eye layers in their
    # authored order and place the largest triangle range last if needed.
    materials = mesh["mats"]
    if materials[-1]["start"] <= 65535:
        return
    starts = [mat["start"] for mat in materials] + [len(mesh["idx"])]
    sizes = np.diff(starts)
    largest = int(np.argmax(sizes))
    order = [i for i in range(len(materials)) if i != largest] + [largest]
    mesh["idx"] = np.concatenate([mesh["idx"][starts[i]:starts[i + 1]] for i in order])
    offset = 0
    mesh["mats"] = []
    for i in order:
        if offset > 65535:
            raise ValueError("Refined material range exceeds the SKM offset limit")
        mesh["mats"].append(dict(materials[i], start=offset))
        offset += int(sizes[i])


def rework(source, output, level):
    stock = source.read_bytes()
    mesh = skm.read(stock)
    if skm.write(mesh) != stock:
        raise ValueError(f"SKM round trip failed for {source}")
    if [part["name"] for part in mesh["skin"]] != [b"0Warrior", b"1Hair"]:
        raise ValueError(f"Unexpected skin tracks in {source}")
    counts = [len(part["idx"]) // 3 for part in mesh["skin"]]
    for index, part in enumerate(mesh["skin"]):
        if level < 3:
            detail = pn.refine(skm.unpack_skin(part), level=2)
            if index == 0:
                soften_body(detail)
                fit_material_offsets(detail)
            # The hair track has three bones. pack_skin expects four slots.
            padding = 4 - detail["bw"].shape[1]
            if padding:
                for key in ["bw", "bi"]:
                    detail[key] = np.pad(detail[key], ((0, 0), (0, padding)))
            part = skm.pack_skin(detail)
            mesh["skin"][index] = part
        for mat in part["mats"]:
            replacements = {b"warrior.dds": b"warriorhd.dds", b"warriorhead.dds": b"warriorheadhd.dds"}
            mat["tex"] = replacements[mat["tex"].lower()]
    result = skm.write(mesh)
    checked = skm.read(result)
    original = skm.read(stock)
    assert all(a["tail"] == b["tail"] and a["bones"].shape == b["bones"].shape
               for a, b in zip(original["skin"], checked["skin"]))
    assert checked["tail"] == original["tail"] and checked["rest"] == original["rest"]
    output.write_bytes(result)
    print(f"{output.name}: {counts} -> {[len(part['idx']) // 3 for part in mesh['skin']]} body and hair triangles")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for stem in ["warrior", "warriorappearance"]:
        for level in range(5):
            name = f"{stem}{level}.skm"
            rework(args.source / name, args.output / name, level)


if __name__ == "__main__":
    main()
