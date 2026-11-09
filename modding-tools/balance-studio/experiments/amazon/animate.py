"""Polish the shared Amazon and Helga animations at their existing frame counts."""

import argparse
from pathlib import Path
import struct

import numpy as np

from pose import ypr
import ska


CLIPS = {
    "amazonwait.ska": (101, (0, 99, 100)),
    "amazonwaitbattle.ska": (111, (0, 109, 110)),
    "amazonrun.ska": (48, (0, 7, 23, 47)),
}


def nearest_angles(matrices, reference):
    pitch = np.arcsin(np.clip(-matrices[..., 2, 1], -1, 1))
    yaw = np.arctan2(matrices[..., 2, 0], matrices[..., 2, 2])
    roll = np.arctan2(matrices[..., 0, 1], matrices[..., 1, 1])
    locked = np.abs(np.cos(pitch)) < 1e-7
    yaw = np.where(locked, np.arctan2(-matrices[..., 0, 2], matrices[..., 0, 0]), yaw)
    roll = np.where(locked, 0, roll)
    primary = np.stack((pitch, yaw, roll), axis=-1)
    alternate = np.stack((np.pi - pitch, yaw + np.pi, roll + np.pi), axis=-1)
    primary += 2 * np.pi * np.round((reference - primary) / (2 * np.pi))
    alternate += 2 * np.pi * np.round((reference - alternate) / (2 * np.pi))
    use_alternate = np.sum((alternate - reference) ** 2, axis=-1) < np.sum((primary - reference) ** 2, axis=-1)
    return np.where(use_alternate[..., None], alternate, primary)


def rotation_projection(matrices):
    left, _, right = np.linalg.svd(matrices)
    left[..., :, 2] *= np.linalg.det(left @ right)[..., None]
    return left @ right


def smooth_motion(tracks, active):
    body, shoulder, spear = tracks
    rotation, translation = ypr(body.astype(float))
    frames = np.arange(len(body))[:, None] + np.arange(-2, 3)
    frames = np.clip(frames, 0, len(body) - 1)
    weights = np.array([1, 4, 6, 4, 1], dtype=float) / 16

    def average(values):
        return np.einsum("k,fk...->f...", weights, values[frames])

    mix = active[:, None, None]
    moved = translation + (average(translation) - translation) * mix
    turned = rotation_projection(rotation + (average(rotation) - rotation) * mix[..., None])
    body_out = np.concatenate((nearest_angles(turned, body[..., :3]), moved), axis=-1)

    equipment = []
    for track, bone in [(shoulder, 14), (spear, 36)]:
        # Carry the original offset through the new parent pose. Rigid SKA
        # transforms use the opposite translation sign to skinned bones.
        old_r, old_t = ypr(track.astype(float))
        delta = rotation[:, bone].transpose(0, 2, 1) @ turned[:, bone]
        new_r = old_r @ delta[:, None]
        new_t = ((old_t + translation[:, bone, None])[:, :, None, :] @ delta[:, None])[:, :, 0]
        new_t -= moved[:, bone, None]
        equipment.append(np.concatenate((nearest_angles(new_r, track[..., :3]), new_t), axis=-1))

    return [body_out, *equipment]


def idle_glance(tracks):
    body, shoulder, spear = tracks
    rotation, translation = ypr(body.astype(float))
    neck, head = 7, 8
    # Find the fixed joint shared by the neck and head transforms in bind space.
    system = (rotation[:, neck] - rotation[:, head]).transpose(0, 2, 1).reshape(-1, 3)
    relative = (translation[:, head] - translation[:, neck]).ravel()
    joint, _, rank, _ = np.linalg.lstsq(system, relative, rcond=None)
    if rank != 3 or np.max(np.abs(system @ joint - relative)) > 0.001:
        raise ValueError("Could not identify the stock Amazon neck joint")
    pivot = joint @ rotation[:, head] + translation[:, head]
    phase = np.linspace(0, 2 * np.pi, len(body))
    offsets = np.zeros((len(body), 6))
    offsets[:, 1] = np.radians(15) * np.sin(phase) * np.sin(phase / 2) ** 2
    offsets[:, 2] = np.radians(4) * np.sin(phase / 2) ** 2
    offset, _ = ypr(offsets)
    revised = body.copy()
    revised[:, head, :3] = nearest_angles(rotation[:, head] @ offset, body[:, head, :3])
    revised[:, head, 3:] = ((translation[:, head] - pivot)[:, None, :] @ offset)[:, 0] + pivot
    return [revised, shoulder, spear]


def build_clip(data, name):
    frames, pins = CLIPS[name]
    original = data["objs"]
    if [keys.shape for keys in original] != [(frames, 60, 6), (frames, 1, 6), (frames, 1, 6)]:
        raise ValueError(f"Unexpected Amazon animation layout in {name}")

    if name == "amazonwait.ska":
        edited = idle_glance(original)
    else:
        distance = np.min(np.abs(np.arange(frames)[:, None] - pins), axis=1)
        ramp = np.clip(distance / 3, 0, 1)
        edited = smooth_motion(original, ramp * ramp * (3 - 2 * ramp) * 0.9)

    chunks = [struct.pack("<IB", len(original), data["flag"])]
    for before, after in zip(original, edited):
        after = np.asarray(after, dtype="<f4").copy()
        after[list(pins)] = before[list(pins)]
        if not np.isfinite(after).all():
            raise ValueError(f"Invalid animation key in {name}")
        chunks.extend([struct.pack("<II", after.shape[1], frames), after.tobytes()])
    return b"".join(chunks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="directory containing stock Amazon SKA files")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in CLIPS:
        (args.output / name).write_bytes(build_clip(ska.read((args.source / name).read_bytes()), name))


if __name__ == "__main__":
    main()
