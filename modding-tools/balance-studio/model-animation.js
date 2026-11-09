/* Existing SKA clip round trips through a sampled, animated rig template. */
(function (root) {
  "use strict";

  const models = typeof module === "undefined" ? root.BalanceModels : require("./models.js");
  const rig = typeof module === "undefined" ? root.BalanceRig : require("./model-rig.js");
  const { readGlb, gltfMatrix, inverseJoint, multiply, nodeMatrix } = rig;
  const fps = 30;
  const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

  function check(condition, message) {
    if (!condition) throw new Error(message);
  }

  function matrixAt(track, frame, bone, rigid) {
    const offset = ((frame < track.frames ? frame : 0) * track.bones + bone) * 6;
    const matrix = models.rotation(track.keys, offset);
    return gltfMatrix(rigid ? matrix.map((value) => -value) : matrix);
  }

  function unitQuaternion(q) {
    const length = Math.hypot(...q);
    check(length > 0 && Number.isFinite(length), "The GLB has an invalid bone rotation.");
    return q.map((value) => value / length);
  }

  function quaternion(m) {
    const trace = m[0] + m[5] + m[10];
    if (trace > 0) {
      const s = 2 * Math.sqrt(1 + trace);
      return unitQuaternion([(m[6] - m[9]) / s, (m[8] - m[2]) / s, (m[1] - m[4]) / s, s / 4]);
    }
    if (m[0] >= m[5] && m[0] >= m[10]) {
      const s = 2 * Math.sqrt(1 + m[0] - m[5] - m[10]);
      return unitQuaternion([s / 4, (m[4] + m[1]) / s, (m[8] + m[2]) / s, (m[6] - m[9]) / s]);
    }
    if (m[5] >= m[10]) {
      const s = 2 * Math.sqrt(1 + m[5] - m[0] - m[10]);
      return unitQuaternion([(m[4] + m[1]) / s, s / 4, (m[9] + m[6]) / s, (m[8] - m[2]) / s]);
    }
    const s = 2 * Math.sqrt(1 + m[10] - m[0] - m[5]);
    return unitQuaternion([(m[8] + m[2]) / s, (m[9] + m[6]) / s, s / 4, (m[1] - m[4]) / s]);
  }

  const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0);
  const trs = (matrix) => ({ translation: matrix.slice(12, 15), rotation: quaternion(matrix) });

  function exportClip(reference, override) {
    const tracks = override ? models.readMotion(override) : reference.tracks;
    const count = reference.scene.frameCount;
    check(count >= 2, "This clip has fewer than two frames.");
    const times = Float32Array.from({ length: count }, (_, frame) => frame / fps);
    const parts = new Map();
    for (const [slot, binding] of reference.bindings) {
      const part = reference.parts[slot], stock = reference.tracks[part.trackIndex], track = tracks[part.trackIndex];
      const rigid = Boolean(part.vertices);
      const rest = rigid ? [identity] : binding.joints;
      const joints = rest.map((matrix, bone) => {
        const parent = binding.parents?.[bone] ?? -1;
        const local = parent < 0 ? matrix : multiply(inverseJoint(rest[parent]), matrix);
        return { rest: trs(local), translations: new Float32Array(count * 3), rotations: new Float32Array(count * 4) };
      });
      const fromStock = rest.map((matrix, bone) => multiply(inverseJoint(matrixAt(stock, 0, bone, rigid)), matrix));
      for (let frame = 0; frame < count; frame++) {
        // SKA keys are absolute. Bake local glTF transforms for the editable hierarchy.
        const world = rest.map((_, bone) => multiply(matrixAt(track, frame, bone, rigid), fromStock[bone]));
        for (const [bone, channel] of joints.entries()) {
          const parent = binding.parents?.[bone] ?? -1;
          const local = parent < 0 ? world[bone] : multiply(inverseJoint(world[parent]), world[bone]);
          const { translation, rotation } = trs(local);
          if (frame && dot(rotation, channel.rotations.subarray((frame - 1) * 4, frame * 4)) < 0) {
            for (let i = 0; i < 4; i++) rotation[i] *= -1;
          }
          channel.translations.set(translation, frame * 3);
          channel.rotations.set(rotation, frame * 4);
        }
      }
      parts.set(slot, joints);
    }
    return { name: reference.motion.replace(/\.ska$/, ""), times, parts, fps };
  }

  function sample(curve, time) {
    const { times, values, width, mode, rotation } = curve;
    let low = 0, high = times.length - 1;
    while (high - low > 1) {
      const mid = (low + high) >> 1;
      if (times[mid] > time) high = mid;
      else low = mid;
    }
    if (time >= times[high] - 1e-6) low = high;
    const a = Array.from(values.subarray(low * width, (low + 1) * width));
    if (mode === "STEP" || time <= times[low] || low === high) return rotation ? unitQuaternion(a) : a;
    const b = Array.from(values.subarray(high * width, (high + 1) * width));
    const t = Math.min(1, (time - times[low]) / (times[high] - times[low]));
    if (!rotation) return a.map((value, i) => value * (1 - t) + b[i] * t);
    const q0 = unitQuaternion(a), q1 = unitQuaternion(b);
    const cosine = dot(q0, q1);
    if (cosine < 0) for (let i = 0; i < 4; i++) q1[i] *= -1;
    const angle = Math.acos(Math.min(1, Math.abs(cosine)));
    if (angle < 1e-4) return unitQuaternion(q0.map((value, i) => value * (1 - t) + q1[i] * t));
    return q0.map((value, i) => (value * Math.sin((1 - t) * angle) + q1[i] * Math.sin(t * angle)) / Math.sin(angle));
  }

  function curvesOf(doc, read, duration) {
    const curves = new Map();
    let last = 0;
    for (const clip of doc.animations ?? []) {
      for (const channel of clip.channels ?? []) {
        const { node, path } = channel.target ?? {};
        const sampler = clip.samplers?.[channel.sampler];
        check(doc.nodes[node] && ["translation", "rotation", "scale"].includes(path) && sampler,
          "The GLB contains an unsupported animation channel.");
        const mode = sampler.interpolation ?? "LINEAR";
        check(mode === "LINEAR" || mode === "STEP", "Bake the animation to linear keyframes before exporting.");
        const times = read(sampler.input, "SCALAR", [5126]);
        const rotation = path === "rotation", width = rotation ? 4 : 3;
        const values = read(sampler.output, rotation ? "VEC4" : "VEC3", [5126]);
        check(values.length === times.length * width && times[0] >= -1e-5 &&
          times.every((time, i) => i === 0 || time > times[i - 1]), "The GLB animation has invalid key times.");
        if (!curves.has(node)) curves.set(node, new Map());
        const target = curves.get(node);
        check(!target.has(path), "Export one Blender scene animation with all body and equipment tracks.");
        target.set(path, { times, values, width, mode, rotation });
        last = Math.max(last, times.at(-1));
      }
    }
    check(curves.size, "This GLB contains no animation. Export the active Blender scene animation.");
    check(Math.abs(last - duration) < 0.5 / fps, "Keep the template’s original animation frame range and 30 FPS.");
    return curves;
  }

  function animationTargets(doc, read, reference) {
    const tagged = new Map();
    for (const [id, node] of doc.nodes.entries()) {
      if (node.mesh === undefined) continue;
      for (const name of [node.name, doc.meshes?.[node.mesh]?.name]) {
        const tag = typeof name === "string" ? name.split("__")[0] : "";
        if (!tagged.has(tag)) tagged.set(tag, id);
      }
    }
    const targets = [];
    for (const [slot, binding] of reference.bindings) {
      const part = reference.parts[slot], track = reference.tracks[part.trackIndex];
      const node = tagged.get(binding.tag);
      check(node !== undefined, "Use the animated template for this mesh, clip and detail level. Keep the tagged object names.");
      if (part.vertices) {
        targets.push({ node, track, bone: 0, rigid: true, factor: matrixAt(track, 0, 0, true) });
        continue;
      }
      const skin = doc.skins?.[doc.nodes[node].skin];
      check(Array.isArray(skin?.joints), "Export skinning with the original template bones.");
      const inverse = read(skin.inverseBindMatrices, "MAT4", [5126]);
      check(inverse.length === skin.joints.length * 16, "The GLB has mismatched inverse bind matrices.");
      const seen = new Set();
      for (const [i, joint] of skin.joints.entries()) {
        const name = doc.nodes[joint]?.name;
        if (rig.isNeutralBone(name)) continue;
        const match = /^att_b(\d+)(?:\.\d+)?$/.exec(name ?? "");
        const bone = match && Number(match[1]);
        check(match && bone < part.boneCount && !seen.has(bone), "The GLB does not contain the original template bone indices.");
        seen.add(bone);
        const factor = multiply(inverse.subarray(i * 16, (i + 1) * 16), matrixAt(track, 0, bone, false));
        targets.push({ node: joint, track, bone, rigid: false, factor });
      }
      check(seen.size === part.boneCount, "Export all template bones, including unused bones.");
    }
    return targets;
  }

  function parentsOf(nodes) {
    const parents = new Map();
    for (const [i, node] of nodes.entries()) {
      for (const child of node.children ?? []) {
        check(nodes[child] && !parents.has(child), "The GLB animation has an invalid node hierarchy.");
        parents.set(child, i);
      }
    }
    return parents;
  }

  function worldSampler(nodes, parents, curves, time) {
    const cache = new Map(), pending = new Set();
    return function world(id) {
      if (cache.has(id)) return cache.get(id);
      check(!pending.has(id) && pending.size < 256, "The GLB animation has an invalid node hierarchy.");
      pending.add(id);
      const node = nodes[id], curve = curves.get(id);
      const local = curve ? { ...node } : node;
      if (curve) {
        check(!node.matrix, "Animated GLB nodes must use translation, rotation and scale.");
        for (const [path, values] of curve) local[path] = sample(values, time);
      }
      const matrix = nodeMatrix(local);
      check(matrix.length === 16 && matrix.every(Number.isFinite), "The GLB animation has an invalid transform.");
      const absolute = parents.has(id) ? multiply(world(parents.get(id)), matrix) : matrix;
      cache.set(id, absolute);
      pending.delete(id);
      return absolute;
    };
  }

  function writeKeys(view, at, matrix, previous, rigid) {
    const m = [matrix[0], matrix[1], -matrix[2], matrix[4], matrix[5], -matrix[6],
      -matrix[8], -matrix[9], matrix[10], matrix[12], matrix[13], -matrix[14]];
    if (rigid) for (let i = 0; i < m.length; i++) m[i] *= -1;
    const [a, b, c] = [m.slice(0, 3), m.slice(3, 6), m.slice(6, 9)];
    const determinant = a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2]) +
      a[2] * (b[0] * c[1] - b[1] * c[0]);
    check(Math.abs(determinant - 1) < 0.001 && [a, b, c].every((axis) => Math.abs(dot(axis, axis) - 1) < 0.001) &&
      Math.abs(dot(a, b)) < 0.001 && Math.abs(dot(a, c)) < 0.001 && Math.abs(dot(b, c)) < 0.001 &&
      m.slice(9).every((value) => Number.isFinite(value) && Math.abs(value) < 10000),
    "SKA animation supports rotation and translation. Remove animated bone or object scaling.");
    const pitch = Math.asin(Math.max(-1, Math.min(1, -m[7])));
    const locked = Math.abs(Math.cos(pitch)) < 1e-5;
    const yaw = locked ? Math.atan2(-m[2], m[0]) : Math.atan2(m[6], m[8]);
    const roll = locked ? 0 : Math.atan2(m[1], m[4]);
    const period = Math.PI * 2;
    const nearest = (angles) => angles.map((angle, i) => angle + period * Math.round((previous[i] - angle) / period));
    const primary = nearest([pitch, yaw, roll]);
    const alternate = nearest([Math.PI - pitch, yaw + Math.PI, roll + Math.PI]);
    const error = (angles) => angles.reduce((sum, value, i) => sum + (value - previous[i]) ** 2, 0);
    const keys = [...(error(primary) <= error(alternate) ? primary : alternate), ...m.slice(9)];
    for (const [i, value] of keys.entries()) view.setFloat32(at + i * 4, value, true);
    return keys;
  }

  function importClip(reference, bytes) {
    const { doc, read } = readGlb(bytes);
    const count = reference.scene.frameCount;
    check(Array.isArray(doc.nodes) && doc.nodes.length <= 8192 && count >= 2, "Choose an animated rig template.");
    const curves = curvesOf(doc, read, (count - 1) / fps);
    const parents = parentsOf(doc.nodes);
    const targets = animationTargets(doc, read, reference);
    check(targets.some(({ node }) => {
      for (let id = node, depth = 0; id !== undefined && depth < 256; id = parents.get(id), depth++) {
        if (curves.has(id)) return true;
      }
      return false;
    }), "The GLB animation does not target the template’s bones or attachments.");

    const output = reference.motionBytes.slice();
    const view = new DataView(output.buffer, output.byteOffset, output.byteLength);
    const previous = new Map();
    for (let frame = 0; frame < count; frame++) {
      const world = worldSampler(doc.nodes, parents, curves, frame / fps);
      const written = new Map();
      for (const { node, track, bone, rigid, factor } of targets) {
        if (frame >= track.frames) continue;
        const i = (frame * track.bones + bone) * 6;
        const at = track.keyOffset + i * 4;
        const base = track.keyOffset + bone * 24;
        const matrix = multiply(world(node), factor);
        const other = written.get(at);
        if (other) {
          check(matrix.every((value, j) => Math.abs(value - other[j]) < 0.001), "Parts using the same game track have conflicting motion.");
          continue;
        }
        written.set(at, matrix);
        const stock = matrixAt(track, frame, bone, rigid);
        const angles = track.keys.subarray(i, i + 3);
        // Keep exact stock keys when Blender round-trips the frame within float precision.
        const keys = matrix.every((value, j) => Math.abs(value - stock[j]) < 0.00002) ? angles :
          writeKeys(view, at, matrix, previous.get(base) ?? angles, rigid);
        previous.set(base, keys);
      }
    }
    return output;
  }

  const api = { exportClip, importClip, fps };
  if (typeof module !== "undefined") module.exports = api;
  else root.BalanceAnimation = api;
})(globalThis);
