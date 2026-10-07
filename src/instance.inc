// ---------------------------------------------------------------- 11) forest: hardware instancing of opaque trees (1.1.2)
// Included into attfix.cpp after skin.inc. Needs the deferred-restore device hooks (effectsm.inc) for hp_DIP.
//
// The opaque 3D trees are drawn part by part with the fixed-function pipeline: per part SetTransform(WORLD),
// CommitChanges (tint) and a DrawIndexedPrimitive per material subset - thousands of draws per frame at the edge
// of a forest (CPU bound). Fixed-function cannot instance, so inside the grouped tree phases (renderopt.inc) each
// such draw is recorded instead (vertex/index buffer, ranges, texture, material, world matrix, tint) and at the end
// of the phase every distinct mesh subset is drawn ONCE with D3D9 instancing: a vs_3_0/ps_3_0 pair reproduces the
// fixed-function result of these techniques (one directional light + ambient + emissive, stage 0
// SELECTARG1/MODULATE/MODULATE2X of texture and diffuse, alpha texture x TFACTOR, fog linear/exp/exp2) with the
// world matrix and tint per instance. The fixed-function state is checked once per effect group; anything outside
// that (more lights, other stage ops, vertex blending, clip planes, shaders, other vertex formats) is drawn the
// original way. [Perf] TreeInstancing=1 (needs TreeBatch, TreeGroupParts and EffectDeferRestore).
#include <cstddef>
static int g_instOn = 1;
static DWORD g_inRecords = 0, g_inDraws = 0, g_inFallback = 0, g_inGroups = 0, g_inGroupsBad = 0, g_inFlushes = 0;
static char g_inWhy[96] = "";

struct InEnv {                                   // per effect group: states that must be equal to share a draw
    DWORD rs[16]; DWORD ss[9];
    float L[4], dif[4], amb[4];                  // light direction (to the light) + lighting on; diffuse product; ambient term
    DWORD lightOn, normalize, fogOn, fogMode; float fogStart, fogEnd, fogDens; DWORD fogColor;
    float op[4];                                 // colour op, alpha op, alpha arg2 = tfactor
    BYTE lightRaw[104]; DWORD ambientRS;
    DWORD ttf;                                   // stage 0 texture transform: 0 = off, 2 = COUNT2 (matrix per key)
};
static const DWORD kInRS[16] = { 7, 23, 15, 25, 27, 19, 20, 171, 22, 168, 206, 195, 175, 8, 9, 0 };   // ZENABLE ZFUNC ATEST AFUNC ABLEND SRC DST BLENDOP CULL COLORWRITE SEPALPHA DEPTHBIAS SLOPEBIAS FILL SHADE
static const DWORD kInSS[9] = { 1, 2, 5, 6, 7, 8, 9, 10, 11 };
struct InKey {
    void* vb; DWORD off, stride; void* ib; void* tex; DWORD base, minIdx, numV, start, prim; DWORD zwrite, aref; int env;
    float tm[6];                                 // stage 0 texture matrix _11 _21 _31 / _12 _22 _32 (identity without TTF)
    BYTE mat[68]; DWORD hash; int first, count, next;
};
struct InInst { float c[12]; DWORD tf; int key; };
enum { IN_MAXENV = 32, IN_MAXKEY = 1024, IN_MAXINST = 16384 };
static InEnv g_inEnv[IN_MAXENV]; static int g_inEnvN = 0, g_inCurEnv = -1;
static InKey g_inKey[IN_MAXKEY]; static int g_inKeyN = 0;
static InInst g_inInst[IN_MAXINST]; static int g_inInstN = 0;
static void* g_inVS = nullptr; static void* g_inPS = nullptr; static void* g_inDecl = nullptr; static void* g_inVB = nullptr; static DWORD g_inVBCap = 0;
static bool g_inBroken = false;

#define DV(i, T) ((T)(*(void***)dev)[i])
typedef HRESULT (__stdcall *G_u_p_t)(void*, DWORD, void*);
static DWORD InRS(void* dev, DWORD s) { DWORD v = 0; DV(58, G_u_p_t)(dev, s, &v); return v; }
static DWORD InTSS(void* dev, DWORD st, DWORD t) { DWORD v = 0; ((HRESULT (__stdcall*)(void*, DWORD, DWORD, DWORD*))(*(void***)dev)[66])(dev, st, t, &v); return v; }
static inline void ColF(DWORD c, float* f) { f[0] = ((c >> 16) & 255) / 255.0f; f[1] = ((c >> 8) & 255) / 255.0f; f[2] = (c & 255) / 255.0f; f[3] = (c >> 24) / 255.0f; }
static bool InFail(const char* why) { snprintf(g_inWhy, sizeof g_inWhy, "%s", why); ++g_inGroupsBad; g_instGroupOk = false; return false; }

// called at the start of an effect group (after BeginPass): check the fixed-function state, remember it
static bool InstGroupBegin() {
    g_instGroupOk = false; g_inCurEnv = -1;
    if (!g_instOn || g_inBroken || !g_fxHooks) return false;
    void* dev = *pDevice; ++g_inGroups;
    InEnv e; memset(&e, 0, sizeof e);
    { void* p = nullptr; ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[93])(dev, &p); if (p) { ComRelease(p); return InFail("vertex shader"); } }
    { void* p = nullptr; ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[108])(dev, &p); if (p) { ComRelease(p); return InFail("pixel shader"); } }
    if (InRS(dev, 151) || InRS(dev, 167)) return InFail("vertex blend");
    if (InRS(dev, 152)) return InFail("clip planes");
    if (InRS(dev, 29)) return InFail("specular");
    if (InRS(dev, 52)) return InFail("stencil");
    if (InRS(dev, 128)) return InFail("wrap0");
    // stage 0 / 1
    DWORD cop = InTSS(dev, 0, 1), ca1 = InTSS(dev, 0, 2), ca2 = InTSS(dev, 0, 3), aop = InTSS(dev, 0, 4), aa1 = InTSS(dev, 0, 5), aa2 = InTSS(dev, 0, 6);
    {   DWORD tci = InTSS(dev, 0, 11), ttf = InTSS(dev, 0, 24), res = InTSS(dev, 0, 28);
        // TEXTURETRANSFORMFLAGS = COUNT2 is on for the trees in towns/forests (left by an earlier effect): the
        // texture matrix is applied in the shader, (u, v, 1) x rows 1..3 as the fixed-function pipeline does
        if (tci != 0 || (ttf != 0 && ttf != 2) || res != 1) {
            char w[80]; snprintf(w, sizeof w, "stage0 texcoordindex=%lX transformflags=%lX resultarg=%lX", tci, ttf, res); return InFail(w); } }
    e.ttf = InTSS(dev, 0, 24);
    if (InTSS(dev, 1, 1) != 1) return InFail("stage1 active");
    if (ca1 != 2 || (ca2 != 0 && ca2 != 1)) return InFail("stage0 colour args");
    if (cop == 2) e.op[0] = 0; else if (cop == 4) e.op[0] = 1; else if (cop == 5) e.op[0] = 2; else return InFail("stage0 colour op");
    if (aa1 != 2) return InFail("stage0 alpha arg1");
    if (aa2 == 3) e.op[2] = 1; else if (aa2 == 0 || aa2 == 1) e.op[2] = 0; else return InFail("stage0 alpha arg2");
    if (aop == 2) e.op[1] = 0; else if (aop == 4) e.op[1] = 1; else if (aop == 3) e.op[1] = 2; else return InFail("stage0 alpha op");
    // lighting
    e.lightOn = InRS(dev, 137) != 0; e.normalize = InRS(dev, 143) != 0; e.ambientRS = InRS(dev, 139);
    int nl = 0, li = -1;
    if (e.lightOn) for (int i = 0; i < 8; ++i) { BOOL on = FALSE; DV(54, G_u_p_t)(dev, i, &on); if (on) { ++nl; li = i; } }
    if (nl > 1) return InFail("several lights");
    if (nl == 1) {
        DV(52, G_u_p_t)(dev, li, e.lightRaw);
        if (*(DWORD*)e.lightRaw != 3) return InFail("non-directional light");
    }
    e.L[3] = e.lightOn ? 1.0f : 0.0f;
    for (int i = 0; i < 16; ++i) e.rs[i] = kInRS[i] ? InRS(dev, kInRS[i]) : 0;
    for (int i = 0; i < 9; ++i) { DWORD v = 0; ((HRESULT (__stdcall*)(void*, DWORD, DWORD, DWORD*))(*(void***)dev)[68])(dev, 0, kInSS[i], &v); e.ss[i] = v; }
    e.fogOn = InRS(dev, 28) != 0; e.fogColor = InRS(dev, 34);
    if (e.fogOn) {
        DWORD tm = InRS(dev, 35), vm = InRS(dev, 140);
        e.fogMode = tm ? tm : vm;
        if (!e.fogMode) e.fogOn = 0;
        DWORD v; v = InRS(dev, 36); memcpy(&e.fogStart, &v, 4); v = InRS(dev, 37); memcpy(&e.fogEnd, &v, 4); v = InRS(dev, 38); memcpy(&e.fogDens, &v, 4);
    }
    // the light part (material dependent terms are applied per key at the draw)
    if (nl == 1) {
        const float* d = (const float*)(e.lightRaw + 64);
        float l = sqrtf(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]); if (l <= 0) l = 1;
        e.L[0] = -d[0] / l; e.L[1] = -d[1] / l; e.L[2] = -d[2] / l;
    }
    int k = 0; for (; k < g_inEnvN; ++k) if (!memcmp(&g_inEnv[k], &e, sizeof e)) break;
    if (k == g_inEnvN) { if (g_inEnvN >= IN_MAXENV) return InFail("too many groups"); g_inEnv[g_inEnvN++] = e; }
    g_inCurEnv = k; g_instGroupOk = true;
    return true;
}
static void InRelease(InKey& k) { ComRelease(k.vb); ComRelease(k.ib); ComRelease(k.tex); k.vb = k.ib = k.tex = nullptr; }
// hp_DIP while g_instCapture: record the draw instead of issuing it; false = draw it normally
static bool InstCaptureDIP(void* dev, DWORD type, DWORD base, DWORD minIdx, DWORD numV, DWORD start, DWORD prim) {
    if (type != 4 || g_inCurEnv < 0 || !g_instMat || g_inInstN >= IN_MAXINST) { ++g_inFallback; return false; }
    DWORD fvf = 0;
    { DWORD f = 0; ((HRESULT (__stdcall*)(void*, DWORD*))(*(void***)dev)[90])(dev, &f); fvf = f; }
    if (fvf != 0x112) { ++g_inFallback; return false; }           // XYZ | NORMAL | TEX1
    InKey k; memset(&k, 0, sizeof k);
    ((HRESULT (__stdcall*)(void*, DWORD, void**, DWORD*, DWORD*))(*(void***)dev)[101])(dev, 0, &k.vb, &k.off, &k.stride);
    if (!k.vb || k.stride != 32) { ComRelease(k.vb); ++g_inFallback; return false; }
    ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[105])(dev, &k.ib);
    DV(64, G_u_p_t)(dev, 0, &k.tex);
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[50])(dev, k.mat);
    k.base = base; k.minIdx = minIdx; k.numV = numV; k.start = start; k.prim = prim;
    k.zwrite = InRS(dev, 14); k.aref = InRS(dev, 24); k.env = g_inCurEnv;
    if (g_inEnv[g_inCurEnv].ttf == 2) {
        float T[16]; DV(45, G_u_p_t)(dev, 16 /*D3DTS_TEXTURE0*/, T);
        k.tm[0] = T[0]; k.tm[1] = T[4]; k.tm[2] = T[8]; k.tm[3] = T[1]; k.tm[4] = T[5]; k.tm[5] = T[9];
    } else { k.tm[0] = 1; k.tm[1] = 0; k.tm[2] = 0; k.tm[3] = 0; k.tm[4] = 1; k.tm[5] = 0; }
    DWORD h = 2166136261u; const DWORD* w = (const DWORD*)&k;
    for (size_t i = 0; i < offsetof(InKey, hash) / 4; ++i) h = (h ^ w[i]) * 16777619u;
    k.hash = h;
    int ki = -1;
    for (int i = g_inKeyN - 1; i >= 0; --i) if (g_inKey[i].hash == h && !memcmp(&g_inKey[i], &k, offsetof(InKey, hash))) { ki = i; break; }
    if (ki < 0) {
        if (g_inKeyN >= IN_MAXKEY) { InRelease(k); ++g_inFallback; return false; }
        k.first = -1; k.count = 0; k.next = -1; ki = g_inKeyN; g_inKey[g_inKeyN++] = k;
    } else InRelease(k);                                            // the key already holds the references
    InInst& in = g_inInst[g_inInstN++];
    const float* m = g_instMat;                                     // row-major world: store its columns
    for (int c = 0; c < 3; ++c) { in.c[c * 4 + 0] = m[c]; in.c[c * 4 + 1] = m[4 + c]; in.c[c * 4 + 2] = m[8 + c]; in.c[c * 4 + 3] = m[12 + c]; }
    in.tf = InRS(dev, 60); in.key = ki;
    ++g_inKey[ki].count; ++g_inRecords;
    return true;
}
static const char* kInVS =
    "float4 vp0:register(c0); float4 vp1:register(c1); float4 vp2:register(c2); float4 vp3:register(c3);\n"
    "float4 L:register(c4); float4 dif:register(c5); float4 amb:register(c6); float4 vz:register(c7); float4 opt:register(c8);\n"
    "float4 tmu:register(c9); float4 tmv:register(c10);\n"
    "struct I { float3 p:POSITION; float3 n:NORMAL; float2 t:TEXCOORD0; float4 w0:TEXCOORD1; float4 w1:TEXCOORD2; float4 w2:TEXCOORD3; float4 tf:COLOR0; };\n"
    "struct O { float4 p:POSITION; float2 t:TEXCOORD0; float4 c:COLOR0; float4 tf:COLOR1; float z:TEXCOORD1; };\n"
    "O main(I i) { O o; float4 p = float4(i.p, 1);\n"
    "  float4 w = float4(dot(p, i.w0), dot(p, i.w1), dot(p, i.w2), 1);\n"
    "  o.p = float4(dot(w, vp0), dot(w, vp1), dot(w, vp2), dot(w, vp3));\n"
    "  float3 n = float3(dot(i.n, i.w0.xyz), dot(i.n, i.w1.xyz), dot(i.n, i.w2.xyz));\n"
    "  if (opt.x > 0) n = normalize(n);\n"
    "  float3 c = amb.rgb + dif.rgb * max(0, dot(n, L.xyz));\n"
    "  o.c = L.w > 0 ? float4(saturate(c), dif.a) : float4(1, 1, 1, 1);\n"
    "  float3 t3 = float3(i.t, 1); o.t = float2(dot(t3, tmu.xyz), dot(t3, tmv.xyz)); o.tf = i.tf; o.z = dot(w, vz); return o; }\n";
static const char* kInPS =
    "sampler s0:register(s0); float4 fogc:register(c0); float4 fogp:register(c1); float4 op:register(c2);\n"
    "float4 main(float2 t:TEXCOORD0, float4 c:COLOR0, float4 tf:COLOR1, float z:TEXCOORD1) : COLOR {\n"
    "  float4 x = tex2D(s0, t);\n"
    "  float3 rgb = op.x < 0.5 ? x.rgb : saturate(x.rgb * c.rgb * op.x);\n"
    "  float a2 = op.z > 0.5 ? tf.a : c.a;\n"
    "  float a = op.y < 0.5 ? x.a : (op.y < 1.5 ? x.a * a2 : a2);\n"
    "  if (fogc.w > 0.5) { float f; if (fogp.w > 2.5) f = (fogp.y - z) / (fogp.y - fogp.x); else if (fogp.w > 1.5) { float q = fogp.z * z; f = exp(-q * q); } else f = exp(-fogp.z * z);\n"
    "    rgb = lerp(fogc.rgb, rgb, saturate(f)); }\n"
    "  return float4(rgb, a); }\n";
typedef HRESULT (WINAPI *D3DXCompileShader_t)(const char*, UINT, const void*, void*, const char*, const char*, DWORD, void**, void**, void**);
static void* InCompile(void* dev, const char* src, const char* prof, bool vs) {
    HMODULE m = GetModuleHandleA("d3dx9_29.dll");
    D3DXCompileShader_t c = m ? (D3DXCompileShader_t)GetProcAddress(m, "D3DXCompileShader") : nullptr;
    if (!c) { LOG("instancing: D3DXCompileShader not found"); return nullptr; }
    void* code = nullptr; void* err = nullptr;
    HRESULT hr = c(src, (UINT)strlen(src), nullptr, nullptr, "main", prof, 0, &code, &err, nullptr);
    if (hr < 0 || !code) {
        LOG("instancing: %s compile failed %08lX: %s", prof, hr, err ? (const char*)((void* (__stdcall*)(void*))(*(void***)err)[3])(err) : "?");
        ComRelease(err); return nullptr;
    }
    ComRelease(err);
    const DWORD* fn = (const DWORD*)((void* (__stdcall*)(void*))(*(void***)code)[3])(code);
    void* sh = nullptr;
    HRESULT h2 = ((HRESULT (__stdcall*)(void*, const DWORD*, void**))(*(void***)dev)[vs ? 91 : 106])(dev, fn, &sh);
    ComRelease(code);
    if (h2 < 0) { LOG("instancing: Create%sShader failed %08lX", vs ? "Vertex" : "Pixel", h2); return nullptr; }
    return sh;
}
static bool InEnsure(void* dev, DWORD need) {
    if (!g_inVS) g_inVS = InCompile(dev, kInVS, "vs_3_0", true);
    if (!g_inPS) g_inPS = InCompile(dev, kInPS, "ps_3_0", false);
    if (!g_inDecl) {
        struct E { WORD s, o; BYTE t, m, u, ui; } el[] = {
            { 0, 0, 2, 0, 0, 0 }, { 0, 12, 2, 0, 3, 0 }, { 0, 24, 1, 0, 5, 0 },
            { 1, 0, 3, 0, 5, 1 }, { 1, 16, 3, 0, 5, 2 }, { 1, 32, 3, 0, 5, 3 }, { 1, 48, 4, 0, 10, 0 },
            { 0xFF, 0, 17, 0, 0, 0 } };
        if (((HRESULT (__stdcall*)(void*, const void*, void**))(*(void***)dev)[86])(dev, el, &g_inDecl) < 0) g_inDecl = nullptr;
    }
    if (!g_inVS || !g_inPS || !g_inDecl) { g_inBroken = true; LOG("instancing: unavailable (shaders/declaration)"); return false; }
    if (need > g_inVBCap) {
        ComRelease(g_inVB); g_inVB = nullptr; g_inVBCap = 0;
        DWORD cap = 4096; while (cap < need) cap *= 2;
        if (((HRESULT (__stdcall*)(void*, UINT, DWORD, DWORD, DWORD, void**, void*))(*(void***)dev)[26])(dev, cap * 52, 0x208 /*DYNAMIC|WRITEONLY*/, 0, 0 /*DEFAULT*/, &g_inVB, nullptr) < 0) {
            g_inVB = nullptr; g_inBroken = true; LOG("instancing: instance buffer creation failed"); return false;
        }
        g_inVBCap = cap;
    }
    return true;
}
static void InClear() { for (int i = 0; i < g_inKeyN; ++i) InRelease(g_inKey[i]); g_inKeyN = 0; g_inInstN = 0; g_inEnvN = 0; g_inCurEnv = -1; }
static void InstRelease() { InClear(); ComRelease(g_inVB); g_inVB = nullptr; g_inVBCap = 0; }   // device reset (the shaders survive)
// draw everything recorded in this phase
static void InstFlush() {
    if (!g_inInstN) { InClear(); return; }
    void* dev = *pDevice; ++g_inFlushes;
    if (!InEnsure(dev, (DWORD)g_inInstN)) { InClear(); return; }
    // instance data grouped by key (record order kept inside a key)
    static int slot[IN_MAXKEY]; int pos = 0;
    for (int k = 0; k < g_inKeyN; ++k) { slot[k] = pos; g_inKey[k].first = pos; pos += g_inKey[k].count; }
    BYTE* p = nullptr;
    if (((HRESULT (__stdcall*)(void*, UINT, UINT, void**, DWORD))(*(void***)g_inVB)[11])(g_inVB, 0, g_inInstN * 52, (void**)&p, 0x2000 /*DISCARD*/) < 0 || !p) { InClear(); return; }
    for (int i = 0; i < g_inInstN; ++i) { InInst& in = g_inInst[i]; BYTE* d = p + (slot[in.key]++) * 52; memcpy(d, in.c, 48); memcpy(d + 48, &in.tf, 4); }
    ((HRESULT (__stdcall*)(void*))(*(void***)g_inVB)[12])(g_inVB);
    // save what is changed here
    void *oVS = nullptr, *oPS = nullptr, *oDecl = nullptr, *oVB0 = nullptr, *oVB1 = nullptr, *oIB = nullptr, *oTex = nullptr;
    DWORD oOff0 = 0, oStr0 = 0, oOff1 = 0, oStr1 = 0, oF0 = 1, oF1 = 1, oFVF = 0;
    ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[93])(dev, &oVS);
    ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[108])(dev, &oPS);
    ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[88])(dev, &oDecl);
    ((HRESULT (__stdcall*)(void*, DWORD*))(*(void***)dev)[90])(dev, &oFVF);
    ((HRESULT (__stdcall*)(void*, DWORD, void**, DWORD*, DWORD*))(*(void***)dev)[101])(dev, 0, &oVB0, &oOff0, &oStr0);
    ((HRESULT (__stdcall*)(void*, DWORD, void**, DWORD*, DWORD*))(*(void***)dev)[101])(dev, 1, &oVB1, &oOff1, &oStr1);
    ((HRESULT (__stdcall*)(void*, DWORD, DWORD*))(*(void***)dev)[103])(dev, 0, &oF0);
    ((HRESULT (__stdcall*)(void*, DWORD, DWORD*))(*(void***)dev)[103])(dev, 1, &oF1);
    ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[105])(dev, &oIB);
    DV(64, G_u_p_t)(dev, 0, &oTex);
    DWORD oRS[16], oSS[9], oZW = InRS(dev, 14), oAR = InRS(dev, 24);
    for (int i = 0; i < 16; ++i) oRS[i] = kInRS[i] ? InRS(dev, kInRS[i]) : 0;
    for (int i = 0; i < 9; ++i) ((HRESULT (__stdcall*)(void*, DWORD, DWORD, DWORD*))(*(void***)dev)[68])(dev, 0, kInSS[i], &oSS[i]);
    // view-projection columns and view depth
    float V[16], P[16], VP[16];
    DV(45, G_u_p_t)(dev, 2, V); DV(45, G_u_p_t)(dev, 3, P);
    for (int r = 0; r < 4; ++r) for (int c = 0; c < 4; ++c) { float s = 0; for (int k = 0; k < 4; ++k) s += V[r * 4 + k] * P[k * 4 + c]; VP[r * 4 + c] = s; }
    float vc[20];
    for (int c = 0; c < 4; ++c) for (int r = 0; r < 4; ++r) vc[c * 4 + r] = VP[r * 4 + c];
    for (int r = 0; r < 4; ++r) vc[16 + r] = V[r * 4 + 2];
    typedef HRESULT (__stdcall *SC_t)(void*, UINT, const float*, UINT);
    ((SC_t)(*(void***)dev)[94])(dev, 0, vc, 4);
    ((SC_t)(*(void***)dev)[94])(dev, 7, vc + 16, 1);
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[87])(dev, g_inDecl);
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[92])(dev, g_inVS);
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[107])(dev, g_inPS);
    ((HRESULT (__stdcall*)(void*, DWORD, void*, DWORD, DWORD))(*(void***)dev)[100])(dev, 1, g_inVB, 0, 52);
    typedef HRESULT (__stdcall *DIP_t2)(void*, DWORD, INT, UINT, UINT, UINT, UINT);
    DIP_t2 dip = (DIP_t2)g_fxO[82];                                 // the device's own DrawIndexedPrimitive (past our hooks)
    int curEnv = -1;
    for (int k = 0; k < g_inKeyN; ++k) {
        InKey& K = g_inKey[k]; const InEnv& e = g_inEnv[K.env];
        if (K.env != curEnv) {
            curEnv = K.env;
            for (int i = 0; i < 16; ++i) if (kInRS[i]) DEVF(57, D_u_u)(dev, kInRS[i], e.rs[i]);
            for (int i = 0; i < 9; ++i) DEVF(69, D_u_u_u)(dev, 0, kInSS[i], e.ss[i]);
            float pc[12]; float fc[4]; ColF(e.fogColor, fc);
            pc[0] = fc[0]; pc[1] = fc[1]; pc[2] = fc[2]; pc[3] = e.fogOn ? 1.0f : 0.0f;
            pc[4] = e.fogStart; pc[5] = e.fogEnd; pc[6] = e.fogDens; pc[7] = (float)e.fogMode;
            pc[8] = e.op[0]; pc[9] = e.op[1]; pc[10] = e.op[2]; pc[11] = 0;
            ((SC_t)(*(void***)dev)[109])(dev, 0, pc, 3);
        }
        // material dependent lighting terms (fixed-function: emissive + Am*(Ga + La) + Dm*Ld*max(N.L,0); alpha = Dm.a)
        const float* Dm = (const float*)K.mat; const float* Am = Dm + 4; const float* Em = Dm + 12;
        float ga[4]; ColF(e.ambientRS, ga);
        const float* Ld = (const float*)(e.lightRaw + 4); const float* La = (const float*)(e.lightRaw + 36);
        bool hasLight = *(DWORD*)e.lightRaw == 3;
        float c[16];
        c[0] = e.L[0]; c[1] = e.L[1]; c[2] = e.L[2]; c[3] = e.L[3];
        for (int i = 0; i < 3; ++i) c[4 + i] = hasLight ? Dm[i] * Ld[i] : 0.0f;
        c[7] = Dm[3];
        for (int i = 0; i < 3; ++i) c[8 + i] = Em[i] + Am[i] * (ga[i] + (hasLight ? La[i] : 0.0f));
        c[11] = 1;
        c[12] = e.normalize ? 1.0f : 0.0f; c[13] = c[14] = c[15] = 0;
        ((SC_t)(*(void***)dev)[94])(dev, 4, c, 3);
        ((SC_t)(*(void***)dev)[94])(dev, 8, c + 12, 1);
        {   float t[8] = { K.tm[0], K.tm[1], K.tm[2], 0, K.tm[3], K.tm[4], K.tm[5], 0 };
            ((SC_t)(*(void***)dev)[94])(dev, 9, t, 2); }
        DEVF(57, D_u_u)(dev, 14, K.zwrite); DEVF(57, D_u_u)(dev, 24, K.aref);
        ((HRESULT (__stdcall*)(void*, DWORD, void*, DWORD, DWORD))(*(void***)dev)[100])(dev, 0, K.vb, K.off, K.stride);
        ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[104])(dev, K.ib);
        DEVF(65, D_u_p)(dev, 0, K.tex);
        ((HRESULT (__stdcall*)(void*, DWORD, DWORD))(*(void***)dev)[102])(dev, 0, 0x40000000u | (DWORD)K.count);   // INDEXEDDATA | n
        ((HRESULT (__stdcall*)(void*, DWORD, DWORD))(*(void***)dev)[102])(dev, 1, 0x80000000u | 1u);               // INSTANCEDATA
        ((HRESULT (__stdcall*)(void*, DWORD, void*, DWORD, DWORD))(*(void***)dev)[100])(dev, 1, g_inVB, K.first * 52, 52);
        dip(dev, 4, (INT)K.base, K.minIdx, K.numV, K.start, K.prim);
        ++g_inDraws;
    }
    // restore
    ((HRESULT (__stdcall*)(void*, DWORD, DWORD))(*(void***)dev)[102])(dev, 0, oF0);
    ((HRESULT (__stdcall*)(void*, DWORD, DWORD))(*(void***)dev)[102])(dev, 1, oF1);
    ((HRESULT (__stdcall*)(void*, DWORD, void*, DWORD, DWORD))(*(void***)dev)[100])(dev, 1, oVB1, oOff1, oStr1);
    ((HRESULT (__stdcall*)(void*, DWORD, void*, DWORD, DWORD))(*(void***)dev)[100])(dev, 0, oVB0, oOff0, oStr0);
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[104])(dev, oIB);
    DEVF(65, D_u_p)(dev, 0, oTex);
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[92])(dev, oVS);
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[107])(dev, oPS);
    if (oDecl) ((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[87])(dev, oDecl);
    if (oFVF) DEVF(89, D_u)(dev, oFVF);
    for (int i = 0; i < 16; ++i) if (kInRS[i]) DEVF(57, D_u_u)(dev, kInRS[i], oRS[i]);
    for (int i = 0; i < 9; ++i) DEVF(69, D_u_u_u)(dev, 0, kInSS[i], oSS[i]);
    DEVF(57, D_u_u)(dev, 14, oZW); DEVF(57, D_u_u)(dev, 24, oAR);
    ComRelease(oVS); ComRelease(oPS); ComRelease(oDecl); ComRelease(oVB0); ComRelease(oVB1); ComRelease(oIB); ComRelease(oTex);
    InClear();
}
static void InstanceStats() {
    PLOG("INSTANCING on=%d: recorded=%lu instanced draws=%lu (flushes %lu) fallback draws=%lu | groups=%lu rejected=%lu%s%s",
         g_instOn && !g_inBroken, g_inRecords, g_inDraws, g_inFlushes, g_inFallback, g_inGroups, g_inGroupsBad, g_inWhy[0] ? " last reason: " : "", g_inWhy);
    g_inRecords = g_inDraws = g_inFlushes = g_inFallback = g_inGroups = g_inGroupsBad = 0;
}
#undef DV

// ---------------------------------------------------------------- quality settings for the in-game options page (1.1.2)
// Lua: AttTFix_GetQuality() -> objectDist, treeDist, treeFade (0/1/2), aniso (0 = off), msaa (0 = off)
//      AttTFix_SetQuality(objectDist, treeDist, treeFade, aniso, msaa): applied at once and saved to AttTFix.ini
static int L_GetQuality(void* L) {
    LPushNum(L, g_objDist); LPushNum(L, g_treeDist); LPushNum(L, (float)g_dissolve);
    LPushNum(L, g_anisoOn ? (float)(g_aniso > 1 ? g_aniso : 0) : 0.0f);
    LPushNum(L, g_msaaOn ? (float)g_msaa : 0.0f);
    LPushNum(L, g_tree3D);
    return 6;
}
static int L_SetQuality(void* L) {
    float od = LNum(L, 1), td = LNum(L, 2); int fade = (int)LNum(L, 3), an = (int)LNum(L, 4), ms = (int)LNum(L, 5);
    float t3 = LNum(L, 6); if (t3 >= 0 && t3 <= 20000) g_tree3D = t3;
    if (od >= 0.5f && od <= 10.0f) g_objDist = od;
    if (td >= 0.5f && td <= 10.0f) g_treeDist = td;
    g_objDistOn = 1; ObjDistApplyShadows();
    if (fade >= 0 && fade <= 2) g_dissolve = fade;
    if (an >= 2) { g_aniso = an; g_anisoOn = 1; } else g_anisoOn = 0;
    if (*pDevice) AnisoApply(*pDevice);
    bool on = ms >= 2;
    if (on != (g_msaaOn != 0) || (on && ms != g_msaa)) {
        if (on) g_msaa = ms; g_msaaOn = on;
        // the live switch re-creates the device through the engine's restore; the system d3d9 refused that
        // (D3DERR_INVALIDCALL, the game quit): there it is applied on the next start
        if (g_dxvkActive) g_msaaResetPending = true; else LOG("options: MSAA change applies on the next start (system d3d9)");
    }
    char b[64];
    snprintf(b, sizeof b, "%.1f", g_objDist); WritePrivateProfileStringA("Video", "ObjectDistance", b, g_iniPath);
    snprintf(b, sizeof b, "%.1f", g_treeDist); WritePrivateProfileStringA("Video", "TreeDistance", b, g_iniPath);
    snprintf(b, sizeof b, "%d", g_dissolve); WritePrivateProfileStringA("Video", "TreeDissolve", b, g_iniPath);
    snprintf(b, sizeof b, "%d", g_anisoOn ? g_aniso : 0); WritePrivateProfileStringA("Video", "Anisotropy", b, g_iniPath);
    snprintf(b, sizeof b, "%d", g_msaaOn ? g_msaa : 0); WritePrivateProfileStringA("Video", "MSAA", b, g_iniPath);
    snprintf(b, sizeof b, "%.0f", g_tree3D); WritePrivateProfileStringA("Video", "Tree3DDistance", b, g_iniPath);
    LOG("options: quality objects x%.1f trees x%.1f 3D trees to %.0f fade %d aniso %d msaa %d", g_objDist, g_treeDist, g_tree3D, g_dissolve, g_anisoOn ? g_aniso : 0, g_msaaOn ? g_msaa : 0);
    return 0;
}
// Lua: AttTFix_GetRenderer() -> setting (0 = d3d9, 1 = dxvk), active, dxvk available (LAA exe + dxvk\d3d9.dll)
//      AttTFix_SetRenderer(v): saved to AttTFix.ini, used on the next start
static int L_GetRenderer(void* L) {
    char t[32]; GetPrivateProfileStringA("Video", "Renderer", "d3d9", t, sizeof t, g_iniPath);
    auto nt = (IMAGE_NT_HEADERS*)((BYTE*)GetModuleHandleA(nullptr) + ((IMAGE_DOS_HEADER*)GetModuleHandleA(nullptr))->e_lfanew);
    char p[MAX_PATH]; snprintf(p, sizeof p, "%sdxvk\\d3d9.dll", g_dir);
    bool avail = (nt->FileHeader.Characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE) && GetFileAttributesA(p) != INVALID_FILE_ATTRIBUTES;
    LPushNum(L, !_strnicmp(t, "dxvk", 4) ? 1.0f : 0.0f); LPushNum(L, (float)g_dxvkActive); LPushNum(L, avail ? 1.0f : 0.0f);
    return 3;
}
static int L_SetRenderer(void* L) {
    bool dx = LNum(L, 1) != 0;
    WritePrivateProfileStringA("Video", "Renderer", dx ? "dxvk  ; d3d9 = system Direct3D 9, dxvk = DXVK (Vulkan) from the dxvk folder"
                                                       : "d3d9  ; d3d9 = system Direct3D 9, dxvk = DXVK (Vulkan) from the dxvk folder", g_iniPath);
    LOG("options: renderer %s (next start)", dx ? "dxvk" : "d3d9");
    return 0;
}
static int L_GetTreeView(void* L) { LPushNum(L, TreeViewDistance()); return 1; }
