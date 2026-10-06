// ---------------------------------------------------------------- 9) CPU skinning (1.1.1)
// Included into attfix.cpp after sound.inc.
//
// Characters are skinned on the CPU before every draw: CSkeletonMeshSubObject 0x4B9110 (thiscall, arg = the
// 6-float keys of the current frame for every bone, called from the sub-object draws 0x4BA850 / 0x4BAB70, result
// in the sub-object's vertex array +0xDC, then copied into a dynamic VB by 0x4BA7F0). The original builds every
// bone matrix with D3DXMatrixRotationYawPitchRoll, transforms through D3DXVec3TransformCoordArray/NormalArray (with
// a per-vertex divide) and blends in x87 code: ~20% of the frame in a battle. Replaced by skin_core.h (SSE, same
// math; checked against the original on live data: the first calls and every 1000th call run both and compare).
// A sub-object drawn again with exactly the same keys (e.g. a second pass, or a pose that did not change since
// the last skinning of that sub-object) keeps the vertices it already has.
#include "skin_core.h"
static int g_optSkin = 1;                       // [Perf] FastSkin; Ctrl+4 with the other optimizations
static DWORD g_skTimed = 0, g_skCalls = 0, g_skHits = 0, g_skVerts = 0, g_skFallback = 0, g_skVerify = 0, g_skBad = 0, g_skGen = 1;
static double g_skMs = 0; static float g_skErr = 0, g_skErrAll = 0;
typedef void (__fastcall *Skin_t)(BYTE* sub, void* edx, const float* keys);
static Skin_t o_Skin = nullptr;
enum { SK_CAP = 65536 };
static float g_skPos[SK_CAP * 4] __attribute__((aligned(16)));
static float g_skNrm[SK_CAP * 4] __attribute__((aligned(16)));
static float g_skRef[SK_CAP * 8];
struct SkEnt {
    BYTE* sub; DWORD gen, lastSeen;
    const void* lists[5]; int counts[5]; const void* src[2]; float* out;   // what the validation was done for
    bool valid;                                     // lists/indices checked for this layout
    bool have; const float* keysAt; int nb; float* keys; int keysCap;      // last keys we skinned with
};
enum { SK_MASK = 1023 };
static SkEnt g_skEnt[SK_MASK + 1];
static SkEnt* SkGet(BYTE* sub) {
    DWORD h = ((DWORD)sub >> 3) * 2654435761u; SkEnt* reuse = nullptr;
    for (int i = 0; i < 16; ++i) {
        SkEnt* e = &g_skEnt[(h + i) & SK_MASK];
        if (e->sub == sub) return e;
        if (!e->sub) { if (!reuse) reuse = e; break; }
        if (!reuse && g_curFrame - e->lastSeen > 120) reuse = e;
    }
    if (!reuse) reuse = &g_skEnt[h & SK_MASK];
    reuse->sub = sub; reuse->valid = false; reuse->have = false; reuse->gen = 0;
    return reuse;
}
static inline int VecCount(BYTE* sub, int off, int elem) {
    BYTE* b = *(BYTE**)(sub + off); if (!b) return 0;
    return (int)((*(BYTE**)(sub + off + 4) - b) / elem);
}
static void SkinToggle(int on);
__attribute__((force_align_arg_pointer))
static void __fastcall h_Skin(BYTE* sub, void* edx, const float* keys) {
    if (!g_optSkin) { o_Skin(sub, edx, keys); return; }
    ++g_skCalls;
    LONGLONG t0 = Now();
    SkinMesh m;
    m.keys = keys;
    m.nBones = VecCount(sub, 0x78, 8); m.ranges = *(const int**)(sub + 0x78);
    m.srcPos = *(const float**)(sub + 0x48); m.srcNrm = *(const float**)(sub + 0x58);
    m.l1 = *(const unsigned short**)(sub + 0x88); m.n1 = VecCount(sub, 0x88, 2);
    m.l2 = *(const unsigned char**)(sub + 0x98); m.n2 = VecCount(sub, 0x98, 12);
    m.l3 = *(const unsigned char**)(sub + 0xA8); m.n3 = VecCount(sub, 0xA8, 20);
    m.l4 = *(const unsigned char**)(sub + 0xB8); m.n4 = VecCount(sub, 0xB8, 24);
    m.out = *(float**)(sub + 0xDC);
    int nOut = VecCount(sub, 0xDC, 32), nAll = m.n1 + m.n2 + m.n3 + m.n4;
    SkEnt* e = SkGet(sub);
    e->lastSeen = g_curFrame;
    const void* lists[5] = { m.ranges, m.l1, m.l2, m.l3, m.l4 }; int counts[5] = { m.nBones, m.n1, m.n2, m.n3, m.n4 };
    if (!e->valid || e->gen != g_skGen || memcmp(e->lists, lists, sizeof lists) || memcmp(e->counts, counts, sizeof counts) ||
        e->src[0] != m.srcPos || e->src[1] != m.srcNrm || e->out != m.out) {
        memcpy(e->lists, lists, sizeof lists); memcpy(e->counts, counts, sizeof counts);
        e->src[0] = m.srcPos; e->src[1] = m.srcNrm; e->out = m.out; e->gen = g_skGen; e->have = false;
        int s = 0; bool ok = m.nBones >= 0 && m.nBones <= 4096 && nAll <= nOut && (nAll == 0 || m.out);
        for (int b = 0; ok && b < m.nBones; ++b) { int c = m.ranges[b * 2 + 1] - m.ranges[b * 2]; if (c < 0) ok = false; else s += c; }
        ok = ok && s <= SK_CAP && (s == 0 || (m.srcPos && m.srcNrm)) && SkinMaxIndex(m) <= s;
        e->valid = ok;
        if (!ok) { static int logged = 0; if (logged++ < 5) LOG("skin: sub-object %p layout not handled (bones %d, outputs %d/%d, copies %d), original code used", sub, m.nBones, nAll, nOut, s); }
    }
    if (!e->valid) { ++g_skFallback; o_Skin(sub, edx, keys); return; }
    int nk = m.nBones * 6;
    bool verify = g_skCalls <= 300 || g_skCalls % 1000 == 0;
    if (!verify && e->have && e->keysAt == keys && e->nb == m.nBones && !memcmp(e->keys, keys, nk * sizeof(float))) {
        ++g_skHits; g_skMs += (Now() - t0) * g_tickMs; return;
    }
    if (verify) { o_Skin(sub, edx, keys); memcpy(g_skRef, m.out, (size_t)nAll * 32); }
    SkinTransform(m, g_skPos, g_skNrm, SK_CAP);
    int n = SkinBlend(m, g_skPos, g_skNrm);
    g_skVerts += n;
    if (verify) {
        ++g_skVerify; float err = 0;
        for (int i = 0; i < nAll; ++i) for (int k = 0; k < 6; ++k) {
            float a = g_skRef[i * 8 + k], b = m.out[i * 8 + k], d = fabsf(a - b) / (fabsf(a) > 1.0f ? fabsf(a) : 1.0f);
            if (!(d <= err)) err = d;                                  // NaN counts as an error too
        }
        if (!(err <= g_skErr)) g_skErr = err;
        if (!(err <= g_skErrAll)) g_skErrAll = err;
        if (!(err < 1e-3f)) {
            if (g_skBad++ < 5) LOG("skin: sub-object %p differs from the original by %g (bones %d, vertices %d)", sub, err, m.nBones, nAll);
            memcpy(m.out, g_skRef, (size_t)nAll * 32);                  // keep the original's result
            if (g_skBad >= 3) { SkinToggle(0); LOG("skin: SSE skinning switched off (results differ from the original)"); }
            return;
        }
    }
    if (e->keysCap < nk) { free(e->keys); e->keys = (float*)malloc(nk * sizeof(float)); e->keysCap = e->keys ? nk : 0; }
    if (e->keys) { memcpy(e->keys, keys, nk * sizeof(float)); e->keysAt = keys; e->nb = m.nBones; e->have = true; }
    if (!verify) { g_skMs += (Now() - t0) * g_tickMs; ++g_skTimed; }
}
static void SkinToggle(int on) { if (on != g_optSkin) { g_optSkin = on; ++g_skGen; } }
static void InstallSkin() {
    static const BYTE c[6] = { 0x81, 0xEC, 0x0C, 0x01, 0x00, 0x00 };   // sub esp, 0x10C
    o_Skin = (Skin_t)Detour((BYTE*)0x004B9110, c, 6, (void*)h_Skin);
    if (!o_Skin) { g_optSkin = 0; LOG("skinning: unexpected code, not installed"); return; }
    LOG("skinning: SSE skinning installed (FastSkin=%d)", g_optSkin);
}
static void SkinStats() {
    DWORD fast = g_skCalls - g_skHits - g_skFallback;
    PLOG("SKIN fast=%d: calls=%lu same pose (kept)=%lu skinned=%lu vertices=%lu (avg %lu) time=%.2f ms (%.2f us/call) fallback=%lu | verify=%lu maxerr=%.2g (all time %.2g) bad=%lu",
         g_optSkin, g_skCalls, g_skHits, fast, g_skVerts, fast ? g_skVerts / fast : 0, g_skMs, g_skTimed ? g_skMs * 1000.0 / (g_skTimed + g_skHits) : 0.0,
         g_skFallback, g_skVerify, g_skErr, g_skErrAll, g_skBad);
    g_skTimed = g_skCalls = g_skHits = g_skVerts = g_skFallback = g_skVerify = 0; g_skMs = 0; g_skErr = 0;
}
