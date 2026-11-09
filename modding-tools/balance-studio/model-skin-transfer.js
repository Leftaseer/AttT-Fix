/* Transfer missing weights from the nearest surface of the same template part. */
(function (root) {
  "use strict";

  const subtract = (a, b) => a.map((value, i) => value - b[i]);
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

  function triangle(points, ids) {
    const [a, b, c] = ids.map((id) => points[id]);
    const ab = subtract(b, a), ac = subtract(c, a);
    const aa = dot(ab, ab), bb = dot(ab, ac), cc = dot(ac, ac);
    const minimum = a.map((x, i) => Math.min(x, b[i], c[i]));
    const maximum = a.map((x, i) => Math.max(x, b[i], c[i]));
    return { ids, a, ab, ac, aa, bb, cc, minimum, maximum,
      center: a.map((x, i) => (x + b[i] + c[i]) / 3) };
  }

  function treeOf(triangles) {
    const minimum = [Infinity, Infinity, Infinity], maximum = [-Infinity, -Infinity, -Infinity];
    for (const tri of triangles) {
      for (let i = 0; i < 3; i++) {
        minimum[i] = Math.min(minimum[i], tri.minimum[i]);
        maximum[i] = Math.max(maximum[i], tri.maximum[i]);
      }
    }
    if (triangles.length <= 8) return { minimum, maximum, triangles };
    const lengths = subtract(maximum, minimum);
    const axis = lengths.indexOf(Math.max(...lengths));
    triangles.sort((a, b) => a.center[axis] - b.center[axis]);
    const mid = triangles.length >> 1;
    return { minimum, maximum, left: treeOf(triangles.slice(0, mid)), right: treeOf(triangles.slice(mid)) };
  }

  function boxDistance(point, box) {
    let squared = 0;
    for (let i = 0; i < 3; i++) {
      const gap = Math.max(box.minimum[i] - point[i], point[i] - box.maximum[i], 0);
      squared += gap * gap;
    }
    return squared;
  }

  function closest(point, tri) {
    const { a, ab, ac, aa, bb, cc } = tri;
    const delta = subtract(point, a);
    const d = dot(delta, ab), e = dot(delta, ac);
    const area = aa * cc - bb * bb;
    let u = 0, v = 0, best = Infinity;
    function candidate(s, t) {
      const x = delta[0] - s * ab[0] - t * ac[0];
      const y = delta[1] - s * ab[1] - t * ac[1];
      const z = delta[2] - s * ab[2] - t * ac[2];
      const distance = x * x + y * y + z * z;
      if (distance < best) { u = s; v = t; best = distance; }
    }
    if (area > 1e-20) {
      const s = (cc * d - bb * e) / area, t = (aa * e - bb * d) / area;
      if (s >= 0 && t >= 0 && s + t <= 1) {
        candidate(s, t);
        return { distance: best, barycentric: [1 - u - v, u, v] };
      }
    }
    const clamp = (x) => Math.max(0, Math.min(1, x));
    candidate(clamp(aa ? d / aa : 0), 0);
    candidate(0, clamp(cc ? e / cc : 0));
    const length = aa + cc - 2 * bb;
    const side = clamp(length > 0 ? (e - d + aa - bb) / length : 0);
    candidate(1 - side, side);
    return { distance: best, barycentric: [1 - u - v, u, v] };
  }

  function transferFrom(part, binding) {
    const points = [], normals = [];
    for (let at = 0; at < part.vertices.length; at += 8) {
      points.push(Array.from(part.vertices.subarray(at, at + 3)));
      normals.push(Array.from(part.vertices.subarray(at + 3, at + 6)));
    }
    const triangles = [];
    for (let at = 0; at + 2 < part.indices.length; at += 3) {
      triangles.push(triangle(points, Array.from(part.indices.subarray(at, at + 3))));
    }
    if (!triangles.length) throw new Error("The template part has no surface to transfer weights from.");
    const tree = treeOf(triangles);
    const extent = Math.hypot(...subtract(tree.maximum, tree.minimum));
    const normalPenalty = (extent * 0.006) ** 2;

    return (position, normal) => {
      let score = Infinity, chosen;
      function search(box, lower = boxDistance(position, box)) {
        if (lower > score) return;
        if (!box.triangles) {
          const left = boxDistance(position, box.left), right = boxDistance(position, box.right);
          if (left <= right) {
            search(box.left, left);
            search(box.right, right);
          } else {
            search(box.right, right);
            search(box.left, left);
          }
          return;
        }
        for (const tri of box.triangles) {
          if (boxDistance(position, tri) > score) continue;
          const hit = closest(position, tri);
          const n = [0, 1, 2].map((axis) =>
            tri.ids.reduce((sum, id, i) => sum + normals[id][axis] * hit.barycentric[i], 0));
          const length = Math.hypot(...n);
          const cosine = length ? Math.max(-1, Math.min(1, dot(normal, n) / length)) : 0;
          const candidate = hit.distance + (1 - cosine) * normalPenalty;
          if (candidate < score) {
            score = candidate;
            chosen = { tri, ...hit };
          }
        }
      }
      search(tree);
      const combined = new Map();
      for (const [i, id] of chosen.tri.ids.entries()) {
        for (let at = id * 4; at < id * 4 + 4; at++) {
          const weight = binding.weights[at] * chosen.barycentric[i];
          if (weight <= 1e-6) continue;
          const bone = binding.bones[at];
          combined.set(bone, (combined.get(bone) ?? 0) + weight);
        }
      }
      const weights = [...combined].sort(([a, wa], [b, wb]) => wb - wa || a - b).slice(0, 4);
      const sum = weights.reduce((total, [, weight]) => total + weight, 0);
      return weights.map(([bone, weight]) => [bone, weight / sum]);
    };
  }

  if (typeof module !== "undefined") module.exports = { transferFrom };
  else root.BalanceSkinTransfer = { transferFrom };
})(globalThis);
