/* glTF 2.0 binary export for posed unit models. */
(function (root) {
  "use strict";

  const arrayBuffer = 34962;
  const elementArrayBuffer = 34963;
  const float = 5126;
  const unsignedShort = 5123;
  const align = (size) => Math.ceil(size / 4) * 4;

  function makeGlb(parts, textures, source, rig, motion) {
    const scene = { name: source.unit, nodes: [], extras: source };
    const document = {
      asset: { version: "2.0", generator: "AttT Balance Studio" },
      scene: 0, scenes: [scene], nodes: [], meshes: [], materials: [],
      bufferViews: [], accessors: [],
    };
    const data = [];
    const materials = new Map();
    const images = new Map();
    let length = 0;
    const view = (value, options = {}) => {
      const bytes = new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
      const index = document.bufferViews.length;
      document.bufferViews.push({ buffer: 0, byteOffset: length, byteLength: bytes.length, ...options });
      data.push({ bytes, offset: length });
      length += align(bytes.length);
      return index;
    };
    const accessor = (entry) => document.accessors.push(entry) - 1;
    const animation = motion && { name: motion.name, samplers: [], channels: [] };
    const time = motion && accessor({ bufferView: view(motion.times), componentType: float, type: "SCALAR",
      count: motion.times.length, min: [0], max: [motion.times.at(-1)] });
    if (animation) {
      document.animations = [animation];
      scene.extras = { ...source, att_animation_frames: motion.times.length, att_animation_fps: motion.fps };
    }

    function animateNode(id, keys) {
      const node = document.nodes[id];
      delete node.matrix;
      Object.assign(node, keys.rest);
      for (const [path, type, values] of [
        ["translation", "VEC3", keys.translations], ["rotation", "VEC4", keys.rotations],
      ]) {
        const output = accessor({ bufferView: view(values), componentType: float, type, count: motion.times.length });
        const sampler = animation.samplers.push({ input: time, output, interpolation: "LINEAR" }) - 1;
        animation.channels.push({ sampler, target: { node: id, path } });
      }
    }

    function material(name, texture) {
      if (materials.has(name)) return materials.get(name);
      const image = textures.get(texture);
      const pbrMetallicRoughness = { metallicFactor: 0, roughnessFactor: 0.85 };
      const entry = { name: name || "Default", doubleSided: true, pbrMetallicRoughness };
      if (image) {
        if (!images.has(texture)) {
          document.images ??= [];
          document.textures ??= [];
          const index = document.images.push({ name: texture, mimeType: "image/png", bufferView: view(image.png) }) - 1;
          images.set(texture, document.textures.push({ source: index }) - 1);
        }
        pbrMetallicRoughness.baseColorTexture = { index: images.get(texture) };
        if (image.masked) Object.assign(entry, { alphaMode: "MASK", alphaCutoff: 0.35 });
      } else {
        pbrMetallicRoughness.baseColorFactor = [0.7, 0.73, 0.75, 1];
      }
      const index = document.materials.push(entry) - 1;
      materials.set(name, index);
      return index;
    }

    function addSkin(name, binding, motionKeys) {
      const { joints, parents, lengths, unused } = binding;
      document.skins ??= [];
      const inverse = new Float32Array(joints.length * 16);
      const nodes = joints.map((joint, i) => {
        const [a, b, c, , d, e, f, , g, h, j, , x, y, z] = joint;
        inverse.set([a, d, g, 0, b, e, h, 0, c, f, j, 0,
          -(a * x + b * y + c * z), -(d * x + e * y + f * z), -(g * x + h * y + j * z), 1], i * 16);
        const node = { name: `att_b${i}`, matrix: joint };
        if (lengths) node.extras = { att_length: lengths[i], att_unused: unused[i] };
        return document.nodes.push(node) - 1;
      });
      const roots = [];
      for (const [i, id] of nodes.entries()) {
        const parent = parents?.[i] ?? -1;
        if (parent < 0) roots.push(id);
        else {
          const p = document.nodes[nodes[parent]];
          (p.children ??= []).push(id);
          const local = new Array(16);
          const a = parent * 16, joint = joints[i];
          for (let k = 0; k < 16; k++) {
            const row = k % 4, col = k - row;
            local[k] = inverse[a + row] * joint[col] + inverse[a + row + 4] * joint[col + 1] +
              inverse[a + row + 8] * joint[col + 2] + inverse[a + row + 12] * joint[col + 3];
          }
          local[15] = 1;
          document.nodes[id].matrix = local;
        }
      }
      if (motionKeys) for (const [i, id] of nodes.entries()) animateNode(id, motionKeys[i]);
      const skeleton = document.nodes.push({ name: `${name}_rig`, children: roots }) - 1;
      scene.nodes.push(skeleton);
      return document.skins.push({ name, skeleton, joints: nodes,
        inverseBindMatrices: accessor({ bufferView: view(inverse), componentType: float, type: "MAT4", count: joints.length }),
      }) - 1;
    }

    for (const part of parts) {
      if (!part.indices.length) continue;
      const vertices = part.vertices.slice();
      const count = vertices.length / 8;
      const min = [Infinity, Infinity, Infinity];
      const max = [-Infinity, -Infinity, -Infinity];
      for (let i = 0; i < vertices.length; i += 8) {
        // The game uses left-handed model coordinates. glTF uses right-handed coordinates.
        vertices[i + 2] *= -1;
        vertices[i + 5] *= -1;
        const normalLength = Math.hypot(vertices[i + 3], vertices[i + 4], vertices[i + 5]);
        if (normalLength) {
          for (let axis = 3; axis <= 5; axis++) vertices[i + axis] /= normalLength;
        } else vertices[i + 4] = 1;
        for (let axis = 0; axis < 3; axis++) {
          min[axis] = Math.min(min[axis], vertices[i + axis]);
          max[axis] = Math.max(max[axis], vertices[i + axis]);
        }
      }
      const bufferView = view(vertices, { target: arrayBuffer, byteStride: 32 });
      const attributes = {
        POSITION: accessor({ bufferView, componentType: float, count, type: "VEC3", min, max }),
        NORMAL: accessor({ bufferView, byteOffset: 12, componentType: float, count, type: "VEC3" }),
        TEXCOORD_0: accessor({ bufferView, byteOffset: 24, componentType: float, count, type: "VEC2" }),
      };
      const binding = rig?.get(part.slot);
      if (binding?.weld) attributes._ATT_WELD = accessor({
        bufferView: view(binding.weld, { target: arrayBuffer }), componentType: float, count, type: "SCALAR",
      });
      if (binding?.joints) {
        attributes.JOINTS_0 = accessor({ bufferView: view(binding.bones, { target: arrayBuffer }),
          componentType: unsignedShort, count, type: "VEC4" });
        attributes.WEIGHTS_0 = accessor({ bufferView: view(binding.weights, { target: arrayBuffer }),
          componentType: float, count, type: "VEC4" });
      }
      const ranges = part.materials.length ? part.materials : [{ start: 0, texture: "" }];
      const primitives = [];
      for (const [index, { start, texture }] of ranges.entries()) {
        const end = ranges[index + 1]?.start ?? part.indices.length;
        if (start === end) continue;
        if ((end - start) % 3) throw new Error("The mesh has an incomplete triangle.");
        const indices = part.indices.slice(start, end);
        for (let i = 0; i < indices.length; i += 3) {
          [indices[i + 1], indices[i + 2]] = [indices[i + 2], indices[i + 1]];
        }
        const indicesAccessor = accessor({ bufferView: view(indices, { target: elementArrayBuffer }),
          componentType: unsignedShort, count: indices.length, type: "SCALAR" });
        const materialName = binding ? `${binding.tag}_m${index}__${texture || "default"}` : texture;
        primitives.push({ attributes, indices: indicesAccessor, material: material(materialName, texture) });
      }
      if (!primitives.length) continue;
      const name = binding ? `${binding.tag}__${part.name.replace(/\0/g, "")}` : part.name;
      const mesh = document.meshes.push({ name, primitives }) - 1;
      const node = { name, mesh };
      const motionKeys = motion?.parts.get(part.slot);
      if (binding?.joints) node.skin = addSkin(binding.tag, binding, motionKeys);
      const nodeId = document.nodes.push(node) - 1;
      scene.nodes.push(nodeId);
      if (motionKeys && !binding?.joints) animateNode(nodeId, motionKeys[0]);
    }

    if (!scene.nodes.length) throw new Error("There is no geometry to export.");
    document.buffers = [{ byteLength: length }];
    const json = new TextEncoder().encode(JSON.stringify(document));
    const jsonLength = align(json.length);
    const binaryStart = 20 + jsonLength;
    const output = new Uint8Array(binaryStart + 8 + length);
    const header = new DataView(output.buffer);
    header.setUint32(0, 0x46546c67, true); // glTF
    header.setUint32(4, 2, true);
    header.setUint32(8, output.length, true);
    header.setUint32(12, jsonLength, true);
    header.setUint32(16, 0x4e4f534a, true); // JSON
    output.fill(32, 20, binaryStart);
    output.set(json, 20);
    header.setUint32(binaryStart, length, true);
    header.setUint32(binaryStart + 4, 0x004e4942, true); // BIN
    for (const { bytes, offset } of data) output.set(bytes, binaryStart + 8 + offset);
    return output;
  }

  const api = { makeGlb };
  if (typeof module !== "undefined") module.exports = api;
  else root.BalanceGlb = api;
})(globalThis);
