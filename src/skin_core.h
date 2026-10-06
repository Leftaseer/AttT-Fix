// ---------------------------------------------------------------- CPU skinning core (1.1.1), no Windows dependencies
// Same algorithm as the game's CSkeletonMeshSubObject skinning (0x4B9110), written with SSE:
//  1) every bone owns a consecutive range of bone-local vertex copies (positions +0x48, normals +0x58);
//     they are transformed by the bone matrix  RotationYawPitchRoll(key[1], key[0], key[2]) * Translation(key[3..5])
//     (D3DXVec3TransformCoordArray / TransformNormalArray; w is exactly 1 for such a matrix)
//  2) output vertices (32 bytes: position, normal, uv - uv untouched) are written in order:
//     1-bone list (u16 index), 2-bone (u16 i0,i1; f w0,w1), 3-bone (u16 i0,i1,i2,pad; f w0,w1,w2),
//     4-bone (u16 i0..i3; f w0..w3) - weighted sums of the transformed copies.
#include <emmintrin.h>
#include <math.h>
#include <string.h>

struct SkinMesh {
    const float* keys; int nBones;               // 6 floats per bone: pitch, yaw, roll, x, y, z
    const int* ranges;                           // nBones pairs {begin, end}: copies per bone = end - begin
    const float* srcPos; const float* srcNrm;    // 12-byte stride
    const unsigned short* l1; int n1;
    const unsigned char* l2; int n2;             // 12-byte records
    const unsigned char* l3; int n3;             // 20-byte records
    const unsigned char* l4; int n4;             // 24-byte records
    float* out;                                  // 32-byte vertices
};

// sine and cosine of 4 floats at once (Cephes single precision: Cody-Waite reduction by pi/4, minimax
// polynomials; ~1 ulp for |x| < 8192, which covers any key angle)
static inline void SkinSinCos4(__m128 x, __m128* s, __m128* c) {
    const __m128 signMask = _mm_castsi128_ps(_mm_set1_epi32((int)0x80000000));
    __m128 sinSign = _mm_and_ps(x, signMask);
    x = _mm_andnot_ps(signMask, x);
    __m128i j = _mm_cvttps_epi32(_mm_mul_ps(x, _mm_set1_ps(1.27323954473516f)));   // 4/pi
    j = _mm_and_si128(_mm_add_epi32(j, _mm_set1_epi32(1)), _mm_set1_epi32(~1));
    __m128 y = _mm_cvtepi32_ps(j);
    __m128i jc = _mm_sub_epi32(j, _mm_set1_epi32(2));
    sinSign = _mm_xor_ps(sinSign, _mm_castsi128_ps(_mm_slli_epi32(_mm_and_si128(j, _mm_set1_epi32(4)), 29)));
    __m128 cosSign = _mm_castsi128_ps(_mm_slli_epi32(_mm_andnot_si128(jc, _mm_set1_epi32(4)), 29));
    __m128 polyMask = _mm_castsi128_ps(_mm_cmpeq_epi32(_mm_and_si128(j, _mm_set1_epi32(2)), _mm_setzero_si128()));
    x = _mm_add_ps(x, _mm_mul_ps(y, _mm_set1_ps(-0.78515625f)));
    x = _mm_add_ps(x, _mm_mul_ps(y, _mm_set1_ps(-2.4187564849853515625e-4f)));
    x = _mm_add_ps(x, _mm_mul_ps(y, _mm_set1_ps(-3.77489497744594108e-8f)));
    __m128 z = _mm_mul_ps(x, x);
    __m128 pc = _mm_set1_ps(2.443315711809948e-5f);
    pc = _mm_add_ps(_mm_mul_ps(pc, z), _mm_set1_ps(-1.388731625493765e-3f));
    pc = _mm_add_ps(_mm_mul_ps(pc, z), _mm_set1_ps(4.166664568298827e-2f));
    pc = _mm_mul_ps(_mm_mul_ps(pc, z), z);
    pc = _mm_add_ps(_mm_sub_ps(pc, _mm_mul_ps(z, _mm_set1_ps(0.5f))), _mm_set1_ps(1.0f));
    __m128 ps = _mm_set1_ps(-1.9515295891e-4f);
    ps = _mm_add_ps(_mm_mul_ps(ps, z), _mm_set1_ps(8.3321608736e-3f));
    ps = _mm_add_ps(_mm_mul_ps(ps, z), _mm_set1_ps(-1.6666654611e-1f));
    ps = _mm_add_ps(_mm_mul_ps(_mm_mul_ps(ps, z), x), x);
    __m128 sv = _mm_or_ps(_mm_and_ps(polyMask, ps), _mm_andnot_ps(polyMask, pc));
    __m128 cv = _mm_or_ps(_mm_and_ps(polyMask, pc), _mm_andnot_ps(polyMask, ps));
    *s = _mm_xor_ps(sv, sinSign); *c = _mm_xor_ps(cv, cosSign);
}

// D3DXMatrixRotationYawPitchRoll (row vectors: v * M), rows 0..2; translation in row 3
static inline void SkinBoneMatrix(const float* k, __m128* r) {
    __m128 sv, cv; SkinSinCos4(_mm_setr_ps(k[0], k[1], k[2], 0.0f), &sv, &cv);
    float s4[4] __attribute__((aligned(16))), c4[4] __attribute__((aligned(16)));
    _mm_store_ps(s4, sv); _mm_store_ps(c4, cv);
    float sp = s4[0], cp = c4[0], sy = s4[1], cy = c4[1], sr = s4[2], cr = c4[2];
    r[0] = _mm_setr_ps(sr * sp * sy + cr * cy, sr * cp, sr * sp * cy - cr * sy, 0.0f);
    r[1] = _mm_setr_ps(cr * sp * sy - sr * cy, cr * cp, cr * sp * cy + sr * sy, 0.0f);
    r[2] = _mm_setr_ps(cp * sy, -sp, cp * cy, 0.0f);
    r[3] = _mm_setr_ps(k[3], k[4], k[5], 0.0f);
}

// scratch: transformed copies, 4 floats each (aligned), capacity in vertices
static inline int SkinTransform(const SkinMesh& m, float* tPos, float* tNrm, int cap) {
    int s = 0;
    const float* sp = m.srcPos; const float* sn = m.srcNrm;
    for (int b = 0; b < m.nBones; ++b) {
        int c = m.ranges[b * 2 + 1] - m.ranges[b * 2];
        if (c <= 0) continue;
        if (s + c > cap) return -1;
        __m128 r[4]; SkinBoneMatrix(m.keys + b * 6, r);
        float* dp = tPos + s * 4; float* dn = tNrm + s * 4;
        for (int i = 0; i < c; ++i, sp += 3, sn += 3, dp += 4, dn += 4) {
            __m128 p = _mm_add_ps(_mm_add_ps(_mm_mul_ps(_mm_set1_ps(sp[0]), r[0]), _mm_mul_ps(_mm_set1_ps(sp[1]), r[1])),
                                  _mm_add_ps(_mm_mul_ps(_mm_set1_ps(sp[2]), r[2]), r[3]));
            __m128 n = _mm_add_ps(_mm_add_ps(_mm_mul_ps(_mm_set1_ps(sn[0]), r[0]), _mm_mul_ps(_mm_set1_ps(sn[1]), r[1])),
                                  _mm_mul_ps(_mm_set1_ps(sn[2]), r[2]));
            _mm_store_ps(dp, p); _mm_store_ps(dn, n);
        }
        s += c;
    }
    return s;
}

static inline void SkinStore(float* o, __m128 p, __m128 n) {
    _mm_storel_pi((__m64*)o, p); _mm_store_ss(o + 2, _mm_movehl_ps(p, p));
    _mm_storel_pi((__m64*)(o + 3), n); _mm_store_ss(o + 5, _mm_movehl_ps(n, n));
}

// indices must be < the number of transformed copies (checked by the caller); returns vertices written
static inline int SkinBlend(const SkinMesh& m, const float* tPos, const float* tNrm) {
    float* o = m.out;
    for (int i = 0; i < m.n1; ++i, o += 8) {
        unsigned a = m.l1[i] * 4;
        SkinStore(o, _mm_load_ps(tPos + a), _mm_load_ps(tNrm + a));
    }
    const unsigned char* q = m.l2;
    for (int i = 0; i < m.n2; ++i, q += 12, o += 8) {
        unsigned a = *(const unsigned short*)q * 4, b = *(const unsigned short*)(q + 2) * 4;
        __m128 wa = _mm_load1_ps((const float*)(q + 4)), wb = _mm_load1_ps((const float*)(q + 8));
        SkinStore(o, _mm_add_ps(_mm_mul_ps(_mm_load_ps(tPos + a), wa), _mm_mul_ps(_mm_load_ps(tPos + b), wb)),
                     _mm_add_ps(_mm_mul_ps(_mm_load_ps(tNrm + a), wa), _mm_mul_ps(_mm_load_ps(tNrm + b), wb)));
    }
    q = m.l3;
    for (int i = 0; i < m.n3; ++i, q += 20, o += 8) {
        const unsigned short* x = (const unsigned short*)q; const float* w = (const float*)(q + 8);
        unsigned a = x[0] * 4, b = x[1] * 4, c = x[2] * 4;
        __m128 wa = _mm_set1_ps(w[0]), wb = _mm_set1_ps(w[1]), wc = _mm_set1_ps(w[2]);
        SkinStore(o, _mm_add_ps(_mm_add_ps(_mm_mul_ps(_mm_load_ps(tPos + a), wa), _mm_mul_ps(_mm_load_ps(tPos + b), wb)), _mm_mul_ps(_mm_load_ps(tPos + c), wc)),
                     _mm_add_ps(_mm_add_ps(_mm_mul_ps(_mm_load_ps(tNrm + a), wa), _mm_mul_ps(_mm_load_ps(tNrm + b), wb)), _mm_mul_ps(_mm_load_ps(tNrm + c), wc)));
    }
    q = m.l4;
    for (int i = 0; i < m.n4; ++i, q += 24, o += 8) {
        const unsigned short* x = (const unsigned short*)q; const float* w = (const float*)(q + 8);
        unsigned a = x[0] * 4, b = x[1] * 4, c = x[2] * 4, d = x[3] * 4;
        __m128 wa = _mm_set1_ps(w[0]), wb = _mm_set1_ps(w[1]), wc = _mm_set1_ps(w[2]), wd = _mm_set1_ps(w[3]);
        SkinStore(o, _mm_add_ps(_mm_add_ps(_mm_mul_ps(_mm_load_ps(tPos + a), wa), _mm_mul_ps(_mm_load_ps(tPos + b), wb)),
                                _mm_add_ps(_mm_mul_ps(_mm_load_ps(tPos + c), wc), _mm_mul_ps(_mm_load_ps(tPos + d), wd))),
                     _mm_add_ps(_mm_add_ps(_mm_mul_ps(_mm_load_ps(tNrm + a), wa), _mm_mul_ps(_mm_load_ps(tNrm + b), wb)),
                                _mm_add_ps(_mm_mul_ps(_mm_load_ps(tNrm + c), wc), _mm_mul_ps(_mm_load_ps(tNrm + d), wd))));
    }
    return (int)((o - m.out) / 8);
}

// largest index used by the blend lists (+1); 0 if none
static inline int SkinMaxIndex(const SkinMesh& m) {
    unsigned mx = 0;
    for (int i = 0; i < m.n1; ++i) if (m.l1[i] >= mx) mx = m.l1[i] + 1u;
    for (int i = 0; i < m.n2; ++i) for (int k = 0; k < 2; ++k) { unsigned v = ((const unsigned short*)(m.l2 + i * 12))[k]; if (v >= mx) mx = v + 1; }
    for (int i = 0; i < m.n3; ++i) for (int k = 0; k < 3; ++k) { unsigned v = ((const unsigned short*)(m.l3 + i * 20))[k]; if (v >= mx) mx = v + 1; }
    for (int i = 0; i < m.n4; ++i) for (int k = 0; k < 4; ++k) { unsigned v = ((const unsigned short*)(m.l4 + i * 24))[k]; if (v >= mx) mx = v + 1; }
    return (int)mx;
}
