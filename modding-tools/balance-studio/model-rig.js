/* Round-trip GLB geometry through AttT's indexed SKM skin and attachment slots. */
(function (root) {
  "use strict";

  const models = typeof module === "undefined" ? root.BalanceModels : require("./models.js");
  const { transferFrom } = typeof module === "undefined" ? root.BalanceSkinTransfer : require("./model-skin-transfer.js");
  const isNeutralBone = (name) => /^neutral_bone(?:\.\d+)?$/.test(name ?? "");

  function check(condition, message) {
    if (!condition) throw new Error(message);
  }

  function fingerprint(...chunks) {
    let hash = 2166136261;
    for (const chunk of chunks) for (const byte of chunk) hash = Math.imul(hash ^ byte, 16777619);
    return (hash >>> 0).toString(16).padStart(8, "0");
  }

  function boneMatrix(track, bone, rigid = false) {
    const matrix = models.rotation(track.keys, bone * 6);
    return rigid ? matrix.map((value) => -value) : matrix;
  }

  function gltfMatrix(m) {
    return [m[0], m[1], -m[2], 0, m[3], m[4], -m[5], 0, -m[6], -m[7], m[8], 0, m[9], m[10], -m[11], 1];
  }

  async function template(game, clip, lod, clips) {
    const scene = await models.loadModel(game, clip, lod);
    const [bytes, motion] = await Promise.all([game.readAsset(scene.mesh), game.readAsset(clip.motion)]);
    const parts = models.readModel(bytes);
    const tracks = models.readMotion(motion);
    const id = fingerprint(new TextEncoder().encode(scene.mesh + "|" + clip.motion), bytes, motion);
    const bindings = new Map();
    for (const posed of scene.parts) {
      const slot = posed.slot;
      const part = parts[slot], track = tracks[part.trackIndex];
      const binding = { tag: `AttT_${id}_p${slot}` };
      if (part.vertices) {
        binding.matrices = [boneMatrix(track, 0, true)];
      } else {
        binding.matrices = Array.from({ length: part.boneCount }, (_, bone) => boneMatrix(track, bone));
        binding.joints = binding.matrices.map(gltfMatrix);
        binding.bones = Uint16Array.from(part.copies, (copy) => part.bones[copy]);
        binding.weights = part.weights.slice();
        for (let at = 0; at < binding.weights.length; at += 4) {
          const sum = binding.weights[at] + binding.weights[at + 1] + binding.weights[at + 2] + binding.weights[at + 3];
          check(sum > 0, `Part ${part.name} has an unweighted vertex.`);
          for (let i = at; i < at + 4; i++) {
            binding.weights[i] /= sum;
            if (!binding.weights[i]) binding.bones[i] = 0;
          }
        }
      }
      bindings.set(slot, binding);
    }
    if (clips) {
      const names = [...new Set(clips.filter((entry) => entry.model === clip.model).map((entry) => entry.motion))]
        .filter((name) => name !== clip.motion).slice(0, 6);
      const samples = new Map();
      for (const part of scene.parts) {
        if (part.boneIds) samples.set(part.trackIndex, []);
      }
      addSamples(samples, tracks);
      for (const name of names) {
        try {
          const keys = await game.readAsset(name);
          if (keys) addSamples(samples, models.readMotion(keys));
        } catch {
          // The reference clip is enough for the bind pose. Extra clips refine the pivots.
        }
      }
      for (const part of scene.parts) {
        const binding = bindings.get(part.slot);
        binding.weld = weldGroups(part, binding);
        if (binding.joints) shapeArmature(part, binding, samples.get(part.trackIndex));
      }
    }
    return { scene, id, bindings, parts, bytes, motion: clip.motion, motionBytes: motion, tracks };
  }

  function weldGroups(part, binding) {
    const count = part.vertices.length / 8;
    const key = (value) => Math.round(value * 100000);
    const positions = [];
    for (let vertex = 0; vertex < count; vertex++) {
      const at = vertex * 8;
      const weights = [];
      if (binding.bones) {
        for (let j = vertex * 4; j < vertex * 4 + 4; j++) {
          if (binding.weights[j]) weights.push([binding.bones[j], key(binding.weights[j])]);
        }
        weights.sort(([a], [b]) => a - b);
      }
      positions.push([key(part.vertices[at]), key(part.vertices[at + 1]), key(part.vertices[at + 2]), ...weights].join(","));
    }
    const edges = new Map();
    for (let i = 0; i + 2 < part.indices.length; i += 3) {
      const [a, b, c] = part.indices.subarray(i, i + 3);
      for (const [from, to, opposite] of [[a, b, c], [b, c, a], [c, a, b]]) {
        const id = Math.min(from, to) * count + Math.max(from, to);
        edges.set(id, edges.has(id) ? null : { from, to, opposite });
      }
    }
    const seams = new Map();
    for (const edge of edges.values()) {
      if (!edge || positions[edge.from] === positions[edge.to]) continue;
      const id = [positions[edge.from], positions[edge.to]].sort().join("|");
      if (!seams.has(id)) seams.set(id, []);
      seams.get(id).push(edge);
    }
    const groups = Float32Array.from({ length: count }, (_, i) => i);
    function rootOf(i) {
      while (groups[i] !== i) {
        groups[i] = groups[groups[i]];
        i = groups[i];
      }
      return i;
    }
    for (const pair of seams.values()) {
      if (pair.length !== 2) continue;
      const [a, b] = pair;
      if (positions[a.from] !== positions[b.to] || positions[a.to] !== positions[b.from] ||
          positions[a.opposite] === positions[b.opposite]) continue;
      groups[rootOf(a.from)] = rootOf(b.to);
      groups[rootOf(a.to)] = rootOf(b.from);
    }
    return groups.map((_, i) => rootOf(i));
  }

  function addSamples(samples, tracks) {
    for (const [index, poses] of samples) {
      const track = tracks[index];
      if (!track?.frames) continue;
      const frames = Math.min(track.frames, 8);
      for (let i = 0; i < frames; i++) {
        const frame = Math.round(i * (track.frames - 1) / Math.max(1, frames - 1));
        poses.push(Array.from({ length: track.bones }, (_, bone) =>
          gltfMatrix(models.rotation(track.keys, (frame * track.bones + bone) * 6))));
      }
    }
  }

  function inverseJoint(joint) {
    const [a, b, c, , d, e, f, , g, h, i, , x, y, z] = joint;
    return [a, d, g, 0, b, e, h, 0, c, f, i, 0,
      -(a * x + b * y + c * z), -(d * x + e * y + f * z), -(g * x + h * y + i * z), 1];
  }

  function pivotEstimate(bone, parent, center, limit, samples) {
    // A joint pivot moves to the same point under the parent and child skin transforms.
    const damping = 0.003 * samples.length;
    const system = [[damping, 0, 0, 0], [0, damping, 0, 0], [0, 0, damping, 0]];
    for (const pose of samples) {
      const a = pose[parent], b = pose[bone];
      for (let row = 0; row < 3; row++) {
        const equation = [a[row] - b[row], a[row + 4] - b[row + 4], a[row + 8] - b[row + 8]];
        const offset = b[row + 12] - a[row + 12] - equation.reduce((sum, value, i) => sum + value * center[i], 0);
        for (let i = 0; i < 3; i++) {
          for (let j = 0; j < 3; j++) system[i][j] += equation[i] * equation[j];
          system[i][3] += equation[i] * offset;
        }
      }
    }
    for (let i = 0; i < 3; i++) {
      const scale = system[i][i];
      if (scale < 1e-9) return center;
      for (let k = i; k < 4; k++) system[i][k] /= scale;
      for (let j = 0; j < 3; j++) {
        if (i === j) continue;
        const factor = system[j][i];
        for (let k = i; k < 4; k++) system[j][k] -= factor * system[i][k];
      }
    }
    const delta = system.map((row) => row[3]);
    return Math.hypot(...delta) <= limit ? center.map((value, i) => value + delta[i]) : center;
  }

  function handParents(centers, motion) {
    // A common humanoid layout stores a collar, upper arm, forearm and hand,
    // followed by five three-joint fingers. The other arm repeats that sequence.
    const fingers = 5, jointsPerFinger = 3, armLength = 4 + fingers * jointsPerFinger;
    const layouts = [...centers.keys()].filter((wrist) => {
      const start = wrist - 3;
      return Array.from({ length: armLength * 2 }, (_, i) => start + i).every((bone) => centers.has(bone));
    });
    if (!layouts.length) return new Map();

    function matches(points, wrist, other) {
      const distance = (a, b) => Math.hypot(...points.get(a).map((value, i) => value - points.get(b)[i]));
      const forearm = distance(wrist, wrist - 1);
      const upperArm = distance(wrist - 1, wrist - 2);
      if (!(forearm > 0 && forearm > upperArm * 0.35 && forearm < upperArm * 2.5) ||
          distance(wrist, other) < forearm || distance(wrist - 2, wrist - 3) > forearm * 1.5) return false;
      const segments = [];
      for (let i = 0; i < fingers; i++) {
        const root = wrist + 1 + i * jointsPerFinger;
        for (let joint = root; joint < root + jointsPerFinger; joint++) {
          if (distance(wrist, joint) > forearm * 1.4) return false;
          if (joint > root) segments.push(distance(joint, joint - 1));
        }
      }
      segments.sort((a, b) => a - b);
      return segments[Math.floor(segments.length / 2)] < forearm * 0.35;
    }

    const poses = [centers];
    // Recognize the layout in several poses so a clenched fist or crossed arms
    // in the chosen reference frame do not decide the hierarchy on their own.
    const stride = Math.max(1, Math.floor(motion.length / 12));
    for (let frame = 0; frame < motion.length; frame += stride) {
      const matrices = motion[frame];
      poses.push(new Map([...centers].map(([bone, [x, y, z]]) => {
        const matrix = matrices[bone];
        return [bone, [0, 1, 2].map((i) => x * matrix[i] + y * matrix[i + 4] + z * matrix[i + 8] + matrix[i + 12])];
      })));
    }
    const votes = new Map();
    for (const points of poses) {
      const plausible = layouts.filter((left) => matches(points, left, left + armLength) &&
        matches(points, left + armLength, left));
      if (plausible.length === 1) votes.set(plausible[0], (votes.get(plausible[0]) ?? 0) + 1);
    }
    const [[first, score] = [], [, nextScore] = []] = [...votes].sort(([, a], [, b]) => b - a);
    if (score === undefined || score < Math.min(2, poses.length) || (nextScore && score < nextScore * 2)) return new Map();

    const parents = new Map();
    for (const wrist of [first, first + armLength]) {
      for (let bone = wrist - 2; bone <= wrist; bone++) parents.set(bone, bone - 1);
      for (let i = 0; i < fingers; i++) {
        const root = wrist + 1 + i * jointsPerFinger;
        parents.set(root, wrist);
        for (let j = 1; j < jointsPerFinger; j++) parents.set(root + j, root + j - 1);
      }
    }
    return parents;
  }

  function shapeArmature(part, binding, samples) {
    const count = binding.joints.length;
    const centers = new Map(part.boneIds.map((bone, i) =>
      [bone, [part.markers[i * 3], part.markers[i * 3 + 1], -part.markers[i * 3 + 2]]]));
    if (!centers.size) return;
    const inverse = binding.joints.map(inverseJoint);
    const motion = samples.filter((pose) => pose.length >= count)
      .map((pose) => inverse.map((matrix, bone) => multiply(pose[bone], matrix)));
    const hands = handParents(centers, motion);
    const middle = [0, 1, 2].map((axis) =>
      [...centers.values()].reduce((total, point) => total + point[axis], 0) / centers.size);
    const vector = (a, b) => a.map((value, i) => value - b[i]);
    const distance = (a, b) => Math.hypot(...vector(a, b));
    const extent = Math.max(...[...centers.values()].map((point) => distance(point, middle)), 0.01);
    const adjacent = Array.from({ length: count }, () => []);
    const links = part.links();
    for (let i = 0; i < links.length; i += 2) {
      const a = part.boneIds[links[i]], b = part.boneIds[links[i + 1]];
      if (hands.has(a) || hands.has(b)) continue;
      adjacent[a].push(b);
      adjacent[b].push(a);
    }
    const parents = Array(count).fill(-1);
    const children = Array.from({ length: count }, () => []);
    const pending = new Set(part.boneIds.filter((bone) => !hands.has(bone))
      .sort((a, b) => distance(centers.get(a), middle) - distance(centers.get(b), middle)));
    for (const bone of pending) {
      pending.delete(bone);
      const queue = [bone];
      for (const parent of queue) {
        for (const child of adjacent[parent]) {
          if (!pending.delete(child)) continue;
          parents[child] = parent;
          children[parent].push(child);
          queue.push(child);
        }
      }
    }
    for (const [bone, parent] of hands) {
      parents[bone] = parent;
      children[parent].push(bone);
    }
    const pivots = binding.joints.map((joint, bone) => {
      if (!centers.has(bone)) return joint.slice(12, 15);
      const center = centers.get(bone), parent = parents[bone];
      if (parent < 0 || !motion.length) return center;
      return pivotEstimate(bone, parent, center, Math.max(extent * 0.24, distance(center, centers.get(parent))), motion);
    });
    const normalize = (v) => {
      const length = Math.hypot(...v);
      return length > 1e-8 ? v.map((value) => value / length) : [0, 1, 0];
    };
    const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const lengths = new Array(count);
    binding.joints = pivots.map((head, bone) => {
      const child = children[bone].sort((a, b) => distance(pivots[b], head) - distance(pivots[a], head))[0];
      const parent = parents[bone];
      const direction = child !== undefined ? vector(pivots[child], head) : parent >= 0 ?
        vector(head, pivots[parent]).map((value) => value * 0.45) : [0, extent * 0.07, 0];
      lengths[bone] = Math.max(extent * 0.015, Math.hypot(...direction));
      const y = normalize(direction);
      const x = normalize(cross(y, Math.abs(y[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]));
      const z = cross(x, y);
      return [...x, 0, ...y, 0, ...z, 0, ...head, 1];
    });
    binding.parents = parents;
    binding.lengths = lengths;
    binding.unused = parents.map((_, bone) => !centers.has(bone));
  }

  function readGlb(bytes) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    check(bytes.length >= 28 && view.getUint32(0, true) === 0x46546c67 &&
      view.getUint32(4, true) === 2 && view.getUint32(8, true) === bytes.length, "Choose a valid glTF 2.0 .glb file.");
    const length = view.getUint32(12, true);
    const bin = 20 + length;
    check(bin + 8 <= bytes.length && view.getUint32(16, true) === 0x4e4f534a &&
      view.getUint32(bin + 4, true) === 0x004e4942 &&
      bin + 8 + view.getUint32(bin, true) === bytes.length, "The GLB needs an embedded binary buffer.");
    const doc = JSON.parse(new TextDecoder().decode(bytes.subarray(20, bin)));
    const buffer = new DataView(bytes.buffer, bytes.byteOffset + bin + 8, view.getUint32(bin, true));
    check(doc.buffers?.length === 1 && !doc.buffers[0].uri && doc.buffers[0].byteLength <= buffer.byteLength,
      "The GLB needs one embedded buffer.");
    function read(index, shape, allowed, normalize = false) {
      const accessor = doc.accessors?.[index];
      const region = doc.bufferViews?.[accessor?.bufferView];
      const channels = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 }[shape];
      const size = { 5121: 1, 5123: 2, 5125: 4, 5126: 4 }[accessor?.componentType];
      check(accessor && accessor.type === shape && allowed.includes(accessor.componentType) &&
        !accessor.sparse && region?.buffer === 0 && !region.extensions?.EXT_meshopt_compression,
        `Unsupported ${shape} accessor in the GLB.`);
      const integer = accessor.componentType !== 5126;
      check(!normalize || !integer || accessor.normalized, "Integer weights must be normalized.");
      const start = region.byteOffset ?? 0;
      const offset = accessor.byteOffset ?? 0;
      const stride = region.byteStride ?? channels * size;
      const count = accessor.count;
      check([start, offset, stride, count, region.byteLength].every(Number.isSafeInteger) &&
        start >= 0 && offset >= 0 && region.byteLength >= 0 && start + region.byteLength <= buffer.byteLength &&
        count > 0 && count <= 1_000_000 && stride >= channels * size &&
        offset + (count - 1) * stride + channels * size <= region.byteLength, "A GLB accessor exceeds its buffer.");
      const values = new (integer && !normalize ? Uint32Array : Float32Array)(count * channels);
      const type = accessor.componentType;
      const divisor = normalize && integer ? (size === 1 ? 255 : 65535) : 1;
      for (let i = 0; i < count; i++) {
        for (let c = 0; c < channels; c++) {
          const at = start + offset + i * stride + c * size;
          const value = type === 5126 ? buffer.getFloat32(at, true) : type === 5125 ? buffer.getUint32(at, true) :
            type === 5123 ? buffer.getUint16(at, true) : buffer.getUint8(at);
          check(Number.isFinite(value), "The GLB contains nonfinite mesh data.");
          values[i * channels + c] = value / divisor;
        }
      }
      return values;
    }
    return { doc, read };
  }

  const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

  function nodeMatrix(node) {
    if (node.matrix) return node.matrix;
    const [x, y, z, w] = node.rotation ?? [0, 0, 0, 1];
    const [sx, sy, sz] = node.scale ?? [1, 1, 1];
    const [tx, ty, tz] = node.translation ?? [0, 0, 0];
    return [
      (1 - 2 * (y * y + z * z)) * sx, 2 * (x * y + z * w) * sx, 2 * (x * z - y * w) * sx, 0,
      2 * (x * y - z * w) * sy, (1 - 2 * (x * x + z * z)) * sy, 2 * (y * z + x * w) * sy, 0,
      2 * (x * z + y * w) * sz, 2 * (y * z - x * w) * sz, (1 - 2 * (x * x + y * y)) * sz, 0,
      tx, ty, tz, 1,
    ];
  }

  function multiply(a, b) {
    return Array.from({ length: 16 }, (_, i) => {
      const row = i % 4, column = i - row;
      return a[row] * b[column] + a[row + 4] * b[column + 1] + a[row + 8] * b[column + 2] + a[row + 12] * b[column + 3];
    });
  }

  function normalMatrix(m) {
    const [a, b, c, , d, e, f, , g, h, i] = m;
    const crossX = [e * i - f * h, f * g - d * i, d * h - e * g];
    const crossY = [h * c - i * b, i * a - g * c, g * b - h * a];
    const crossZ = [b * f - c * e, c * d - a * f, a * e - b * d];
    const determinant = a * crossX[0] + b * crossX[1] + c * crossX[2];
    check(Number.isFinite(determinant) && Math.abs(determinant) > 1e-10, "A mesh has a singular object transform.");
    return { axes: [crossX, crossY, crossZ].flat().map((value) => value / determinant), mirrored: determinant < 0 };
  }

  function influences(joints, weights, at, boneIds) {
    const combined = new Map();
    for (let i = at; i < at + 4; i++) {
      check(weights[i] >= 0 && weights[i] <= 1, "Bone weights must be between zero and one.");
      if (weights[i] <= 0) continue;
      const bone = boneIds[joints[i]];
      check(bone !== undefined, "A vertex references an unknown game bone.");
      if (bone === null) continue;
      combined.set(bone, (combined.get(bone) ?? 0) + weights[i]);
    }
    const result = [...combined].sort(([a], [b]) => a - b);
    const sum = result.reduce((total, [, weight]) => total + weight, 0);
    return result.map(([bone, weight]) => [bone, weight / sum]);
  }

  function readPart(doc, read, mesh, node, matrix, stock, binding, posed, fillWeights) {
    const skin = stock.boneCount !== undefined;
    let boneIds;
    if (skin) {
      const joints = doc.skins?.[node.skin]?.joints;
      check(Array.isArray(joints) && joints.length, "The skinned mesh needs the armature from the rig template.");
      boneIds = joints.map((id) => {
        const name = doc.nodes?.[id]?.name;
        if (isNeutralBone(name)) return null;
        const match = /^att_b(\d+)(?:\.\d+)?$/.exec(name);
        const bone = match && Number(match[1]);
        check(match && bone < stock.boneCount, `Unknown game bone ${name || "(unnamed)"}.`);
        return bone;
      });
      const gameBones = boneIds.filter((bone) => bone !== null);
      check(new Set(gameBones).size === gameBones.length, "A mesh has duplicate game bone names.");
    } else {
      check(node.skin === undefined, "Keep rigid attachment objects separate from the armature.");
    }
    check(Array.isArray(mesh.primitives) && mesh.primitives.length <= 256, "The GLB has too many material groups.");
    const { axes, mirrored } = normalMatrix(matrix);
    const vertices = [], ranges = new Map(), buffers = new Map();
    const materialTag = new RegExp(`^${binding.tag}_m(\\d+)(?:__|$)`);
    for (const primitive of mesh.primitives) {
      check((primitive.mode ?? 4) === 4 && !primitive.targets && !primitive.extensions?.KHR_draco_mesh_compression,
        "Export uncompressed triangle meshes without shape keys.");
      const attrs = primitive.attributes ?? {};
      const key = JSON.stringify([attrs.POSITION, attrs.NORMAL, attrs.TEXCOORD_0, attrs.JOINTS_0, attrs.WEIGHTS_0]);
      check(attrs.JOINTS_1 === undefined, "Use at most four bone influences per vertex.");
      if (!buffers.has(key)) {
        const p = read(attrs.POSITION, "VEC3", [5126]);
        const n = read(attrs.NORMAL, "VEC3", [5126]);
        const uv = read(attrs.TEXCOORD_0, "VEC2", [5126]);
        const count = p.length / 3;
        check(n.length === p.length && uv.length === count * 2 && vertices.length + count <= 65535,
          "A part has invalid streams or more than 65,535 vertices.");
        const joints = skin && read(attrs.JOINTS_0, "VEC4", [5121, 5123]);
        const weights = skin && read(attrs.WEIGHTS_0, "VEC4", [5121, 5123, 5126], true);
        check(!skin || (joints.length === count * 4 && weights.length === count * 4), "Bone weights do not match the vertices.");
        buffers.set(key, { start: vertices.length, count });
        for (let i = 0; i < count; i++) {
          const [x, y, z] = p.subarray(i * 3, i * 3 + 3);
          const [nx, ny, nz] = n.subarray(i * 3, i * 3 + 3);
          const position = [matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12],
            matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13],
            -(matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14])];
          const normal = [axes[0] * nx + axes[3] * ny + axes[6] * nz,
            axes[1] * nx + axes[4] * ny + axes[7] * nz, -(axes[2] * nx + axes[5] * ny + axes[8] * nz)];
          const length = Math.hypot(...normal);
          check(Number.isFinite(length) && length > 0 && position.every((value) => Math.abs(value) < 10000),
            "The GLB contains invalid positions or normals.");
          vertices.push({ position, normal: normal.map((value) => value / length),
            uv: uv.subarray(i * 2, i * 2 + 2), weights: skin ? influences(joints, weights, i * 4, boneIds) : [] });
        }
      }
      const { start, count } = buffers.get(key);
      const name = doc.materials?.[primitive.material]?.name ?? "";
      const match = materialTag.exec(name);
      const material = match ? Number(match[1]) : (stock.materials.length <= 1 ? 0 : -1);
      check(material >= 0 && material < Math.max(1, stock.materials.length),
        `Keep the template material names on ${stock.name}.`);
      const indices = primitive.indices === undefined ? Uint32Array.from({ length: count }, (_, i) => i) :
        read(primitive.indices, "SCALAR", [5121, 5123, 5125]);
      check(indices.length % 3 === 0 && !indices.some((index) => index >= count), "The GLB has invalid triangle indices.");
      if (!ranges.has(material)) ranges.set(material, []);
      const output = ranges.get(material);
      check(output.length + indices.length <= 1_000_000, "A GLB material group has too many triangles.");
      for (let i = 0; i < indices.length; i += 3) {
        output.push(indices[i] + start, indices[i + (mirrored ? 1 : 2)] + start, indices[i + (mirrored ? 2 : 1)] + start);
      }
    }
    const indexCount = [...ranges.values()].reduce((total, indices) => total + indices.length, 0);
    check(indexCount && indexCount <= 1_000_000, "The replacement needs drawable triangles.");
    if (!skin || vertices.every((vertex) => vertex.weights.length)) return { vertices, ranges, filled: 0 };

    const used = new Set();
    for (const indices of ranges.values()) for (const index of indices) used.add(index);
    const missing = [...used].map((index) => vertices[index]).filter((vertex) => !vertex.weights.length);
    if (missing.length) {
      const label = missing.length === 1 ? "vertex" : "vertices";
      check(fillWeights,
        `${stock.name} has ${missing.length.toLocaleString()} exported ${label} without game weights. Enable “Fill missing weights from template” and import again, or assign weights in Blender.`);
      const transfer = transferFrom(posed, binding);
      for (const vertex of missing) {
        vertex.weights = transfer(vertex.position, vertex.normal);
        check(vertex.weights.length, "Could not find game weights on the template surface.");
      }
    }
    // Loose, unweighted vertices do not belong to any exported triangle.
    if (vertices.some((vertex) => !vertex.weights.length)) {
      const remap = new Uint16Array(vertices.length);
      const kept = [];
      for (const [index, vertex] of vertices.entries()) {
        if (!vertex.weights.length) continue;
        remap[index] = kept.length;
        kept.push(vertex);
      }
      for (const indices of ranges.values()) for (let i = 0; i < indices.length; i++) indices[i] = remap[indices[i]];
      return { vertices: kept, ranges, filled: missing.length };
    }
    return { vertices, ranges, filled: missing.length };
  }

  function collectGeometry(bytes, reference, fillWeights) {
    const { doc, read } = readGlb(bytes);
    const matches = new Map(), visited = new Set();
    const roots = doc.scenes?.[doc.scene ?? 0]?.nodes;
    check(Array.isArray(roots) && Array.isArray(doc.nodes) && doc.nodes.length <= 8192, "The GLB has no supported scene.");
    const tags = new Map([...reference.bindings].map(([slot, binding]) => [binding.tag, slot]));
    const stack = roots.map((node) => [node, identity]);
    while (stack.length) {
      const [index, parent] = stack.pop();
      const node = doc.nodes[index];
      check(node && !visited.has(index), "The GLB has an invalid node graph.");
      visited.add(index);
      const local = nodeMatrix(node);
      check(local.length === 16 && local.every(Number.isFinite) && local[3] === 0 && local[7] === 0 &&
        local[11] === 0 && local[15] === 1, "A GLB node has an unsupported transform.");
      const matrix = multiply(parent, local);
      const mesh = doc.meshes?.[node.mesh];
      if (mesh) {
        const tag = [node.name, mesh.name].map((name) => name?.split("__")[0]).find((value) => tags.has(value));
        check(tag, "Use the rig template for this mesh, animation and detail level. Keep its part names.");
        const slot = tags.get(tag);
        check(!matches.has(slot), `More than one mesh uses template slot ${slot}.`);
        const posed = reference.scene.parts.find((part) => part.slot === slot);
        matches.set(slot, readPart(doc, read, mesh, node, matrix, reference.parts[slot], reference.bindings.get(slot), posed, fillWeights));
      }
      for (const child of node.children ?? []) stack.push([child, matrix]);
    }
    check(matches.size, "No meshes matched the game rig template.");
    return matches;
  }

  const word = (value) => {
    const bytes = new Uint8Array(4);
    new DataView(bytes.buffer).setUint32(0, value, true);
    return bytes;
  };

  function join(chunks) {
    const bytes = new Uint8Array(chunks.reduce((total, chunk) => total + chunk.byteLength, 0));
    let at = 0;
    for (const chunk of chunks) {
      const data = new Uint8Array(chunk.buffer, chunk.byteOffset, chunk.byteLength);
      bytes.set(data, at);
      at += data.length;
    }
    return bytes;
  }

  function inverse(point, matrix, position) {
    const x = point[0] - (position ? matrix[9] : 0);
    const y = point[1] - (position ? matrix[10] : 0);
    const z = point[2] - (position ? matrix[11] : 0);
    return [matrix[0] * x + matrix[1] * y + matrix[2] * z,
      matrix[3] * x + matrix[4] * y + matrix[5] * z, matrix[6] * x + matrix[7] * y + matrix[8] * z];
  }

  function writePart(target, bytes, source, sourceBytes, replacement, binding) {
    const { vertices, ranges } = replacement;
    const groups = [[], [], [], []];
    const remap = new Uint16Array(vertices.length);
    const chunks = [bytes.subarray(target.start, target.nameEnd)];
    if (source.vertices) {
      const matrix = binding.matrices[0];
      const packed = new Float32Array(vertices.length * 8);
      for (const [i, { position, normal, uv }] of vertices.entries()) {
        remap[i] = i;
        packed.set([...inverse(position, matrix, true), ...inverse(normal, matrix, false), ...uv], i * 8);
      }
      chunks.push(word(vertices.length), packed);
    } else {
      for (const vertex of vertices) groups[vertex.weights.length - 1].push(vertex);
      const copiesByBone = Array.from({ length: source.boneCount }, () => []);
      for (const [i, vertex] of vertices.entries()) {
        vertex.copies = [];
        vertex.index = i;
        for (const [influence, [bone]] of vertex.weights.entries()) copiesByBone[bone].push({ vertex, influence });
      }
      let out = 0;
      const uv = new Float32Array(vertices.length * 2);
      for (const group of groups) {
        for (const vertex of group) {
          remap[vertex.index] = out;
          uv.set(vertex.uv, out++ * 2);
        }
      }
      const count = copiesByBone.reduce((total, copies) => total + copies.length, 0);
      check(count <= 65535, `${source.name} exceeds 65,535 weighted vertex copies. Split or simplify the geometry.`);
      const positions = new Float32Array(count * 3), normals = new Float32Array(count * 3);
      const bones = new Uint32Array(source.boneCount * 2);
      let copy = 0;
      for (const [bone, copies] of copiesByBone.entries()) {
        bones[bone * 2] = copy;
        const matrix = binding.matrices[bone];
        for (const { vertex, influence } of copies) {
          // Each SKM influence stores its own copy in that bone's local space.
          positions.set(inverse(vertex.position, matrix, true), copy * 3);
          normals.set(inverse(vertex.normal, matrix, false), copy * 3);
          vertex.copies[influence] = copy++;
        }
        bones[bone * 2 + 1] = copy;
      }
      const weights = groups.flatMap((group, i) => {
        const count = i + 1, indexBytes = count === 3 ? 8 : count * 2;
        const stride = indexBytes + (count === 1 ? 0 : count * 4);
        const data = new Uint8Array(stride * group.length);
        const view = new DataView(data.buffer);
        for (const [row, vertex] of group.entries()) {
          for (let j = 0; j < count; j++) {
            view.setUint16(row * stride + j * 2, vertex.copies[j], true);
            if (count > 1) view.setFloat32(row * stride + indexBytes + j * 4, vertex.weights[j][1], true);
          }
        }
        return [word(group.length), data];
      });
      chunks.push(word(count), positions, word(count), normals, word(vertices.length), uv, word(source.boneCount), bones, ...weights);
    }

    const slots = [...ranges].sort(([a], [b]) => a - b);
    const count = slots.reduce((total, [, indices]) => total + indices.length, 0);
    const indices = new Uint16Array(count);
    const materialChunks = [];
    let offset = 0;
    for (const [slot, group] of slots) {
      const material = source.materials[slot];
      if (material) {
        check(offset <= 65535, "A material starts beyond the game's 16-bit material range.");
        materialChunks.push(sourceBytes.subarray(material.recordStart, material.rangeOffset), Uint16Array.of(offset));
      }
      for (const index of group) indices[offset++] = remap[index];
    }
    const indexChunks = [word(indices.length), indices];
    if (source.vertices) chunks.push(...indexChunks);
    else chunks.splice(1, 0, ...indexChunks);
    return join([...chunks, word(materialChunks.length / 2), ...materialChunks, word(target.trackIndex)]);
  }

  async function importUnit(game, reference, bytes, { fillWeights = false } = {}) {
    const replacements = collectGeometry(bytes, reference, fillWeights);
    const assets = new Map(), skipped = [];
    const base = reference.scene.mesh;
    for (const name of reference.scene.meshFiles) {
      const sourceBytes = name === base ? reference.bytes : await game.readAsset(name);
      check(sourceBytes, `Missing mesh ${name}.`);
      const parts = name === base ? reference.parts : models.readModel(sourceBytes);
      const compatible = [...replacements].every(([slot]) => {
        const original = reference.parts[slot], part = parts[slot];
        return part?.name === original.name && part.trackIndex === original.trackIndex &&
          part.boneCount === original.boneCount;
      });
      if (!compatible) {
        skipped.push(name);
        continue;
      }
      const chunks = [];
      let offset = 0;
      for (const [slot, part] of parts.entries()) {
        const replacement = replacements.get(slot);
        if (!replacement) continue;
        chunks.push(sourceBytes.subarray(offset, part.start),
          writePart(part, sourceBytes, reference.parts[slot], reference.bytes, replacement, reference.bindings.get(slot)));
        offset = part.end;
      }
      chunks.push(sourceBytes.subarray(offset));
      assets.set(name, join(chunks));
    }
    check(assets.has(base), "The imported geometry does not match the selected mesh.");
    return { assets, skipped, count: replacements.size, filled: [...replacements.values()].reduce((n, part) => n + part.filled, 0) };
  }

  const api = { template, importUnit, readGlb, gltfMatrix, inverseJoint, multiply, nodeMatrix, isNeutralBone };
  if (typeof module !== "undefined") module.exports = api;
  else root.BalanceRig = api;
})(globalThis);
