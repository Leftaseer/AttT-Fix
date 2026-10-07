// ---------------------------------------------------------------- render optimizations (1.0.3)
// Included into attfix.cpp after pDevice / Now() / g_tickMs are defined.
//
// 1) Sun occlusion test (CSun 0x535850, used by CFlares 0x52B420 / 0x52B1F0).
//    The original locks the WHOLE lockable back buffer twice per frame (sun on screen) to read one pixel:
//    the CPU waits for the GPU and the driver copies the full surface (33 MB at 4K).
//    Here: StretchRect of that pixel into a small lockable render target, read 2-3 frames later with
//    D3DLOCK_DONOTWAIT -> no stall. Same colour test as the original.
// 2) Forest trees (TreeMassive::Render tail -> 0x55C690 -> ForestTree 0x455CF0 -> 0x4558C0 / 0x455960).
//    Each tree draws two effect techniques (Trunk, Foliage), each Begin(0)/End() saving and restoring the
//    states the technique touches. Here the techniques run with D3DXFX_DONOTSAVESTATE through a state manager
//    that records the original values once per tree loop and restores exactly what the original End() would
//    have restored at the moment it matters (states not set by the next pass, and everything at the end).
static int g_optSun = 1, g_optTrees = 1;          // [Perf] AsyncSunCheck, TreeBatch; F7 toggles both
static double g_frSun = 0, g_frTrees = 0; static int g_frTreeN = 0;   // per-frame accumulators
static double g_ovSun = 0, g_ovTrees = 0, g_ovTreeN = 0;              // overlay averages
static DWORD g_sunCopies = 0, g_sunReads = 0, g_sunBusy = 0, g_sunSync = 0, g_treeLoops = 0, g_treeDraws = 0;

#define DEVF(i, T) ((T)(*(void***)dev)[i])
typedef HRESULT (__stdcall *D_u_u)(void*, DWORD, DWORD);
typedef HRESULT (__stdcall *D_u_p)(void*, DWORD, void*);
typedef HRESULT (__stdcall *D_p)(void*, void*);
typedef HRESULT (__stdcall *D_u)(void*, DWORD);
typedef HRESULT (__stdcall *D_u_u_u)(void*, DWORD, DWORD, DWORD);
typedef HRESULT (__stdcall *D_u_u_p)(void*, DWORD, DWORD, void*);
typedef HRESULT (__stdcall *D_u_p_u)(void*, DWORD, const void*, DWORD);
typedef ULONG   (__stdcall *Rel_t)(void*);
static inline void ComRelease(void* p) { if (p) ((Rel_t)(*(void***)p)[2])(p); }

// ---------------------------------------------------------------- 1) sun
typedef int (__fastcall *SunTest_t)(BYTE* sun, void* edx);
static SunTest_t o_SunTest = nullptr;
enum { SUN_SLOTS = 3 };
static void* g_sunRT[SUN_SLOTS]; static DWORD g_sunSlotFrame[SUN_SLOTS]; static bool g_sunSlotValid[SUN_SLOTS];
static BYTE g_sunPx[4]; static bool g_sunHave = false; static DWORD g_sunFrame = 0xFFFFFFFF, g_sunSeq = 0; static bool g_sunBroken = false;
static void SunRelease() {
    for (int i = 0; i < SUN_SLOTS; ++i) { ComRelease(g_sunRT[i]); g_sunRT[i] = nullptr; g_sunSlotValid[i] = false; }
    g_sunHave = false;
}
struct SurfDesc { DWORD Format, Type, Usage, Pool, MS, MSQ; UINT W, H; };
struct LockedRect { INT Pitch; void* pBits; };
static void SunSample(BYTE* sun) {
    void* dev = *pDevice; void* bb = *(void**)(sun + 0x78);
    if (!dev || !bb) return;
    void** svt = *(void***)bb;
    // read finished copies, oldest first
    for (int age = SUN_SLOTS - 1; age >= 1; --age) {
        int s = (int)((g_sunSeq + SUN_SLOTS * 4 - age) % SUN_SLOTS);
        if (!g_sunSlotValid[s] || g_sunSlotFrame[s] != g_sunSeq - age) { g_sunSlotValid[s] = false; continue; }
        void* rt = g_sunRT[s]; LockedRect lr;
        HRESULT hr = ((HRESULT (__stdcall*)(void*, LockedRect*, const RECT*, DWORD))(*(void***)rt)[13])(rt, &lr, nullptr, 0x10 /*READONLY*/ | 0x4000 /*DONOTWAIT*/);
        if (hr == (HRESULT)0x8876021C) { ++g_sunBusy; break; }               // D3DERR_WASSTILLDRAWING: newer ones aren't ready either
        g_sunSlotValid[s] = false;
        if (hr < 0) continue;
        memcpy(g_sunPx, lr.pBits, 4); g_sunHave = true; ++g_sunReads;
        ((HRESULT (__stdcall*)(void*))(*(void***)rt)[14])(rt);
    }
    // copy the current pixel
    int s = (int)(g_sunSeq % SUN_SLOTS);
    SurfDesc d; if (((HRESULT (__stdcall*)(void*, SurfDesc*))svt[12])(bb, &d) < 0) return;
    if (!g_sunRT[s]) {
        // CreateRenderTarget(W, H, Format, MultiSample, Quality, Lockable, ppSurface, pSharedHandle) = 28
        HRESULT hr = ((HRESULT (__stdcall*)(void*, UINT, UINT, DWORD, DWORD, DWORD, BOOL, void**, void*))(*(void***)dev)[28])(dev, 1, 1, d.Format, 0, 0, TRUE, &g_sunRT[s], nullptr);
        if (hr < 0) { LOG("sun: CreateRenderTarget fmt=%lu failed %08lX -> original sun test", d.Format, hr); g_sunBroken = true; g_sunRT[s] = nullptr; return; }
    }
    int x = *(int*)(sun + 0x88), y = *(int*)(sun + 0x8C);
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x >= (int)d.W) x = d.W - 1;
    if (y >= (int)d.H) y = d.H - 1;
    RECT r = { x, y, x + 1, y + 1 };
    // StretchRect(src, srcRect, dst, dstRect, filter) = 34
    HRESULT hr = ((HRESULT (__stdcall*)(void*, void*, const RECT*, void*, const RECT*, DWORD))(*(void***)dev)[34])(dev, bb, &r, g_sunRT[s], nullptr, 0);
    if (hr < 0) { LOG("sun: StretchRect failed %08lX -> original sun test", hr); g_sunBroken = true; return; }
    g_sunSlotValid[s] = true; g_sunSlotFrame[s] = g_sunSeq; ++g_sunCopies;
}
static int __fastcall h_SunTest(BYTE* sun, void* edx) {
    LONGLONG t0 = Now(); int r;
    if (!g_optSun || g_sunBroken) { ++g_sunSync; g_sunLockCtx = sun; r = o_SunTest(sun, edx); g_sunLockCtx = nullptr; }
    else if (*(int*)(sun + 0xB0) == 2) {                               // sun off screen
        r = 2; g_sunHave = false; for (int i = 0; i < SUN_SLOTS; ++i) g_sunSlotValid[i] = false;
    } else {
        if (g_sunFrame != g_frames) { g_sunFrame = g_frames; ++g_sunSeq; SunSample(sun); }   // called twice per frame: sample once
        if (g_sunBroken) { ++g_sunSync; g_sunLockCtx = sun; r = o_SunTest(sun, edx); g_sunLockCtx = nullptr; }
        else if (!g_sunHave) r = 1;                                    // no result yet: treat as occluded (flare stays faded)
        else {
            r = 0; int tol = *(int*)(sun + 0xB4); BYTE tb = (BYTE)tol;
            for (int i = 0; i < 3; ++i) {                              // same test as the original (byte arithmetic included)
                BYTE c = g_sunPx[i], hi = ((int)c + tol > 0xFF) ? 0xFF : (BYTE)(tb + c), lo = (BYTE)(c - tb), ref = sun[0x94 + i];
                if (ref < lo || ref > hi) { r = 1; break; }
            }
        }
    }
    g_frSun += (Now() - t0) * g_tickMs;
    return r;
}

// ---------------------------------------------------------------- 2) trees: effect state manager
struct SMEntry { DWORD key; BYTE n; bool touched, needRestore; void* ref; BYTE s0[104]; };
enum { SM_RS = 1, SM_TSS, SM_SS, SM_LE, SM_TEX, SM_FVF, SM_VS, SM_PS, SM_XF, SM_MAT, SM_LIGHT, SM_NP, SM_VCF, SM_VCI, SM_VCB, SM_PCF, SM_PCI, SM_PCB };
enum { SM_MAX = 256 };
static SMEntry g_sm[SM_MAX]; static int g_smN = 0; static bool g_smOverflow = false;
static void* g_smFx[16]; static void* g_smOld[16]; static int g_smFxN = 0;
static bool g_treeLoop = false;
static inline DWORD SMKey(int type, DWORD a, DWORD b) { return ((DWORD)type << 24) | ((a & 0x3FF) << 14) | (b & 0x3FFF); }

static void SMRestore(void* dev, SMEntry& e) {   // set the saved original value directly on the device
    DWORD type = e.key >> 24, a = (e.key >> 14) & 0x3FF, b = e.key & 0x3FFF; DWORD v = *(DWORD*)e.s0;
    switch (type) {
    case SM_RS:   DEVF(57, D_u_u)(dev, b, v); break;
    case SM_TSS:  DEVF(67, D_u_u_u)(dev, a, b, v); break;
    case SM_SS:   DEVF(69, D_u_u_u)(dev, a, b, v); break;
    case SM_LE:   DEVF(53, D_u_u)(dev, b, v); break;
    case SM_TEX:  DEVF(65, D_u_p)(dev, b, e.ref); break;
    case SM_FVF:  if (v) DEVF(89, D_u)(dev, v); else if (e.ref) DEVF(87, D_p)(dev, e.ref); break;   // FVF 0: a declaration was set
    case SM_VS:   DEVF(92, D_p)(dev, e.ref); break;
    case SM_PS:   DEVF(107, D_p)(dev, e.ref); break;
    case SM_XF:   DEVF(44, D_u_p)(dev, b, e.s0); break;
    case SM_MAT:  DEVF(49, D_p)(dev, e.s0); break;
    case SM_LIGHT: if (e.n) DEVF(51, D_u_p)(dev, b, e.s0); break;
    case SM_NP:   ((HRESULT (__stdcall*)(void*, float))(*(void***)dev)[79])(dev, *(float*)e.s0); break;
    case SM_VCF:  DEVF(94, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_VCI:  DEVF(96, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_VCB:  DEVF(98, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_PCF:  DEVF(109, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_PCI:  DEVF(111, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_PCB:  DEVF(113, D_u_p_u)(dev, b, e.s0, 1); break;
    }
}
// first touch in this tree loop: remember the current device value
static SMEntry* SMTouch(int type, DWORD a, DWORD b) {
    DWORD key = SMKey(type, a, b);
    for (int i = 0; i < g_smN; ++i) if (g_sm[i].key == key) { g_sm[i].touched = g_sm[i].needRestore = true; return &g_sm[i]; }
    if (g_smN >= SM_MAX) { g_smOverflow = true; return nullptr; }
    SMEntry& e = g_sm[g_smN++]; e.key = key; e.n = 1; e.ref = nullptr; e.touched = e.needRestore = true; memset(e.s0, 0, sizeof e.s0);
    void* dev = *pDevice;
    switch (type) {
    case SM_RS:   DEVF(58, D_u_p)(dev, b, e.s0); break;
    case SM_TSS:  DEVF(66, D_u_u_p)(dev, a, b, e.s0); break;
    case SM_SS:   DEVF(68, D_u_u_p)(dev, a, b, e.s0); break;
    case SM_LE:   DEVF(54, D_u_p)(dev, b, e.s0); break;
    case SM_TEX:  DEVF(64, D_u_p)(dev, b, &e.ref); break;
    case SM_FVF:  DEVF(90, D_p)(dev, e.s0); break;
    case SM_VS:   DEVF(93, D_p)(dev, &e.ref); break;
    case SM_PS:   DEVF(108, D_p)(dev, &e.ref); break;
    case SM_XF:   DEVF(45, D_u_p)(dev, b, e.s0); break;
    case SM_MAT:  DEVF(50, D_p)(dev, e.s0); break;
    case SM_LIGHT: e.n = DEVF(52, D_u_p)(dev, b, e.s0) >= 0; break;
    case SM_NP:   *(float*)e.s0 = ((float (__stdcall*)(void*))(*(void***)dev)[80])(dev); break;
    case SM_VCF:  DEVF(95, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_VCI:  DEVF(97, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_VCB:  DEVF(99, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_PCF:  DEVF(110, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_PCI:  DEVF(112, D_u_p_u)(dev, b, e.s0, 1); break;
    case SM_PCB:  DEVF(114, D_u_p_u)(dev, b, e.s0, 1); break;
    }
    return &e;
}
// The original End() of the previous technique restored everything it had touched before this technique's
// first pass. Emulated lazily: after BeginPass(0), states set earlier but not by this pass go back to their
// original values; states this pass sets are already correct (passes > 0 see leftovers, as in the original).
static void SMClearTouched() { for (int i = 0; i < g_smN; ++i) g_sm[i].touched = false; }
static void SMPassBegun() {
    void* dev = *pDevice;
    for (int i = 0; i < g_smN; ++i) {
        SMEntry& e = g_sm[i];
        if (!e.touched && e.needRestore) { SMRestore(dev, e); e.needRestore = false; }
    }
}
static void SMEndLoop() {
    void* dev = *pDevice;
    for (int i = 0; i < g_smN; ++i) { if (g_sm[i].needRestore) SMRestore(dev, g_sm[i]); ComRelease(g_sm[i].ref); }
    g_smN = 0;
}
// ID3DXEffectStateManager implementation (COM, stdcall)
struct StateMgr { void** vt; };
static StateMgr g_stateMgr;
#define SMDEV void* dev = *pDevice
static HRESULT __stdcall SM_QI(StateMgr* t, const GUID*, void** o) { *o = t; return S_OK; }
static ULONG __stdcall SM_AddRef(StateMgr*) { return 1; }
static ULONG __stdcall SM_Release(StateMgr*) { return 1; }
static HRESULT __stdcall SM_SetTransform(StateMgr*, DWORD s, const void* m) { SMDEV; SMTouch(SM_XF, 0, s); return DEVF(44, D_u_p)(dev, s, (void*)m); }
static HRESULT __stdcall SM_SetMaterial(StateMgr*, const void* m) { SMDEV; SMTouch(SM_MAT, 0, 0); return DEVF(49, D_p)(dev, (void*)m); }
static HRESULT __stdcall SM_SetLight(StateMgr*, DWORD i, const void* l) { SMDEV; SMTouch(SM_LIGHT, 0, i); return DEVF(51, D_u_p)(dev, i, (void*)l); }
static HRESULT __stdcall SM_LightEnable(StateMgr*, DWORD i, BOOL e) { SMDEV; SMTouch(SM_LE, 0, i); return DEVF(53, D_u_u)(dev, i, e); }
static HRESULT __stdcall SM_SetRenderState(StateMgr*, DWORD s, DWORD v) { SMDEV; SMTouch(SM_RS, 0, s); return DEVF(57, D_u_u)(dev, s, v); }
static HRESULT __stdcall SM_SetTexture(StateMgr*, DWORD st, void* t) { SMDEV; SMTouch(SM_TEX, 0, st); return DEVF(65, D_u_p)(dev, st, t); }
static HRESULT __stdcall SM_SetTSS(StateMgr*, DWORD st, DWORD ty, DWORD v) { SMDEV; SMTouch(SM_TSS, st, ty); return DEVF(67, D_u_u_u)(dev, st, ty, v); }
static HRESULT __stdcall SM_SetSS(StateMgr*, DWORD s, DWORD ty, DWORD v) { SMDEV; SMTouch(SM_SS, s, ty); return DEVF(69, D_u_u_u)(dev, s, ty, v); }
static HRESULT __stdcall SM_SetNPatch(StateMgr*, float n) { SMDEV; SMTouch(SM_NP, 0, 0); return ((HRESULT (__stdcall*)(void*, float))(*(void***)dev)[79])(dev, n); }
static HRESULT __stdcall SM_SetFVF(StateMgr*, DWORD f) { SMDEV; SMTouch(SM_FVF, 0, 0); return DEVF(89, D_u)(dev, f); }
static HRESULT __stdcall SM_SetVS(StateMgr*, void* s) { SMDEV; SMTouch(SM_VS, 0, 0); return DEVF(92, D_p)(dev, s); }
static HRESULT __stdcall SM_SetPS(StateMgr*, void* s) { SMDEV; SMTouch(SM_PS, 0, 0); return DEVF(107, D_p)(dev, s); }
static void SMConsts(int type, DWORD reg, DWORD cnt) { for (DWORD i = 0; i < cnt; ++i) SMTouch(type, 0, reg + i); }
static HRESULT __stdcall SMf_VCF(StateMgr*, DWORD r, const void* d, DWORD c) { SMDEV; SMConsts(SM_VCF, r, c); return DEVF(94, D_u_p_u)(dev, r, d, c); }
static HRESULT __stdcall SMf_VCI(StateMgr*, DWORD r, const void* d, DWORD c) { SMDEV; SMConsts(SM_VCI, r, c); return DEVF(96, D_u_p_u)(dev, r, d, c); }
static HRESULT __stdcall SMf_VCB(StateMgr*, DWORD r, const void* d, DWORD c) { SMDEV; SMConsts(SM_VCB, r, c); return DEVF(98, D_u_p_u)(dev, r, d, c); }
static HRESULT __stdcall SMf_PCF(StateMgr*, DWORD r, const void* d, DWORD c) { SMDEV; SMConsts(SM_PCF, r, c); return DEVF(109, D_u_p_u)(dev, r, d, c); }
static HRESULT __stdcall SMf_PCI(StateMgr*, DWORD r, const void* d, DWORD c) { SMDEV; SMConsts(SM_PCI, r, c); return DEVF(111, D_u_p_u)(dev, r, d, c); }
static HRESULT __stdcall SMf_PCB(StateMgr*, DWORD r, const void* d, DWORD c) { SMDEV; SMConsts(SM_PCB, r, c); return DEVF(113, D_u_p_u)(dev, r, d, c); }
static void* g_smVtbl[] = { (void*)SM_QI, (void*)SM_AddRef, (void*)SM_Release, (void*)SM_SetTransform, (void*)SM_SetMaterial, (void*)SM_SetLight,
    (void*)SM_LightEnable, (void*)SM_SetRenderState, (void*)SM_SetTexture, (void*)SM_SetTSS, (void*)SM_SetSS, (void*)SM_SetNPatch, (void*)SM_SetFVF,
    (void*)SM_SetVS, (void*)SMf_VCF, (void*)SMf_VCI, (void*)SMf_VCB, (void*)SM_SetPS, (void*)SMf_PCF, (void*)SMf_PCI, (void*)SMf_PCB };

// attach the state manager to this effect for the rest of the tree loop; false = it already has one (use the original path)
static bool SMAttach(void* fx) {
    for (int i = 0; i < g_smFxN; ++i) if (g_smFx[i] == fx) return g_smOld[i] == nullptr;
    if (g_smFxN >= 16) return false;
    void* old = nullptr; ((HRESULT (__stdcall*)(void*, void**))(*(void***)fx)[72])(fx, &old);   // GetStateManager
    g_smFx[g_smFxN] = fx; g_smOld[g_smFxN] = old; ++g_smFxN;
    if (old) return false;
    g_stateMgr.vt = g_smVtbl;
    ((HRESULT (__stdcall*)(void*, void*))(*(void***)fx)[71])(fx, &g_stateMgr);                  // SetStateManager
    return true;
}
static void SMDetachAll() {
    for (int i = 0; i < g_smFxN; ++i) {
        void* fx = g_smFx[i];
        if (!g_smOld[i]) ((HRESULT (__stdcall*)(void*, void*))(*(void***)fx)[71])(fx, nullptr);
        else ComRelease(g_smOld[i]);
    }
    g_smFxN = 0;
}

// ForestTree parts: 0x4558C0 (Trunk: technique [T+0x22C], mesh [[T+0x1C4]+0x34], frame 0)
//                   0x455960 (Foliage: technique [T+0x230], mesh [[[T+0x1C4]+0x34]+0x40], frame [T+0x1D8])
typedef void (__fastcall *TreePart_t)(BYTE* T, void* edx, void* mat, DWORD z);
typedef void (__fastcall *CE0_t)(void* ce, void* edx);
typedef void (__fastcall *CE1_t)(void* ce, void* edx, DWORD a);
typedef void (__fastcall *CE2_t)(void* ce, void* edx, void* a, DWORD b);
typedef void (__fastcall *Mesh_t)(void* m, void* edx, DWORD frame, DWORD lod);
// Trees in the crossfade band (3D -> flat) are originally alpha-blended (see-through). With TreeDissolve the 3D
// tree stays opaque and alpha-tested with its full-size alpha reference while its alpha (texture x fade) drops:
// the foliage thins out leaf by leaf and the flat tree behind it shows through the gaps.
static int g_dissolve = 0;   // 0 = original blending (default), 1 = dissolve, 2 = dissolve in a 4x shorter band
static bool g_treeDissolve = false; static DWORD g_dissolveRef = 0x84; static DWORD g_dissolveN = 0;
typedef void (__fastcall *ForestTree_t)(BYTE* T, void* edx, void* mat, float a, DWORD s, DWORD sh);
static void __fastcall h_FadingTree(BYTE* T, void* edx, void* mat, float a, DWORD s, DWORD sh) {
    bool on = g_dissolve && g_treeLoop;
    if (on) {
        float v = *(float*)(T + 0x260);                                 // same mapping as the opaque trees (alpha 1)
        g_dissolveRef = v >= 1.0f ? 0xFF : v <= 0.0f ? 0 : (DWORD)(int)(v * 255.0f + 0.5f);
        g_treeDissolve = true; ++g_dissolveN;
    }
    ((ForestTree_t)0x00455CF0)(T, edx, mat, a, s, sh);
    g_treeDissolve = false;
}
// Opaque trees grouped by part (1.1.1): the opaque list is drawn twice - all trunks, then all foliage (both
// far to near as before) - and consecutive parts with the same effect and technique stay inside one
// Begin/BeginPass: per tree only the world matrix, the tree's effect parameters (CommitChanges) and the draw.
// ~2500 effect Begin/BeginPass/EndPass/End per frame in a forest become a handful. Trunks are opaque and write
// depth, so drawing them before the foliage gives the same picture (foliage edges now blend over a nearer
// trunk instead of being cut by it).
static int g_treeParts = 1;                     // [Perf] TreeGroupParts (with TreeBatch)
static bool g_instCapture = false, g_instGroupOk = false; static const float* g_instMat = nullptr;   // instance.inc
static DWORD g_lightGen = 0;                    // bumped on every light change (SetLight / LightEnable / state block / flush)
static bool InstGroupBegin(); static void InstFlush();
static int g_treePhase = 0;                     // 0 = normal, 1 = trunks only, 2 = foliage only
static bool g_tbActive = false, g_tbDissolve = false; static void* g_tbCe = nullptr; static DWORD g_tbTech = 0; static DWORD g_tbGrouped = 0, g_tbStarts = 0, g_tbFadeGrouped = 0;
typedef void (__fastcall *CE0_t)(void* ce, void* edx);
static void TreeBatchEnd() {
    if (!g_tbActive) return;
    void** cvt = *(void***)g_tbCe;
    ((CE0_t)cvt[9])(g_tbCe, nullptr);                                   // EndPass
    ((CE0_t)cvt[7])(g_tbCe, nullptr);                                   // End
    g_tbActive = false; g_tbCe = nullptr;
}
static void TreePart(BYTE* T, void* mat, DWORD tech, void* mesh, DWORD frame) {
    ((VM0_t)0x00435640)(*(void**)(T + 0x228), nullptr);                 // camera view/projection (once per frame)
    void* dev = *pDevice; DEVF(44, D_u_p)(dev, 0x100 /*WORLD*/, mat);
    void* ce = *(void**)(T + 0x3C); void** cvt = *(void***)ce;
    void* fx = *(void**)((BYTE*)ce + 0x20);
    if (g_tbActive) {
        if (g_treePhase && ce == g_tbCe && tech == g_tbTech && g_treeDissolve == g_tbDissolve) {   // same technique: stay in the pass
            ((HRESULT (__stdcall*)(void*))(*(void***)fx)[65])(fx);       // ID3DXEffect::CommitChanges (tree tint, alpha ref)
            if (g_treeDissolve) {                                       // CommitChanges may re-apply parameter-driven states
                DEVF(57, D_u_u)(dev, 27 /*ALPHABLENDENABLE*/, FALSE);
                DEVF(57, D_u_u)(dev, 15 /*ALPHATESTENABLE*/, TRUE);
                DEVF(57, D_u_u)(dev, 24 /*ALPHAREF*/, g_dissolveRef);
                DEVF(57, D_u_u)(dev, 14 /*ZWRITEENABLE*/, TRUE);         // 0x455CF0 turned it off for the fading tree
                ++g_tbFadeGrouped;
            }
            g_instMat = (const float*)mat; g_instCapture = g_instGroupOk && !g_treeDissolve;
            ((Mesh_t)0x004773F0)(mesh, nullptr, frame, 0);
            g_instCapture = false;
            ++g_treeDraws; ++g_tbGrouped;
            return;
        }
        TreeBatchEnd();
    }
    bool batch = SMAttach(fx);
    ((CE1_t)cvt[11])(ce, nullptr, tech);                                // SetTechnique
    UINT passes = 0; ((CE2_t)cvt[6])(ce, nullptr, &passes, batch ? 1 /*D3DXFX_DONOTSAVESTATE*/ : 0);
    if (batch && g_treePhase && passes == 1) {                          // start a group: Begin + BeginPass, draw, keep open
        SMClearTouched();
        ((CE1_t)cvt[8])(ce, nullptr, 0);                                // BeginPass
        SMPassBegun();
        if (g_treeDissolve) {                                           // fading tree: dissolve instead of blending
            SM_SetRenderState(nullptr, 27 /*ALPHABLENDENABLE*/, FALSE);
            SM_SetRenderState(nullptr, 15 /*ALPHATESTENABLE*/, TRUE);
            SM_SetRenderState(nullptr, 24 /*ALPHAREF*/, g_dissolveRef);
            DEVF(57, D_u_u)(dev, 14 /*ZWRITEENABLE*/, TRUE);
        }
        if (!g_treeDissolve) InstGroupBegin(); else g_instGroupOk = false;
        g_instMat = (const float*)mat; g_instCapture = g_instGroupOk;
        ((Mesh_t)0x004773F0)(mesh, nullptr, frame, 0);
        g_instCapture = false;
        g_tbActive = true; g_tbCe = ce; g_tbTech = tech; g_tbDissolve = g_treeDissolve; ++g_tbStarts; ++g_treeDraws;
        return;
    }
    for (UINT p = 0; p < passes; ++p) {
        if (batch && p == 0) SMClearTouched();
        ((CE1_t)cvt[8])(ce, nullptr, p);                                // BeginPass
        if (batch && p == 0) SMPassBegun();
        if (batch && p == 0 && g_treeDissolve) {                        // fading tree: dissolve instead of blending
            SM_SetRenderState(nullptr, 27 /*ALPHABLENDENABLE*/, FALSE);
            SM_SetRenderState(nullptr, 15 /*ALPHATESTENABLE*/, TRUE);
            SM_SetRenderState(nullptr, 24 /*ALPHAREF*/, g_dissolveRef);
            DEVF(57, D_u_u)(dev, 14 /*ZWRITEENABLE*/, TRUE);             // the tree code restores it after the tree
        }
        ((Mesh_t)0x004773F0)(mesh, nullptr, frame, 0);
        ((CE0_t)cvt[9])(ce, nullptr);                                   // EndPass
    }
    ((CE0_t)cvt[7])(ce, nullptr);                                       // End
    ++g_treeDraws;
}
static void __fastcall h_TreeTrunk(BYTE* T, void* edx, void* mat, DWORD z) {
    if (g_treePhase == 2) return;                                       // grouped drawing: foliage phase
    if (!g_treeLoop) { ((TreePart_t)0x004558C0)(T, edx, mat, z); return; }
    TreePart(T, mat, *(DWORD*)(T + 0x22C), *(void**)(*(BYTE**)(T + 0x1C4) + 0x34), 0);
}
static void __fastcall h_TreeFoliage(BYTE* T, void* edx, void* mat, DWORD z) {
    if (g_treePhase == 1) return;                                       // grouped drawing: trunk phase
    CtxGuard g((int*)(T + 0x1D8));                                      // foliage sway smoothing (smoothanim.inc)
    if (!g_treeLoop) { ((TreePart_t)0x00455960)(T, edx, mat, z); return; }
    TreePart(T, mat, *(DWORD*)(T + 0x230), *(void**)(*(BYTE**)(*(BYTE**)(T + 0x1C4) + 0x34) + 0x40), *(DWORD*)(T + 0x1D8));
}
// 0x55C690 reimplemented. List entries are 16 bytes: +8 tree matrix (16 floats; fade at +0x60), +0xC holder ->
// [[holder+8]] = ForestTree. Original blending (TreeDissolve=0): fading trees as before (far to near, each tree
// complete), then the opaque trees far to near twice - trunks, then foliage. With dissolve the fading trees are
// alpha-tested and write depth like the opaque ones, so they join the grouped drawing: all trunks (fading and
// opaque, grouped by tree type), then the fading foliage far to near, then the opaque foliage far to near.
static inline BYTE* TreeOf(BYTE* e) { return **(BYTE***)(*(BYTE**)(e + 12) + 8); }
static int TreeOrderByType(BYTE* base, int count, int* ord) {   // far to near, stable-grouped by effect (tree kind)
    static void* key[32768]; static int tmp[32768];
    int k = 0;
    for (int i = count - 1; i >= 0 && k < 32768; --i) { ord[k] = i; key[k] = *(void**)(TreeOf(base + i * 16) + 0x3C); ++k; }
    void* kinds[16]; int nk = 0, t = 0;
    for (int i = 0; i < k; ++i) { int j = 0; while (j < nk && kinds[j] != key[i]) ++j; if (j == nk) { if (nk == 16) return k; kinds[nk++] = key[i]; } }
    for (int j = 0; j < nk; ++j) for (int i = 0; i < k; ++i) if (key[i] == kinds[j]) tmp[t++] = ord[i];
    memcpy(ord, tmp, k * sizeof(int));
    return k;
}
static inline void TreeFading(BYTE* e, float* mat) {
    float* m = *(float**)(e + 8); memcpy(mat, m, 64);
    h_FadingTree(TreeOf(e), nullptr, mat, 1.0f - m[0x18], 0, 0);
}
static inline void TreeOpaque(BYTE* e, float* mat) {
    memcpy(mat, *(float**)(e + 8), 64);
    ((ForestTree_t)0x00455CF0)(TreeOf(e), nullptr, mat, 1.0f, 0, 0);
}
static void TreeDrawGrouped() {
    float mat[16];
    static int ord[32768];
    int nf = *(int*)0x008CF05C; BYTE* bf = *(BYTE**)0x008CF054;
    int no = *(int*)0x008CF050; BYTE* bo = *(BYTE**)0x008CF04C;
    bool fadeGrouped = g_dissolve != 0;
    if (!fadeGrouped) for (int i = nf - 1; i >= 0; --i) TreeFading(bf + i * 16, mat);
    g_treePhase = 1;                                                    // trunks: opaque, order does not matter
    if (fadeGrouped) { int k = TreeOrderByType(bf, nf, ord); for (int q = 0; q < k; ++q) TreeFading(bf + ord[q] * 16, mat); }
    { int k = TreeOrderByType(bo, no, ord); for (int q = 0; q < k; ++q) TreeOpaque(bo + ord[q] * 16, mat); }
    InstFlush();                                                        // instanced trunks
    g_treePhase = 2;                                                    // foliage: blended edges, far to near
    if (fadeGrouped) for (int i = nf - 1; i >= 0; --i) TreeFading(bf + i * 16, mat);
    for (int i = no - 1; i >= 0; --i) TreeOpaque(bo + i * 16, mat);
    InstFlush();                                                        // instanced foliage
    g_treePhase = 0;
    TreeBatchEnd();
}
// TreeMassive::Render (0x55EDF0) ends with "jmp 0x55C690" (draw the visible trees) -> here
static void TreeDistApply(BYTE* tm);
static void __fastcall h_TreeLoop(void* self) {
    TreeDistApply((BYTE*)self);
    LONGLONG t0 = Now();
    int n = *(int*)0x008CF05C + *(int*)0x008CF050;                      // fading + opaque trees
    if (g_optTrees && n > 0) { g_treeLoop = true; g_smN = 0; g_smOverflow = false; g_smFxN = 0; }
    if (g_treeLoop && g_treeParts) TreeDrawGrouped();
    else ((void (*)())0x0055C690)();
    if (g_treeLoop) {
        TreeBatchEnd();
        SMEndLoop(); SMDetachAll(); g_treeLoop = false; ++g_treeLoops;
        if (g_smOverflow) { g_optTrees = 0; LOG("trees: state manager table overflow -> TreeBatch disabled"); }
    }
    g_frTrees += (Now() - t0) * g_tickMs; g_frTreeN += n;
    (void)self;
}
static void InstallRenderOpt() {
    if (g_optSun >= 0) {
        static const BYTE p[6] = { 0x83, 0xEC, 0x0C, 0x56, 0x8B, 0xF1 };
        o_SunTest = (SunTest_t)Detour((BYTE*)0x00535850, p, 6, (void*)h_SunTest);
        if (!o_SunTest) g_sunBroken = true;
    }
    static const BYTE c1[5] = { 0xE8, 0x2C, 0xF9, 0xFF, 0xFF }, c2[5] = { 0xE8, 0xC2, 0xF9, 0xFF, 0xFF }, j[5] = { 0xE9, 0x89, 0xD8, 0xFF, 0xFF };
    BYTE* a1 = (BYTE*)0x00455F8F; BYTE* a2 = (BYTE*)0x00455F99; BYTE* a3 = (BYTE*)0x0055EE02;
    if (!memcmp(a1, c1, 5) && !memcmp(a2, c2, 5) && !memcmp(a3, j, 5) && !memcmp((void*)0x00435640, "\x81\xEC\xA4\x00\x00\x00", 6)) {
        BYTE b[5];
        b[0] = 0xE8; *(DWORD*)(b + 1) = (DWORD)(void*)h_TreeTrunk - (DWORD)(a1 + 5);   PatchBytes(a1, b, 5);
        b[0] = 0xE8; *(DWORD*)(b + 1) = (DWORD)(void*)h_TreeFoliage - (DWORD)(a2 + 5); PatchBytes(a2, b, 5);
        b[0] = 0xE9; *(DWORD*)(b + 1) = (DWORD)(void*)h_TreeLoop - (DWORD)(a3 + 5);    PatchBytes(a3, b, 5);
        LOG("render opt: forest tree batching installed (TreeBatch=%d)", g_optTrees);
        static const BYTE cf[5] = { 0xE8, 0x04, 0x96, 0xEF, 0xFF };   // fading loop: call 0x455CF0 at 0x55C6E7
        BYTE* a4 = (BYTE*)0x0055C6E7;
        if (!memcmp(a4, cf, 5)) { b[0] = 0xE8; *(DWORD*)(b + 1) = (DWORD)(void*)h_FadingTree - (DWORD)(a4 + 5); PatchBytes(a4, b, 5); }
        else LOG("render opt: fading tree call differs, TreeDissolve unavailable");
    } else { g_optTrees = 0; LOG("render opt: forest tree code differs, TreeBatch unavailable"); }
    LOG("render opt: async sun test %s (AsyncSunCheck=%d)", o_SunTest ? "installed" : "unavailable", g_optSun);
}

// ---------------------------------------------------------------- 3) point-in-polygon test (0x43F2F0)
// Used by movement / collision code against obstacle outlines. The original sums the angle between consecutive
// vertex vectors with two atan2 calls per edge (over count-1 edges of a circular list) and reports "inside" when
// |sum| >= pi. Next to a big obstacle (a large rock) it runs thousands of times per frame: ~15 ms of atan2.
// Same result here: the open-chain sum equals 2*pi*windingNumber - angle(closing edge), the winding number is
// counted with cross products and only one atan2 is needed. The iterator side effect (count-1 steps) is kept.
static int g_optPoly = 1;                            // [Perf] FastPolygonTest; Ctrl+4 with the other optimizations
static DWORD g_polyCalls = 0;
static int __cdecl h_PointInPoly(const float* A, const float* B, BYTE* it, float dx, float dy) {
    ++g_polyCalls;
    int n = *(int*)(it + 4);
    if (n - 1 <= 0) return 0;
    BYTE* nd = *(BYTE**)it;
    float px = B[0] + dx, py = dy + B[1];
    BYTE* first = nd; BYTE* last = nd;
    int wn = 0;
    float ax = 0, ay = 0;
    for (int i = 0; i < n; ++i) {                                       // vertices start .. start+n-1
        const float* v = (const float*)(nd + 0x0C);
        float wx = (A[0] + v[0]) - px, wy = (v[1] + A[1]) - py;
        if (i > 0) {
            float c = ax * wy - ay * wx;
            if (ay <= 0) { if (wy > 0 && c > 0) ++wn; } else { if (wy <= 0 && c < 0) --wn; }
        }
        ax = wx; ay = wy; last = nd;
        if (i < n - 1) nd = *(BYTE**)(nd + 4);
    }
    *(BYTE**)it = last;                                                 // iterator advanced n-1 times, as in the original
    const float* f = (const float*)(first + 0x0C);
    float bx = (A[0] + f[0]) - px, by = (f[1] + A[1]) - py;             // closing edge last -> first
    float c = ax * by - ay * bx;
    if (ay <= 0) { if (by > 0 && c > 0) ++wn; } else { if (by <= 0 && c < 0) --wn; }
    float th = atan2f(c, ax * bx + ay * by);
    float s = 6.2831855f * wn - th;
    return fabsf(s) >= 3.1415927f ? 1 : 0;
}
static int __cdecl h_PointInPolyGate(const float* A, const float* B, BYTE* it, float dx, float dy);
typedef int (__cdecl *PIP_t)(const float*, const float*, BYTE*, float, float);
static PIP_t o_PointInPoly = nullptr;
static int __cdecl h_PointInPolyGate(const float* A, const float* B, BYTE* it, float dx, float dy) {
    return g_optPoly ? h_PointInPoly(A, B, it, dx, dy) : o_PointInPoly(A, B, it, dx, dy);
}
static void InstallPolyOpt() {
    static const BYTE p[5] = { 0x83, 0xEC, 0x14, 0xD9, 0xEE };          // sub esp,14h / fldz
    o_PointInPoly = (PIP_t)Detour((BYTE*)0x0043F2F0, p, 5, (void*)h_PointInPolyGate);
    LOG("point-in-polygon test %s (FastPolygonTest=%d)", o_PointInPoly ? "replaced" : "unavailable", g_optPoly);
}

static void RenderOptStats() {
    PLOG("RENDEROPT sun(async=%d): copies=%lu reads=%lu busy=%lu sync=%lu | trees(batch=%d grouped=%d): loops=%lu parts=%lu (groups %lu, in a group %lu, of them fading %lu, fading trees %lu) | polygon tests(fast=%d)=%lu",
         g_optSun, g_sunCopies, g_sunReads, g_sunBusy, g_sunSync, g_optTrees, g_treeParts, g_treeLoops, g_treeDraws, g_tbStarts, g_tbGrouped, g_tbFadeGrouped, g_dissolveN, g_optPoly, g_polyCalls);
    g_sunCopies = g_sunReads = g_sunBusy = g_sunSync = g_treeLoops = g_treeDraws = g_polyCalls = 0; g_tbStarts = g_tbGrouped = g_tbFadeGrouped = g_dissolveN = 0;
}

// ---------------------------------------------------------------- 4) object view distance
// World props ("gizmos") are hidden beyond a distance computed from their size, the camera field of view and a
// range class (GizmoRanges: closest 2 ... farest 32) at load time (0x45C3E0); visible = dist^2 < range^2 (0x45CB40).
// The thresholds were tuned for 800x600..1280x1024, so at modern resolutions props pop in while still large on
// screen. [Video] ObjectDistance multiplies the range (1.0 = original); applied when a location is loaded.
static float g_objDist = 2.0f; static int g_objDistOn = 1;
static inline float ObjDist() { return g_objDistOn ? g_objDist : 1.0f; }
typedef float (__fastcall *GizmoRange_t)(BYTE* obj, void* edx, float cls);
static GizmoRange_t o_GizmoRange = nullptr;
static float __fastcall h_GizmoRange(BYTE* obj, void* edx, float cls) {
    float r = o_GizmoRange(obj, edx, cls);
    return r * ObjDist();
}
// Most other objects (SAO props: boxes, wheels, ropes; NPCs; town animations; units) pick a LOD level from their
// size and distance (0x463E20, ~distance / (size * tan(fov/2))) and are not drawn at all beyond level 10..11.
// The level is divided by ObjectDistance (also selects the more detailed mesh LOD further away).
// Their shadows are drawn only within 500 units (dist^2 < 250000, double at 0x615808; float 0x615B28 for town
// animations): scaled by ObjectDistance^2.
static bool g_shadowDistOk = false;
static void ObjDistApplyShadows() {
    if (!g_shadowDistOk) return;
    double nd = 250000.0 * ObjDist() * ObjDist(); float nf = (float)nd;
    PatchBytes((void*)0x00615808, &nd, 8); PatchBytes((void*)0x00615B28, &nf, 4);
}
typedef int (__cdecl *LodLevel_t)(void* a, float* b, float* c);
static LodLevel_t o_LodLevel = nullptr;
static int __cdecl h_LodLevel(void* a, float* b, float* c) {
    int lv = o_LodLevel(a, b, c);
    float f = ObjDist();
    return f > 1.0f ? (int)(lv / f) : lv;
}
static void InstallObjDistance() {
    // installed also at 1.0 (= original behaviour) so that the in-game quality page can change it at run time
    static const BYTE p[5] = { 0x83, 0xEC, 0x70, 0x8B, 0xC1 };
    o_GizmoRange = (GizmoRange_t)Detour((BYTE*)0x0045C3E0, p, 5, (void*)h_GizmoRange);
    static const BYTE pl[7] = { 0x83, 0xEC, 0x18, 0x8B, 0x44, 0x24, 0x20 };
    o_LodLevel = (LodLevel_t)Detour((BYTE*)0x00463E20, pl, 7, (void*)h_LodLevel);
    double* sd = (double*)0x00615808; float* sf = (float*)0x00615B28;
    if (*sd == 250000.0 && *sf == 250000.0f) { g_shadowDistOk = true; ObjDistApplyShadows(); }
    else LOG("object shadow distance: unexpected constants, unchanged");
    LOG("object view distance x%.2f (gizmo %s, LOD %s, shadows %.0f units)", g_objDist, o_GizmoRange ? "ok" : "n/a", o_LodLevel ? "ok" : "n/a", 500.0 * g_objDist);
}

// ---------------------------------------------------------------- 5) forest tree distances
// TreeMassive (0x55E820) sorts the trees in view by distance: closer than crossFadeDistanceStart [+0x58] they are
// full 3D trees, up to crossFadeDistanceEnd [+0x5C] the 3D tree fades out (alpha 1-t) while a flat billboard
// fades in (alpha t) -> both are see-through in that band; billboards are drawn up to visibleTreeDistance
// [+0x60] and fade out over visibleTreeFadeDistance [+0x64]. The values come from planetree.ef and the
// "tree distance" option (start 100..500). [Video] TreeDistance multiplies all four (Ctrl+9 with the props):
// the crossfade happens where trees are small on screen.
static float g_treeDist = 2.0f;
// [Video] Tree3DDistance (1.1.2): 0 = the 3D -> flat crossfade as the game's "tree distance" option sets it (times
// TreeDistance); > 0 = the crossfade ends at this distance whatever the game option (which then only decides how far
// flat trees are drawn). The game's "very far" puts 3D trees out to ~4800 units: thousands of 3D trees per frame.
static float g_tree3D = 0.0f;
struct TreeDistRec { BYTE* tm; float orig[4], written[4]; };
static TreeDistRec g_tdr[64]; static int g_tdrN = 0;
static void TreeDistApply(BYTE* tm) {
    if (!tm) return;
    TreeDistRec* r = nullptr;
    for (int i = 0; i < g_tdrN; ++i) if (g_tdr[i].tm == tm) { r = &g_tdr[i]; break; }
    float* f = (float*)(tm + 0x58);
    if (!r) {
        if (g_tdrN >= 64) return;
        r = &g_tdr[g_tdrN++]; r->tm = tm;
        for (int k = 0; k < 4; ++k) r->orig[k] = r->written[k] = f[k];
        LOG("trees: crossfade %.0f..%.0f, visible %.0f (fade %.0f) -> x%.2f", f[0], f[1], f[2], f[3], g_treeDist);
    }
    bool chg = false;
    for (int k = 0; k < 4; ++k) if (f[k] != r->written[k]) { r->orig[k] = f[k]; chg = true; }   // changed by the game (options)
    if (r->orig[2] < 500 || r->orig[1] > r->orig[2] || r->orig[0] > r->orig[1] || r->orig[0] < 0) {
        // broken by the old interaction with the game's option (negative / inverted distances saved): sane values,
        // the game's option continues from them and saves them on Apply
        LOG("trees: invalid distances %.0f..%.0f visible %.0f -> repaired", r->orig[0], r->orig[1], r->orig[2]);
        r->orig[0] = 667; r->orig[1] = 1000; r->orig[2] = 4000; r->orig[3] = 200; chg = true;
    }
    if (r->orig[1] - r->orig[0] < 50 || r->orig[0] > 1000) {
        // no crossfade band (e.g. 1500..1500 saved in graphic.cfg when our 3D distance leaked into the game's settings
        // on Apply): 3D trees popped to flat ones. The game keeps end = start + 200 and start <= 500 ("very far"
        // = 500..700 with visible 5000); the band is rebuilt from the visible distance, also in the engine settings
        // (saved with the next Apply).
        float st = r->orig[2] * 0.1f; if (st > 500) st = 500; if (st < 50) st = 50;
        LOG("trees: crossfade %.1f..%.1f has no band -> %.0f..%.0f", r->orig[0], r->orig[1], st, st + 200);
        BYTE* eng = ((BYTE* (*)())0x0042F160)();
        if (eng) { float* es = (float*)(eng + 0x2C);
            if (fabsf(es[0] - r->orig[0]) < 1.0f && fabsf(es[1] - r->orig[1]) < 1.0f) { es[0] = st; es[1] = st + 200; LOG("trees: engine tree settings repaired too"); } }
        r->orig[0] = st; r->orig[1] = st + 200; chg = true;
    }
    if (chg) LOG("trees: game option -> crossfade %.0f..%.0f, visible %.0f (fade %.0f)", r->orig[0], r->orig[1], r->orig[2], r->orig[3]);
    float m = (g_objDistOn && g_treeDist > 0.5f) ? g_treeDist : 1.0f;
    // only the 3D -> flat crossfade moves; the flat-tree range stays original (scaling it filled the horizon with
    // thousands of alpha-blended billboards: GPU fill rate, ~90 FPS when looking over a large forest)
    float lim = r->orig[2] - r->orig[3];                                // keep the crossfade inside the flat-tree range
    f[0] = r->orig[0] * m; f[1] = r->orig[1] * m;
    if (g_tree3D > 0 && g_objDistOn && r->orig[1] > 0) {                // absolute 3D range, crossfade band keeps its proportion
        float ratio = r->orig[0] / r->orig[1]; if (!(ratio >= 0.3f && ratio <= 0.95f)) ratio = 500.0f / 700.0f;
        f[1] = g_tree3D; f[0] = g_tree3D * ratio;
    }
    if (lim > 0 && f[1] > lim) { float d = f[1] - lim; f[1] = lim; f[0] = f[0] - d > 0 ? f[0] - d : 0; }
    if (g_dissolve == 2 && f[1] > f[0]) f[0] = f[1] - (f[1] - f[0]) * 0.25f;   // short transition: 4x narrower band
    f[2] = r->orig[2]; f[3] = r->orig[3];
    for (int k = 0; k < 4; ++k) r->written[k] = f[k];
}
// The game's own tree-distance functions (Lua: TreeDistanceUp/Down, GetTreeDistCoef, SaveTreeDist, CancelTreeDist)
// read and write the TreeMassive values that TreeDistApply has scaled: they added their step to our value, saved it
// and computed the option level from it (levels skipped, the band grew with every click, trees popped). While one
// of them runs, the game's own values are put back; afterwards ours are applied again.
static bool TreeDistIsCurrent(BYTE* tm) {
    BYTE* eng = ((BYTE* (*)())0x0042F160)(); if (!eng) return false;
    BYTE* lvl = *(BYTE**)(eng + 0x70); if (!lvl) return false;
    BYTE* c = *(BYTE**)(lvl + 0x78); if (!c) return false;
    BYTE** b = *(BYTE***)(c + 0x68); BYTE** e = *(BYTE***)(c + 0x6C);
    if (!b || e < b || e - b > 64) return false;
    for (BYTE** p = b; p < e; ++p) if (*p == tm) return true;
    return false;
}
static void TreeDistGameValues() {   // our values out, the game's in
    for (int i = 0; i < g_tdrN; ++i) {
        TreeDistRec& r = g_tdr[i]; if (!TreeDistIsCurrent(r.tm)) continue;
        float* f = (float*)(r.tm + 0x58);
        for (int k = 0; k < 4; ++k) { if (f[k] == r.written[k]) f[k] = r.orig[k]; r.written[k] = f[k]; }
    }
}
static void TreeDistOurValues() {    // whatever the game changed becomes its value, ours applied on top
    for (int i = 0; i < g_tdrN; ++i) if (TreeDistIsCurrent(g_tdr[i].tm)) TreeDistApply(g_tdr[i].tm);
}
static float TreeViewDistance() {    // the game's own "visible trees" distance of the current level (0 = none)
    BYTE* eng = ((BYTE* (*)())0x0042F160)(); if (!eng) return 0;
    BYTE* lvl = *(BYTE**)(eng + 0x70); if (!lvl) return 0;
    BYTE* c = *(BYTE**)(lvl + 0x78); if (!c) return 0;
    BYTE** b = *(BYTE***)(c + 0x68); BYTE** e = *(BYTE***)(c + 0x6C);
    if (!b || e <= b || e - b > 64 || !*b) return 0;
    for (int i = 0; i < g_tdrN; ++i) if (g_tdr[i].tm == *b) return g_tdr[i].orig[2];
    return ((float*)(*b + 0x58))[2];
}
typedef int (__cdecl *LuaCF_t)(void* L);
#define TD_WRAP(name, addr) static int __cdecl name(void* L) { TreeDistGameValues(); int r = ((LuaCF_t)(addr))(L); TreeDistOurValues(); return r; }
TD_WRAP(L_TreeDistUp, 0x0044C5A0)
TD_WRAP(L_TreeDistDown, 0x0044C840)
TD_WRAP(L_TreeDistCoef, 0x0044CAE0)
TD_WRAP(L_TreeDistSave, 0x0044B610)
TD_WRAP(L_TreeDistCancel, 0x0044CCF0)
