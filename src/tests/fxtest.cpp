// test harness: deferred effect-state restore vs reference D3DX save/restore semantics
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <map>
#include <vector>
#include <cmath>
#define __stdcall
#define __fastcall
typedef uint32_t DWORD; typedef unsigned char BYTE; typedef int32_t HRESULT; typedef uint32_t ULONG; typedef int BOOL; typedef unsigned UINT; typedef int INT;
struct GUID { DWORD a, b, c, d; };
#define S_OK 0
static void LOG(const char*, ...) {}
static void PLOG(const char*, ...) {}
static void* g_devPtr; static void** const pDevice = &g_devPtr;
static int AnisoLevel() { return 0; }
static void* PatchVtbl(void** vt, int i, void* h) { void* o = vt[i]; vt[i] = h; return o; }
static void* Detour(BYTE*, const BYTE*, int, void*) { return nullptr; }
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
static bool g_instCapture=false; static bool InstCaptureDIP(void*,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD){return false;}
#define E_FAIL ((HRESULT)0x80004005)
// ---------------------------------------------------------------- 6) all effects: cheaper state save/restore (1.1.1)
// Included into attfix.cpp after renderopt.inc.
//
// Every CEffect::Begin (0x4480C0) of the game passes flags 0: D3DX captures the states the technique touches and
// End (0x4480F0) re-applies all of them, then every BeginPass sets all pass states again, whether they changed or
// not. In the profile CEffect::End + BeginPass are ~25% of the frame.
// Here a Begin with flags 0 runs with D3DXFX_DONOTSAVESTATE through a per-Begin state manager:
//  - a state set by the effect is forwarded only if it differs from the current device value (read back with
//    the device's Get* call, so direct device changes by the game in between are always seen);
//  - the first time a state is touched its value is remembered; at End every touched state whose current value
//    differs from the remembered one is set back.
// The device state after End is the same as with the original save/restore. Effects that already have a state
// manager (the forest tree batching) and Begin calls with other flags are left alone.
static int g_optFx = 1;                         // [Perf] EffectStates; Ctrl+4 with the other optimizations
static int g_fxDeferCfg = 1;                    // [Perf] EffectDeferRestore (needs EffectStates)
static bool g_fxHooks = false, g_fxInstalled = false;                  // device hooks for the deferred restore installed
static DWORD g_fxBegins = 0, g_fxSkipped = 0, g_fxForwarded = 0, g_fxRestored = 0;
static DWORD g_fxDeferred = 0, g_fxTaken = 0, g_fxFlushed = 0, g_fxDropped = 0, g_fxFlushes = 0;
static int g_fxIn = 0;                          // >0: our own device calls (no pending-state handling in the hooks)

struct FxEntry { DWORD key; BYTE ok; void* ref; BYTE s0[104]; };
enum { FX_MAXE = 192, FX_SESS = 8 };
enum { FX_SLOTS = 900 };
struct FxSess { void** vt; void* fx; bool used; int n; DWORD gen; FxEntry e[FX_MAXE]; DWORD slotGen[FX_SLOTS]; BYTE slotIdx[FX_SLOTS]; };
static DWORD g_fxGen = 0;
// dense slot of a state key for O(1) lookup (-1: rare key, linear search)
static int FxSlot(DWORD key) {
    DWORD type = key >> 24, a = (key >> 14) & 0x3FF, b = key & 0x3FFF;
    auto smp = [](DWORD i) -> int { return i < 16 ? (int)i : (i >= 256 && i <= 260) ? (int)(i - 240) : -1; };
    switch (type) {
    case SM_RS:  return b < 256 ? (int)b : -1;
    case SM_TSS: return a < 8 && b < 33 ? 256 + (int)(a * 33 + b) : -1;
    case SM_SS:  { int i = smp(a); return i >= 0 && b < 14 ? 520 + i * 14 + (int)b : -1; }
    case SM_TEX: { int i = smp(b); return i >= 0 ? 814 + i : -1; }
    case SM_LE:  return b < 8 ? 835 + (int)b : -1;
    case SM_LIGHT: return b < 8 ? 843 + (int)b : -1;
    case SM_FVF: return 851; case SM_VS: return 852; case SM_PS: return 853; case SM_MAT: return 854; case SM_NP: return 855;
    case SM_XF:  return b < 24 ? 856 + (int)b : (b >= 256 && b < 260) ? 880 + (int)(b - 256) : -1;
    }
    return -1;
}
static FxSess g_fxs[FX_SESS];
static void* g_fxVtbl[21];

// read the current device value of a state (same keys as the tree state manager)
static bool FxGet0(void* dev, DWORD key, BYTE* out, void** ref) {
    DWORD type = key >> 24, a = (key >> 14) & 0x3FF, b = key & 0x3FFF;
    memset(out, 0, 16);
    switch (type) {
    case SM_RS:   return DEVF(58, D_u_p)(dev, b, out) >= 0;
    case SM_TSS:  return DEVF(66, D_u_u_p)(dev, a, b, out) >= 0;
    case SM_SS:   return DEVF(68, D_u_u_p)(dev, a, b, out) >= 0;
    case SM_LE:   { bool r = DEVF(54, D_u_p)(dev, b, out) >= 0; *(DWORD*)out = *(DWORD*)out ? 1 : 0; return r; }
    case SM_TEX:  { void* t = nullptr; if (DEVF(64, D_u_p)(dev, b, &t) < 0) return false; *(void**)out = t; if (ref) *ref = t; else ComRelease(t); return true; }
    case SM_FVF:  {   // FVF 0 = a vertex declaration is set: remember that one (restored with SetVertexDeclaration)
        if (DEVF(90, D_p)(dev, out) < 0) return false;
        if (ref && !*(DWORD*)out) { void* d = nullptr; if (DEVF(88, D_p)(dev, &d) >= 0) *ref = d; }
        return true; }
    case SM_VS:   { void* t = nullptr; if (DEVF(93, D_p)(dev, &t) < 0) return false; *(void**)out = t; if (ref) *ref = t; else ComRelease(t); return true; }
    case SM_PS:   { void* t = nullptr; if (DEVF(108, D_p)(dev, &t) < 0) return false; *(void**)out = t; if (ref) *ref = t; else ComRelease(t); return true; }
    case SM_XF:   return DEVF(45, D_u_p)(dev, b, out) >= 0;
    case SM_MAT:  return DEVF(50, D_p)(dev, out) >= 0;
    case SM_LIGHT: return DEVF(52, D_u_p)(dev, b, out) >= 0;
    case SM_NP:   *(float*)out = ((float (__stdcall*)(void*))(*(void***)dev)[80])(dev); return true;
    case SM_VCF:  return DEVF(95, D_u_p_u)(dev, b, out, 1) >= 0;
    case SM_VCI:  return DEVF(97, D_u_p_u)(dev, b, out, 1) >= 0;
    case SM_VCB:  return DEVF(99, D_u_p_u)(dev, b, out, 1) >= 0;
    case SM_PCF:  return DEVF(110, D_u_p_u)(dev, b, out, 1) >= 0;
    case SM_PCI:  return DEVF(112, D_u_p_u)(dev, b, out, 1) >= 0;
    case SM_PCB:  return DEVF(114, D_u_p_u)(dev, b, out, 1) >= 0;
    }
    return false;
}
static bool FxGet(void* dev, DWORD key, BYTE* out, void** ref) { ++g_fxIn; bool r = FxGet0(dev, key, out, ref); --g_fxIn; return r; }
static int FxSize(DWORD key) {
    switch (key >> 24) {
    case SM_XF: return 64; case SM_MAT: return 68; case SM_LIGHT: return 104;
    case SM_VCF: case SM_VCI: case SM_PCF: case SM_PCI: return 16;
    case SM_TEX: case SM_VS: case SM_PS: return (int)sizeof(void*);
    default: return 4;
    }
}
// ---- deferred restore (1.1.1): End does not set the touched states back right away. They become "pending"
// (key -> value the original End would have restored). The next effect that sets such a state compares against
// the device and takes the pending value over as its own original; everything else still pending is applied
// right before anything that could observe it: a draw call, Clear, EndScene, any Get*, a state block. A state
// the game sets directly drops its pending value (the new value wins, as it would have after a real restore).
enum { FX_PEND = 256 };
static FxEntry g_pend[FX_PEND]; static int g_pendN = 0; static short g_pendSlot[FX_SLOTS];   // slot -> index + 1
static inline bool FxDefer() { return g_fxHooks && g_optFx && g_fxDeferCfg; }
static int PendFind(DWORD key) {
    int sl = FxSlot(key);
    if (sl >= 0) return g_pendSlot[sl] - 1;
    for (int i = 0; i < g_pendN; ++i) if (g_pend[i].key == key) return i;
    return -1;
}
static void PendRemove(int i, bool release) {
    if (release) ComRelease(g_pend[i].ref);
    int sl = FxSlot(g_pend[i].key); if (sl >= 0) g_pendSlot[sl] = 0;
    if (i != --g_pendN) {
        g_pend[i] = g_pend[g_pendN];
        int sl2 = FxSlot(g_pend[i].key); if (sl2 >= 0) g_pendSlot[sl2] = (short)(i + 1);
    }
}
static void PendApply(void* dev, FxEntry& e) {   // set the pending value on the device (our own call)
    SMEntry tmp; tmp.key = e.key; tmp.n = e.ok; tmp.ref = e.ref; memcpy(tmp.s0, e.s0, sizeof tmp.s0);
    ++g_fxIn; SMRestore(dev, tmp); --g_fxIn;
}
static void PendAdd(void* dev, FxEntry& e) {      // takes over e.ref
    if (g_pendN >= FX_PEND) { PendApply(dev, e); ComRelease(e.ref); e.ref = nullptr; ++g_fxRestored; return; }
    g_pend[g_pendN] = e; e.ref = nullptr;
    int sl = FxSlot(e.key); if (sl >= 0) g_pendSlot[sl] = (short)(g_pendN + 1);
    ++g_pendN; ++g_fxDeferred;
}
static void FxFlush() {                           // apply everything pending
    if (!g_pendN) return;
    void* dev = *pDevice; ++g_fxFlushes;
    for (int i = 0; i < g_pendN; ++i) {
        PendApply(dev, g_pend[i]); ComRelease(g_pend[i].ref);
        int sl = FxSlot(g_pend[i].key); if (sl >= 0) g_pendSlot[sl] = 0;
    }
    g_fxFlushed += g_pendN; g_pendN = 0;
}
static void PendDrop(DWORD key) {                 // the game sets this state itself
    int i = PendFind(key); if (i < 0) return;
    PendRemove(i, true); ++g_fxDropped;
}
static void PendClear() {                         // device reset: forget (states are reset anyway)
    for (int i = 0; i < g_pendN; ++i) ComRelease(g_pend[i].ref);
    g_pendN = 0; memset(g_pendSlot, 0, sizeof g_pendSlot);
}
#define PEND_FLUSH() do { if (g_pendN && !g_fxIn) FxFlush(); } while (0)
#define PEND_DROP(k) do { if (g_pendN && !g_fxIn) PendDrop(k); } while (0)
typedef HRESULT (__stdcall *F_p_t)(void*);
typedef HRESULT (__stdcall *F_u_t)(void*, DWORD);
typedef HRESULT (__stdcall *F_pp_t)(void*, void*);
typedef HRESULT (__stdcall *F_u_p_t)(void*, DWORD, void*);
typedef HRESULT (__stdcall *F_u_u_t)(void*, DWORD, DWORD);
typedef HRESULT (__stdcall *F_u_u_p_t)(void*, DWORD, DWORD, void*);
typedef HRESULT (__stdcall *F_u_u_u_t)(void*, DWORD, DWORD, DWORD);
static void* g_fxO[128];                          // original device methods by vtable index
static void* g_sbO[8];                            // original state block methods
#define O(i, T) ((T)g_fxO[i])
// sets by the game: drop the pending value of that state
static HRESULT __stdcall hp_SetTransform(void* d, DWORD st, void* m) { PEND_DROP(SMKey(SM_XF, 0, st)); return O(44, F_u_p_t)(d, st, m); }
static HRESULT __stdcall hp_MulTransform(void* d, DWORD st, void* m) { PEND_FLUSH(); return O(46, F_u_p_t)(d, st, m); }
static HRESULT __stdcall hp_SetMaterial(void* d, void* m) { PEND_DROP(SMKey(SM_MAT, 0, 0)); return O(49, F_pp_t)(d, m); }
static HRESULT __stdcall hp_SetLight(void* d, DWORD i, void* l) { PEND_DROP(SMKey(SM_LIGHT, 0, i)); return O(51, F_u_p_t)(d, i, l); }
static HRESULT __stdcall hp_LightEnable(void* d, DWORD i, DWORD en) { PEND_DROP(SMKey(SM_LE, 0, i)); return O(53, F_u_u_t)(d, i, en); }
static HRESULT __stdcall hp_SetRS(void* d, DWORD st, DWORD v) { PEND_DROP(SMKey(SM_RS, 0, st)); return O(57, F_u_u_t)(d, st, v); }
static HRESULT __stdcall hp_SetTexture(void* d, DWORD st, void* t) { PEND_DROP(SMKey(SM_TEX, 0, st)); return O(65, F_u_p_t)(d, st, t); }
static HRESULT __stdcall hp_SetTSS(void* d, DWORD st, DWORD ty, DWORD v) { PEND_DROP(SMKey(SM_TSS, st, ty)); return O(67, F_u_u_u_t)(d, st, ty, v); }
static HRESULT __stdcall hp_SetSS(void* d, DWORD sm, DWORD ty, DWORD v) { PEND_DROP(SMKey(SM_SS, sm, ty)); return O(69, F_u_u_u_t)(d, sm, ty, v); }
static HRESULT __stdcall hp_SetNPatch(void* d, float n) { PEND_DROP(SMKey(SM_NP, 0, 0)); return ((HRESULT (__stdcall*)(void*, float))g_fxO[79])(d, n); }
static HRESULT __stdcall hp_SetDecl(void* d, void* decl) { PEND_DROP(SMKey(SM_FVF, 0, 0)); return O(87, F_pp_t)(d, decl); }
static HRESULT __stdcall hp_SetFVF(void* d, DWORD f) { PEND_DROP(SMKey(SM_FVF, 0, 0)); return O(89, F_u_t)(d, f); }
static HRESULT __stdcall hp_SetVS(void* d, void* sh) { PEND_DROP(SMKey(SM_VS, 0, 0)); return O(92, F_pp_t)(d, sh); }
static HRESULT __stdcall hp_SetPS(void* d, void* sh) { PEND_DROP(SMKey(SM_PS, 0, 0)); return O(107, F_pp_t)(d, sh); }
// anything that reads or depends on the full state: apply what is pending first
static HRESULT __stdcall hp_GetTransform(void* d, DWORD st, void* m) { PEND_FLUSH(); return O(45, F_u_p_t)(d, st, m); }
static HRESULT __stdcall hp_GetMaterial(void* d, void* m) { PEND_FLUSH(); return O(50, F_pp_t)(d, m); }
static HRESULT __stdcall hp_GetLight(void* d, DWORD i, void* l) { PEND_FLUSH(); return O(52, F_u_p_t)(d, i, l); }
static HRESULT __stdcall hp_GetLightEnable(void* d, DWORD i, void* b) { PEND_FLUSH(); return O(54, F_u_p_t)(d, i, b); }
static HRESULT __stdcall hp_GetRS(void* d, DWORD st, void* v) { PEND_FLUSH(); return O(58, F_u_p_t)(d, st, v); }
static HRESULT __stdcall hp_GetTexture(void* d, DWORD st, void* t) { PEND_FLUSH(); return O(64, F_u_p_t)(d, st, t); }
static HRESULT __stdcall hp_GetTSS(void* d, DWORD st, DWORD ty, void* v) { PEND_FLUSH(); return O(66, F_u_u_p_t)(d, st, ty, v); }
static HRESULT __stdcall hp_GetSS(void* d, DWORD sm, DWORD ty, void* v) { PEND_FLUSH(); return O(68, F_u_u_p_t)(d, sm, ty, v); }
static float __stdcall hp_GetNPatch(void* d) { PEND_FLUSH(); return ((float (__stdcall*)(void*))g_fxO[80])(d); }
static HRESULT __stdcall hp_GetDecl(void* d, void* p) { PEND_FLUSH(); return O(88, F_pp_t)(d, p); }
static HRESULT __stdcall hp_GetFVF(void* d, void* p) { PEND_FLUSH(); return O(90, F_pp_t)(d, p); }
static HRESULT __stdcall hp_GetVS(void* d, void* p) { PEND_FLUSH(); return O(93, F_pp_t)(d, p); }
static HRESULT __stdcall hp_GetPS(void* d, void* p) { PEND_FLUSH(); return O(108, F_pp_t)(d, p); }
static HRESULT __stdcall hp_EndScene(void* d) { PEND_FLUSH(); return O(42, F_p_t)(d); }
static HRESULT __stdcall hp_Clear(void* d, DWORD n, void* r, DWORD f, DWORD c, DWORD z, DWORD st) {
    PEND_FLUSH(); return ((HRESULT (__stdcall*)(void*, DWORD, void*, DWORD, DWORD, DWORD, DWORD))g_fxO[43])(d, n, r, f, c, z, st); }
static HRESULT __stdcall hp_DP(void* d, DWORD a, DWORD b, DWORD c) { PEND_FLUSH(); return O(81, F_u_u_u_t)(d, a, b, c); }

static HRESULT __stdcall hp_DIP(void* d, DWORD a, DWORD b, DWORD c, DWORD e, DWORD f, DWORD g) {
    PEND_FLUSH();
    if (g_instCapture && !g_fxIn && InstCaptureDIP(d, a, b, c, e, f, g)) return 0;   // instanced later (forest trees)
    return ((HRESULT (__stdcall*)(void*, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD))g_fxO[82])(d, a, b, c, e, f, g); }
static HRESULT __stdcall hp_DPUP(void* d, DWORD a, DWORD b, void* c, DWORD e) {
    PEND_FLUSH(); return ((HRESULT (__stdcall*)(void*, DWORD, DWORD, void*, DWORD))g_fxO[83])(d, a, b, c, e); }
static HRESULT __stdcall hp_DIPUP(void* d, DWORD a, DWORD b, DWORD c, DWORD e, void* f, DWORD g, void* h, DWORD i) {
    PEND_FLUSH(); return ((HRESULT (__stdcall*)(void*, DWORD, DWORD, DWORD, DWORD, void*, DWORD, void*, DWORD))g_fxO[84])(d, a, b, c, e, f, g, h, i); }
static HRESULT __stdcall hp_ProcessVertices(void* d, DWORD a, DWORD b, DWORD c, void* vb, void* decl, DWORD f) {
    PEND_FLUSH(); return ((HRESULT (__stdcall*)(void*, DWORD, DWORD, DWORD, void*, void*, DWORD))g_fxO[85])(d, a, b, c, vb, decl, f); }
// state blocks: the system d3d9 has more than one state block class (CreateStateBlock / recorded ones), each with
// its own vtable - every vtable seen is hooked (DXVK has one). An Apply/Capture with states still pending would
// otherwise capture or be overwritten by stale values (broke the 2D menu with the system Direct3D 9).
struct SBVt { void** vt; void* cap; void* app; };
static SBVt g_sbVt[8]; static int g_sbVtN = 0;
static SBVt* SBFind(void* sb) { void** vt = *(void***)sb; for (int i = 0; i < g_sbVtN; ++i) if (g_sbVt[i].vt == vt) return &g_sbVt[i]; return nullptr; }
static HRESULT __stdcall hp_SBCapture(void* sb) { PEND_FLUSH(); SBVt* v = SBFind(sb); return v ? ((F_p_t)v->cap)(sb) : E_FAIL; }
static HRESULT __stdcall hp_SBApply(void* sb) { PEND_FLUSH(); SBVt* v = SBFind(sb); return v ? ((F_p_t)v->app)(sb) : E_FAIL; }
static void HookStateBlock(void* sb) {
    if (!sb || SBFind(sb)) return;
    void** vt = *(void***)sb;
    if (vt[4] == (void*)hp_SBCapture) return;
    if (g_sbVtN >= 8) { if (g_fxDeferCfg) { g_fxDeferCfg = 0; LOG("effect states: too many state block classes -> deferred restore off"); } return; }
    SBVt& e = g_sbVt[g_sbVtN++]; e.vt = vt;
    e.cap = PatchVtbl(vt, 4, (void*)hp_SBCapture); e.app = PatchVtbl(vt, 5, (void*)hp_SBApply);
    LOG("effect states: state block class %d hooked (vtable %p)", g_sbVtN, (void*)vt);
}
static HRESULT __stdcall hp_CreateSB(void* d, DWORD type, void** sb) { PEND_FLUSH(); HRESULT hr = O(59, F_u_p_t)(d, type, sb); if (hr >= 0 && sb) HookStateBlock(*sb); return hr; }
static HRESULT __stdcall hp_BeginSB(void* d) { PEND_FLUSH(); return O(60, F_p_t)(d); }
static HRESULT __stdcall hp_EndSB(void* d, void** sb) { PEND_FLUSH(); HRESULT hr = O(61, F_pp_t)(d, sb); if (hr >= 0 && sb) HookStateBlock(*sb); return hr; }
#undef O
static void FxDeviceHooks(void* dev) {
    if (g_fxHooks || !g_fxDeferCfg || !g_fxInstalled) return;
    void** vt = *(void***)dev;
    struct { int i; void* h; } hk[] = {
        { 44, (void*)hp_SetTransform }, { 45, (void*)hp_GetTransform }, { 46, (void*)hp_MulTransform }, { 49, (void*)hp_SetMaterial },
        { 50, (void*)hp_GetMaterial }, { 51, (void*)hp_SetLight }, { 52, (void*)hp_GetLight }, { 53, (void*)hp_LightEnable },
        { 54, (void*)hp_GetLightEnable }, { 57, (void*)hp_SetRS }, { 58, (void*)hp_GetRS }, { 59, (void*)hp_CreateSB },
        { 60, (void*)hp_BeginSB }, { 61, (void*)hp_EndSB }, { 64, (void*)hp_GetTexture }, { 65, (void*)hp_SetTexture },
        { 66, (void*)hp_GetTSS }, { 67, (void*)hp_SetTSS }, { 68, (void*)hp_GetSS }, { 69, (void*)hp_SetSS },
        { 79, (void*)hp_SetNPatch }, { 80, (void*)hp_GetNPatch }, { 81, (void*)hp_DP }, { 82, (void*)hp_DIP },
        { 83, (void*)hp_DPUP }, { 84, (void*)hp_DIPUP }, { 85, (void*)hp_ProcessVertices }, { 87, (void*)hp_SetDecl },
        { 88, (void*)hp_GetDecl }, { 89, (void*)hp_SetFVF }, { 90, (void*)hp_GetFVF }, { 92, (void*)hp_SetVS },
        { 93, (void*)hp_GetVS }, { 107, (void*)hp_SetPS }, { 108, (void*)hp_GetPS }, { 42, (void*)hp_EndScene }, { 43, (void*)hp_Clear },
    };
    for (auto& h : hk) g_fxO[h.i] = PatchVtbl(vt, h.i, h.h);
    g_fxHooks = true;
    LOG("effect states: deferred restore active (device hooks installed)");
}

// value about to be set == current device value?  (first touch also remembers the original value)
static bool FxSame(FxSess* s, DWORD key, const void* nv) {
    void* dev = *pDevice; int sz = FxSize(key);
    FxEntry* e = nullptr;
    int sl = FxSlot(key);
    if (sl >= 0) { if (s->slotGen[sl] == s->gen) e = &s->e[s->slotIdx[sl]]; }
    else for (int i = 0; i < s->n; ++i) if (s->e[i].key == key) { e = &s->e[i]; break; }
    if (!e) {
        if (s->n >= FX_MAXE) { if (g_pendN) FxFlush(); return false; }   // table full: just forward (never skip)
        if (sl >= 0) { s->slotGen[sl] = s->gen; s->slotIdx[sl] = (BYTE)s->n; }
        e = &s->e[s->n++]; e->key = key; e->ref = nullptr;
        int pi = g_pendN ? PendFind(key) : -1;
        if (pi >= 0) {                                                    // pending from an earlier effect: that is our original
            FxEntry& p = g_pend[pi];
            memcpy(e->s0, p.s0, sizeof e->s0); e->ref = p.ref; e->ok = p.ok; p.ref = nullptr;
            PendRemove(pi, false); ++g_fxTaken;
            BYTE cur[104]; if (!FxGet(dev, key, cur, nullptr)) return false;
            return !memcmp(cur, nv, sz);
        }
        e->ok = FxGet(dev, key, e->s0, &e->ref);
        if (!e->ok) return false;
        return !memcmp(e->s0, nv, sz);
    }
    if (g_pendN) { int pi = PendFind(key); if (pi >= 0) PendRemove(pi, true); }   // left pending by a nested effect: ours now
    BYTE cur[104]; if (!FxGet(dev, key, cur, nullptr)) return false;
    return !memcmp(cur, nv, sz);
}
static void FxRestore(void* dev, FxEntry& e) {   // set the remembered value back if it differs from the current one
    if (!e.ok) return;
    BYTE cur[104];
    if (FxGet(dev, e.key, cur, nullptr) && !memcmp(cur, e.s0, FxSize(e.key))) return;
    SMEntry tmp; tmp.key = e.key; tmp.n = 1; tmp.ref = e.ref; memcpy(tmp.s0, e.s0, sizeof tmp.s0);
    ++g_fxIn; SMRestore(dev, tmp); --g_fxIn; ++g_fxRestored;
}

#define FXS FxSess* s = (FxSess*)t; void* dev = *pDevice
#define FX_FWD(cond, call) do { if (cond) { ++g_fxSkipped; return S_OK; } ++g_fxForwarded; return call; } while (0)
static HRESULT __stdcall FX_QI(void* t, const GUID*, void** o) { *o = t; return S_OK; }
static ULONG __stdcall FX_AddRef(void*) { return 1; }
static ULONG __stdcall FX_Release(void*) { return 1; }
static HRESULT __stdcall FX_SetTransform(void* t, DWORD st, const void* m) { FXS; FX_FWD(FxSame(s, SMKey(SM_XF, 0, st), m), DEVF(44, D_u_p)(dev, st, (void*)m)); }
static HRESULT __stdcall FX_SetMaterial(void* t, const void* m) { FXS; FX_FWD(FxSame(s, SMKey(SM_MAT, 0, 0), m), DEVF(49, D_p)(dev, (void*)m)); }
static HRESULT __stdcall FX_SetLight(void* t, DWORD i, const void* l) { FXS; FX_FWD(FxSame(s, SMKey(SM_LIGHT, 0, i), l), DEVF(51, D_u_p)(dev, i, (void*)l)); }
static HRESULT __stdcall FX_LightEnable(void* t, DWORD i, BOOL en) { FXS; DWORD v = en ? 1 : 0; BOOL same = FxSame(s, SMKey(SM_LE, 0, i), &v);
    if (same) { ++g_fxSkipped; return S_OK; }
    // GetLightEnable returns any non-zero value for "on": compare as booleans
    ++g_fxForwarded; return DEVF(53, D_u_u)(dev, i, en); }
static HRESULT __stdcall FX_SetRenderState(void* t, DWORD st, DWORD v) { FXS; FX_FWD(FxSame(s, SMKey(SM_RS, 0, st), &v), DEVF(57, D_u_u)(dev, st, v)); }
static HRESULT __stdcall FX_SetTexture(void* t, DWORD st, void* tx) { FXS; FX_FWD(FxSame(s, SMKey(SM_TEX, 0, st), &tx), DEVF(65, D_u_p)(dev, st, tx)); }
static HRESULT __stdcall FX_SetTSS(void* t, DWORD st, DWORD ty, DWORD v) { FXS; FX_FWD(FxSame(s, SMKey(SM_TSS, st, ty), &v), DEVF(67, D_u_u_u)(dev, st, ty, v)); }
static HRESULT __stdcall FX_SetSS(void* t, DWORD sm, DWORD ty, DWORD v) {
    FXS; DWORD dv = v;                                                   // what the device will really hold (anisotropic filtering)
    if (sm < 16 && AnisoLevel()) { if (ty == 6 && v == 2) dv = 3; else if (ty == 10) dv = AnisoLevel(); }
    FX_FWD(FxSame(s, SMKey(SM_SS, sm, ty), &dv), DEVF(69, D_u_u_u)(dev, sm, ty, v)); }
static HRESULT __stdcall FX_SetNPatch(void* t, float nps) { FXS; FX_FWD(FxSame(s, SMKey(SM_NP, 0, 0), &nps), ((HRESULT (__stdcall*)(void*, float))(*(void***)dev)[79])(dev, nps)); }
static HRESULT __stdcall FX_SetFVF(void* t, DWORD f) { FXS; FX_FWD(FxSame(s, SMKey(SM_FVF, 0, 0), &f), DEVF(89, D_u)(dev, f)); }
static HRESULT __stdcall FX_SetVS(void* t, void* sh) { FXS; FX_FWD(FxSame(s, SMKey(SM_VS, 0, 0), &sh), DEVF(92, D_p)(dev, sh)); }
static HRESULT __stdcall FX_SetPS(void* t, void* sh) { FXS; FX_FWD(FxSame(s, SMKey(SM_PS, 0, 0), &sh), DEVF(107, D_p)(dev, sh)); }
// Shader constants: one ranged Get + compare, forwarded when anything differs. They are not remembered/restored:
// every effect pass uploads all constants its shaders use and the rest of the game renders fixed-function, so
// nothing reads constants left by a previous effect (and skinned meshes upload hundreds of registers per draw).
static BYTE g_fxCbuf[256 * 16];
static bool FxConstsSame(int getIdx, DWORD reg, const void* d, DWORD cnt, int per) {
    if (!cnt || cnt * per > sizeof g_fxCbuf) return false;
    void* dev = *pDevice;
    if (DEVF(getIdx, D_u_p_u)(dev, reg, g_fxCbuf, cnt) < 0) return false;
    return !memcmp(g_fxCbuf, d, cnt * per);
}
static HRESULT __stdcall FX_VCF(void* t, DWORD r, const void* d, DWORD c) { FXS; (void)s; FX_FWD(FxConstsSame(95, r, d, c, 16), DEVF(94, D_u_p_u)(dev, r, d, c)); }
static HRESULT __stdcall FX_VCI(void* t, DWORD r, const void* d, DWORD c) { FXS; (void)s; FX_FWD(FxConstsSame(97, r, d, c, 16), DEVF(96, D_u_p_u)(dev, r, d, c)); }
static HRESULT __stdcall FX_VCB(void* t, DWORD r, const void* d, DWORD c) { FXS; (void)s; FX_FWD(FxConstsSame(99, r, d, c, 4), DEVF(98, D_u_p_u)(dev, r, d, c)); }
static HRESULT __stdcall FX_PCF(void* t, DWORD r, const void* d, DWORD c) { FXS; (void)s; FX_FWD(FxConstsSame(110, r, d, c, 16), DEVF(109, D_u_p_u)(dev, r, d, c)); }
static HRESULT __stdcall FX_PCI(void* t, DWORD r, const void* d, DWORD c) { FXS; (void)s; FX_FWD(FxConstsSame(112, r, d, c, 16), DEVF(111, D_u_p_u)(dev, r, d, c)); }
static HRESULT __stdcall FX_PCB(void* t, DWORD r, const void* d, DWORD c) { FXS; (void)s; FX_FWD(FxConstsSame(114, r, d, c, 4), DEVF(113, D_u_p_u)(dev, r, d, c)); }

typedef void (__fastcall *CEBegin_t)(BYTE* ce, void* edx, UINT* passes, DWORD flags);
typedef void (__fastcall *CEEnd_t)(BYTE* ce, void* edx);
static CEBegin_t o_CEBegin = nullptr; static CEEnd_t o_CEEnd = nullptr;
struct FxCaller { DWORD ra; DWORD n; };
static FxCaller g_fxCallers[64];
static void FxCountCaller(DWORD ra) {
    for (int i = 0; i < 64; ++i) { if (g_fxCallers[i].ra == ra) { ++g_fxCallers[i].n; return; } if (!g_fxCallers[i].ra) { g_fxCallers[i].ra = ra; g_fxCallers[i].n = 1; return; } }
}
// billboard batching (billboard.inc): one Begin/BeginPass for consecutive fading billboard trees
static bool g_bbMode = false, g_bbOpen = false, g_bbClosing = false; static BYTE* g_bbCe = nullptr;
static UINT g_bbPasses = 0; static int g_bbPass = -1; static DWORD g_bbBegins = 0, g_bbKept = 0;
static void CEBeginImpl(BYTE* ce, void* edx, UINT* passes, DWORD flags);
static void BBClose();
static void __fastcall h_CEBegin(BYTE* ce, void* edx, UINT* passes, DWORD flags) {
    FxCountCaller((DWORD)(uintptr_t)__builtin_return_address(0));
    if (!g_bbMode) { CEBeginImpl(ce, edx, passes, flags); return; }
    if (g_bbOpen && ce == g_bbCe) { if (passes) *passes = g_bbPasses; ++g_bbKept; return; }   // still open: no new Begin
    BBClose();
    CEBeginImpl(ce, edx, passes, flags);
    g_bbOpen = true; g_bbCe = ce; g_bbPasses = passes ? *passes : 0; g_bbPass = -1; ++g_bbBegins;
}
static void CEBeginImpl(BYTE* ce, void* edx, UINT* passes, DWORD flags) {
    void* fx = *(void**)(ce + 0x20);
    FxSess* s = nullptr;
    if (g_optFx && flags == 0 && fx) {
        for (int i = 0; i < FX_SESS; ++i) if (g_fxs[i].used && g_fxs[i].fx == fx) { s = nullptr; goto plain; }   // nested Begin of the same effect
        for (int i = 0; i < FX_SESS; ++i) if (!g_fxs[i].used) { s = &g_fxs[i]; break; }
        if (s) {
            void* old = nullptr; ((HRESULT (__stdcall*)(void*, void**))(*(void***)fx)[72])(fx, &old);
            if (old) { ComRelease(old); s = nullptr; }
            else {
                s->vt = g_fxVtbl; s->fx = fx; s->used = true; s->n = 0; s->gen = ++g_fxGen;
                ((HRESULT (__stdcall*)(void*, void*))(*(void***)fx)[71])(fx, s);
                ++g_fxBegins;
                o_CEBegin(ce, edx, passes, 1 /*D3DXFX_DONOTSAVESTATE*/);
                return;
            }
        }
    }
plain:
    if (g_pendN) FxFlush();
    o_CEBegin(ce, edx, passes, flags);
}
static void __fastcall h_CEEnd(BYTE* ce, void* edx) {
    if (g_bbOpen && ce == g_bbCe && !g_bbClosing) return;               // billboard batch: End when the batch closes
    void* fx = *(void**)(ce + 0x20);
    o_CEEnd(ce, edx);
    for (int i = 0; i < FX_SESS; ++i) {
        FxSess* s = &g_fxs[i];
        if (!s->used || s->fx != fx) continue;
        void* dev = *pDevice;
        if (FxDefer()) {
            for (int k = 0; k < s->n; ++k) {
                FxEntry& e = s->e[k];
                if (!e.ok) { ComRelease(e.ref); continue; }
                int pi = g_pendN ? PendFind(e.key) : -1;
                if (pi >= 0) {                                            // nested sessions: the outer original wins
                    FxEntry& p = g_pend[pi]; ComRelease(p.ref);
                    memcpy(p.s0, e.s0, sizeof p.s0); p.ref = e.ref; p.ok = e.ok; e.ref = nullptr;
                    continue;
                }
                BYTE cur[104];
                if (FxGet(dev, e.key, cur, nullptr) && !memcmp(cur, e.s0, FxSize(e.key))) { ComRelease(e.ref); continue; }
                PendAdd(dev, e);
            }
        } else {
            if (g_pendN) FxFlush();
            for (int k = 0; k < s->n; ++k) { FxRestore(dev, s->e[k]); ComRelease(s->e[k].ref); }
        }
        ((HRESULT (__stdcall*)(void*, void*))(*(void***)fx)[71])(fx, nullptr);
        s->used = false; s->n = 0; s->fx = nullptr;
        break;
    }
}
static void FxReleaseAll() {   // device Reset: no effect session may keep references to device resources
    PendClear();
    for (int i = 0; i < FX_SESS; ++i) {
        FxSess* s = &g_fxs[i]; if (!s->used) continue;
        for (int k = 0; k < s->n; ++k) ComRelease(s->e[k].ref);
        ((HRESULT (__stdcall*)(void*, void*))(*(void***)s->fx)[71])(s->fx, nullptr);
        s->used = false; s->n = 0; s->fx = nullptr;
        LOG("effect states: session left open at device reset released");
    }
}
static void InstallEffectStates() {
    void* v[21] = { (void*)FX_QI, (void*)FX_AddRef, (void*)FX_Release, (void*)FX_SetTransform, (void*)FX_SetMaterial, (void*)FX_SetLight,
        (void*)FX_LightEnable, (void*)FX_SetRenderState, (void*)FX_SetTexture, (void*)FX_SetTSS, (void*)FX_SetSS, (void*)FX_SetNPatch, (void*)FX_SetFVF,
        (void*)FX_SetVS, (void*)FX_VCF, (void*)FX_VCI, (void*)FX_VCB, (void*)FX_SetPS, (void*)FX_PCF, (void*)FX_PCI, (void*)FX_PCB };
    memcpy(g_fxVtbl, v, sizeof v);
    static const BYTE pb[7] = { 0x8B, 0x54, 0x24, 0x08, 0x8B, 0x41, 0x20 };
    static const BYTE pe[5] = { 0x8B, 0x41, 0x20, 0x8B, 0x08 };
    if (false) { g_optFx = 0; LOG("effect states: unexpected code, not installed"); return; }
    o_CEBegin = (CEBegin_t)Detour((BYTE*)nullptr, pb, 7, (void*)h_CEBegin);
    o_CEEnd = (CEEnd_t)Detour((BYTE*)nullptr, pe, 5, (void*)h_CEEnd);
    g_fxInstalled = o_CEBegin && o_CEEnd;
    LOG("effect states: lazy save/restore installed (EffectStates=%d)", g_optFx);
}
static void EffectStats() {
    PLOG("EFFECTS lazy=%d defer=%d: begins=%lu states forwarded=%lu skipped (unchanged)=%lu restored at End=%lu | deferred=%lu taken by next effect=%lu applied later=%lu (%lu flushes) dropped (game set)=%lu",
         g_optFx, FxDefer() ? 1 : 0, g_fxBegins, g_fxForwarded, g_fxSkipped, g_fxRestored, g_fxDeferred, g_fxTaken, g_fxFlushed, g_fxFlushes, g_fxDropped);
    {   char b[600]; int n = 0; b[0] = 0;
        for (int t = 0; t < 8; ++t) {
            int best = -1; for (int i = 0; i < 64; ++i) if (g_fxCallers[i].n && (best < 0 || g_fxCallers[i].n > g_fxCallers[best].n)) best = i;
            if (best < 0) break;
            n += snprintf(b + n, sizeof b - n, " %08lX=%lu", g_fxCallers[best].ra, g_fxCallers[best].n); g_fxCallers[best].n = 0;
        }
        memset(g_fxCallers, 0, sizeof g_fxCallers);
        if (n) PLOG("EFFECTS Begin callers (return address=count):%s", b);
    }
    g_fxBegins = g_fxForwarded = g_fxSkipped = g_fxRestored = 0; g_fxDeferred = g_fxTaken = g_fxFlushed = g_fxFlushes = g_fxDropped = 0;
}
// ---------------- fake COM object (texture / shader)
struct Obj { void** vt; int refs; int id; };
static int g_noRef = 0;
static ULONG __stdcall ObjAdd(Obj* o) { if (g_noRef) return 1; return ++o->refs; }
static ULONG __stdcall ObjRel(Obj* o) { if (g_noRef) return 1; if (o->refs <= 0) { printf("REFCOUNT UNDERFLOW obj %d\n", o->id); exit(1); } return --o->refs; }
static void* g_objVt[3] = { nullptr, (void*)ObjAdd, (void*)ObjRel };
static Obj g_objs[8];
// ---------------- fake device: plain state storage
struct Dev {
    void** vt;
    DWORD rs[256], tss[8][33], ss[21][14], le[8], fvf; void* tex[21]; void* vs; void* ps; BYTE xf[8][64]; BYTE mat[68]; BYTE light[8][104]; float np;
    float vcf[256][4]; float pcf[224][4]; int vci[16][4]; int pci[16][4]; BOOL vcb[16], pcb[16];
};
static int SmpIdx(DWORD s) { return s < 16 ? (int)s : (int)(s - 240); }
static int XfIdx(DWORD st) { return st == 2 ? 0 : st == 3 ? 1 : st == 256 ? 2 : 3; }
#define D Dev* d = (Dev*)dv
static HRESULT __stdcall dSetXF(void* dv, DWORD st, void* m) { D; memcpy(d->xf[XfIdx(st)], m, 64); return 0; }
static HRESULT __stdcall dGetXF(void* dv, DWORD st, void* m) { D; memcpy(m, d->xf[XfIdx(st)], 64); return 0; }
static HRESULT __stdcall dMulXF(void* dv, DWORD st, void* m) { D; float* a = (float*)d->xf[XfIdx(st)]; a[0] += ((float*)m)[0]; return 0; }
static HRESULT __stdcall dSetMat(void* dv, void* m) { D; memcpy(d->mat, m, 68); return 0; }
static HRESULT __stdcall dGetMat(void* dv, void* m) { D; memcpy(m, d->mat, 68); return 0; }
static HRESULT __stdcall dSetLight(void* dv, DWORD i, void* l) { D; memcpy(d->light[i], l, 104); return 0; }
static HRESULT __stdcall dGetLight(void* dv, DWORD i, void* l) { D; memcpy(l, d->light[i], 104); return 0; }
static HRESULT __stdcall dLE(void* dv, DWORD i, DWORD e) { D; d->le[i] = e ? 128 : 0; return 0; }
static HRESULT __stdcall dGetLE(void* dv, DWORD i, DWORD* e) { D; *e = d->le[i]; return 0; }
static HRESULT __stdcall dSetRS(void* dv, DWORD st, DWORD v) { D; d->rs[st] = v; return 0; }
static HRESULT __stdcall dGetRS(void* dv, DWORD st, DWORD* v) { D; *v = d->rs[st]; return 0; }
static HRESULT __stdcall dGetTex(void* dv, DWORD st, void** t) { D; *t = d->tex[SmpIdx(st)]; if (*t) ObjAdd((Obj*)*t); return 0; }
static HRESULT __stdcall dSetTex(void* dv, DWORD st, void* t) { D; void*& s = d->tex[SmpIdx(st)]; if (t) ObjAdd((Obj*)t); if (s) ObjRel((Obj*)s); s = t; return 0; }
static HRESULT __stdcall dGetTSS(void* dv, DWORD s, DWORD t, DWORD* v) { D; *v = d->tss[s][t]; return 0; }
static HRESULT __stdcall dSetTSS(void* dv, DWORD s, DWORD t, DWORD v) { D; d->tss[s][t] = v; return 0; }
static HRESULT __stdcall dGetSS(void* dv, DWORD s, DWORD t, DWORD* v) { D; *v = d->ss[SmpIdx(s)][t]; return 0; }
static HRESULT __stdcall dSetSS(void* dv, DWORD s, DWORD t, DWORD v) { D; d->ss[SmpIdx(s)][t] = v; return 0; }
static HRESULT __stdcall dSetNP(void* dv, float n) { D; d->np = n; return 0; }
static float __stdcall dGetNP(void* dv) { D; return d->np; }
static HRESULT __stdcall dSetDecl(void* dv, void*) { D; d->fvf = 0; return 0; }
static HRESULT __stdcall dGetDecl(void* dv, void** p) { *p = nullptr; return 0; }
static HRESULT __stdcall dSetFVF(void* dv, DWORD f) { D; d->fvf = f; return 0; }
static HRESULT __stdcall dGetFVF(void* dv, DWORD* f) { D; *f = d->fvf; return 0; }
static HRESULT __stdcall dSetVS(void* dv, void* s) { D; if (s) ObjAdd((Obj*)s); if (d->vs) ObjRel((Obj*)d->vs); d->vs = s; return 0; }
static HRESULT __stdcall dGetVS(void* dv, void** s) { D; *s = d->vs; if (*s) ObjAdd((Obj*)*s); return 0; }
static HRESULT __stdcall dSetPS(void* dv, void* s) { D; if (s) ObjAdd((Obj*)s); if (d->ps) ObjRel((Obj*)d->ps); d->ps = s; return 0; }
static HRESULT __stdcall dGetPS(void* dv, void** s) { D; *s = d->ps; if (*s) ObjAdd((Obj*)*s); return 0; }
static HRESULT __stdcall dSetVCF(void* dv, DWORD r, const void* p, DWORD c) { D; memcpy(d->vcf[r], p, c * 16); return 0; }
static HRESULT __stdcall dGetVCF(void* dv, DWORD r, void* p, DWORD c) { D; memcpy(p, d->vcf[r], c * 16); return 0; }
static HRESULT __stdcall dSetPCF(void* dv, DWORD r, const void* p, DWORD c) { D; memcpy(d->pcf[r], p, c * 16); return 0; }
static HRESULT __stdcall dGetPCF(void* dv, DWORD r, void* p, DWORD c) { D; memcpy(p, d->pcf[r], c * 16); return 0; }
static HRESULT __stdcall dNop0(void*) { return 0; }
static HRESULT __stdcall dNop2(void*, DWORD, void*) { return 0; }
// snapshot at draw
static int g_draws = 0;
static HRESULT __stdcall dDraw(void*, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD) { ++g_draws; return 0; }
static HRESULT __stdcall dDP(void*, DWORD, DWORD, DWORD) { ++g_draws; return 0; }
static HRESULT __stdcall dClear(void*, DWORD, void*, DWORD, DWORD, DWORD, DWORD) { return 0; }
struct SB { void** vt; Dev saved; Dev* dev; };
static void* g_fakeSbVt[6];
static HRESULT __stdcall sbCapture(SB* sb) { sb->saved = *sb->dev; return 0; }
static HRESULT __stdcall sbApply(SB* sb) { sb->dev->rs[0] = sb->dev->rs[0]; return 0; }   // not used for state here
static HRESULT __stdcall dCreateSB(void* dv, DWORD, void** sb) { SB* s = new SB; s->vt = g_fakeSbVt; s->dev = (Dev*)dv; *sb = s; return 0; }
static void* g_devVt[120];
static void InitDev(Dev* d) {
    memset(d, 0, sizeof *d); d->vt = g_devVt; d->fvf = 1;
}
static void InitVt() {
    for (int i = 0; i < 120; ++i) g_devVt[i] = (void*)dNop0;
    g_devVt[44] = (void*)dSetXF; g_devVt[45] = (void*)dGetXF; g_devVt[46] = (void*)dMulXF; g_devVt[49] = (void*)dSetMat; g_devVt[50] = (void*)dGetMat;
    g_devVt[51] = (void*)dSetLight; g_devVt[52] = (void*)dGetLight; g_devVt[53] = (void*)dLE; g_devVt[54] = (void*)dGetLE; g_devVt[57] = (void*)dSetRS; g_devVt[58] = (void*)dGetRS;
    g_devVt[59] = (void*)dCreateSB; g_devVt[60] = (void*)dNop0; g_devVt[61] = (void*)dNop2;
    g_devVt[64] = (void*)dGetTex; g_devVt[65] = (void*)dSetTex; g_devVt[66] = (void*)dGetTSS; g_devVt[67] = (void*)dSetTSS; g_devVt[68] = (void*)dGetSS; g_devVt[69] = (void*)dSetSS;
    g_devVt[79] = (void*)dSetNP; g_devVt[80] = (void*)dGetNP; g_devVt[81] = (void*)dDP; g_devVt[82] = (void*)dDraw; g_devVt[83] = (void*)dDP; g_devVt[84] = (void*)dDraw; g_devVt[85] = (void*)dDraw;
    g_devVt[87] = (void*)dSetDecl; g_devVt[88] = (void*)dGetDecl; g_devVt[89] = (void*)dSetFVF; g_devVt[90] = (void*)dGetFVF; g_devVt[92] = (void*)dSetVS; g_devVt[93] = (void*)dGetVS;
    g_devVt[94] = (void*)dSetVCF; g_devVt[95] = (void*)dGetVCF; g_devVt[107] = (void*)dSetPS; g_devVt[108] = (void*)dGetPS; g_devVt[109] = (void*)dSetPCF; g_devVt[110] = (void*)dGetPCF;
    g_devVt[42] = (void*)dNop0; g_devVt[43] = (void*)dClear;
    g_fakeSbVt[1] = g_fakeSbVt[2] = (void*)dNop0; g_fakeSbVt[4] = (void*)sbCapture; g_fakeSbVt[5] = (void*)sbApply;
}
struct Dev; extern Dev g_ref;
// ---------------- state ops (key, value) applied through: manager / device vtable
struct Op { int type; DWORD a, b; DWORD v; };
static void* ObjOf(DWORD v) { return v ? (void*)&g_objs[v] : nullptr; }
static void DevApply(void* dev, const Op& o) {   // through the (possibly hooked) device vtable
    struct G { bool on; G(bool b) : on(b) { if (on) ++g_noRef; } ~G() { if (on) --g_noRef; } } g(dev == (void*)&g_ref);
    switch (o.type) {
    case SM_RS: DEVF(57, D_u_u)(dev, o.b, o.v); break;
    case SM_TSS: DEVF(67, D_u_u_u)(dev, o.a, o.b, o.v); break;
    case SM_SS: DEVF(69, D_u_u_u)(dev, o.a, o.b, o.v); break;
    case SM_TEX: DEVF(65, D_u_p)(dev, o.b, ObjOf(o.v)); break;
    case SM_FVF: DEVF(89, D_u)(dev, o.v); break;
    case SM_VS: DEVF(92, D_p)(dev, ObjOf(o.v)); break;
    case SM_PS: DEVF(107, D_p)(dev, ObjOf(o.v)); break;
    case SM_LE: DEVF(53, D_u_u)(dev, o.b, o.v); break;
    case SM_XF: { float m[16] = { (float)o.v }; DEVF(44, D_u_p)(dev, o.b, m); break; }
    }
}
static void MgrApply(void** mgr, const Op& o) {  // through ID3DXEffectStateManager
    void** vt = *(void***)mgr;
    switch (o.type) {
    case SM_RS: ((HRESULT(*)(void*, DWORD, DWORD))vt[7])(mgr, o.b, o.v); break;
    case SM_TSS: ((HRESULT(*)(void*, DWORD, DWORD, DWORD))vt[9])(mgr, o.a, o.b, o.v); break;
    case SM_SS: ((HRESULT(*)(void*, DWORD, DWORD, DWORD))vt[10])(mgr, o.a, o.b, o.v); break;
    case SM_TEX: ((HRESULT(*)(void*, DWORD, void*))vt[8])(mgr, o.b, ObjOf(o.v)); break;
    case SM_FVF: ((HRESULT(*)(void*, DWORD))vt[12])(mgr, o.v); break;
    case SM_VS: ((HRESULT(*)(void*, void*))vt[13])(mgr, ObjOf(o.v)); break;
    case SM_PS: ((HRESULT(*)(void*, void*))vt[17])(mgr, ObjOf(o.v)); break;
    case SM_LE: ((HRESULT(*)(void*, DWORD, BOOL))vt[6])(mgr, o.b, o.v); break;
    case SM_XF: { float m[16] = { (float)o.v }; ((HRESULT(*)(void*, DWORD, const void*))vt[3])(mgr, o.b, m); break; }
    }
}
static Op RandOp() {
    Op o; o.type = 0; o.a = o.b = 0; int r = rand() % 9;
    switch (r) {
    case 0: o.type = SM_RS; o.b = rand() % 6; o.v = rand() % 3; break;
    case 1: o.type = SM_TSS; o.a = rand() % 2; o.b = 1 + rand() % 3; o.v = rand() % 3; break;
    case 2: o.type = SM_SS; o.a = rand() % 2; o.b = 5 + rand() % 3; o.v = rand() % 3; break;
    case 3: o.type = SM_TEX; o.b = rand() % 3; o.v = rand() % 4; break;
    case 4: o.type = SM_FVF; o.v = 1 + rand() % 3; break;
    case 5: o.type = SM_VS; o.v = rand() % 3; break;
    case 6: o.type = SM_PS; o.v = rand() % 3; break;
    case 7: o.type = SM_LE; o.b = rand() % 2; o.v = rand() % 2; break;
    default: o.type = SM_XF; o.b = (rand() % 2) ? 256 : 2; o.v = rand() % 3; break;
    }
    return o;
}
// compare logically relevant state of two devices
static bool Same(const Dev* a, const Dev* b, const char* where, int step) {
    bool ok = true;
    for (int i = 0; i < 6; ++i) if (a->rs[i] != b->rs[i]) { printf("%s step %d: RS%d %u vs %u\n", where, step, i, a->rs[i], b->rs[i]); ok = false; }
    for (int s = 0; s < 2; ++s) for (int t = 1; t < 4; ++t) if (a->tss[s][t] != b->tss[s][t]) { printf("%s step %d: TSS%d/%d\n", where, step, s, t); ok = false; }
    for (int s = 0; s < 2; ++s) for (int t = 5; t < 8; ++t) if (a->ss[s][t] != b->ss[s][t]) { printf("%s step %d: SS%d/%d\n", where, step, s, t); ok = false; }
    for (int i = 0; i < 3; ++i) if (a->tex[i] != b->tex[i]) { printf("%s step %d: TEX%d\n", where, step, i); ok = false; }
    if (a->fvf != b->fvf) { printf("%s step %d: FVF %u vs %u\n", where, step, a->fvf, b->fvf); ok = false; }
    if (a->vs != b->vs) { printf("%s step %d: VS\n", where, step); ok = false; }
    if (a->ps != b->ps) { printf("%s step %d: PS\n", where, step); ok = false; }
    for (int i = 0; i < 2; ++i) if ((a->le[i] != 0) != (b->le[i] != 0)) { printf("%s step %d: LE%d\n", where, step, i); ok = false; }
    for (int i = 0; i < 2; ++i) if (memcmp(a->xf[i], b->xf[i], 64)) { printf("%s step %d: XF%d\n", where, step, i); ok = false; }
    return ok;
}
// ---------------- fake effect objects
struct FakeFx { void** vt; void* mgr; };
static HRESULT __stdcall fxSetMgr(FakeFx* f, void* m) { f->mgr = m; return 0; }
static HRESULT __stdcall fxGetMgr(FakeFx* f, void** m) { *m = f->mgr; return 0; }   // our sessions don't count refs
static void* g_fxVt[80];
struct CE { BYTE pad[0x20]; FakeFx* fx; };
struct ActiveFx { CE* ce; std::vector<std::vector<Op>> passes; bool plain; Dev refSaved; std::vector<Op> keys; SB* sb; };
static std::vector<ActiveFx*> g_stack;
static DWORD g_lastFlags = 0;
static void __fastcall fakeBegin(BYTE* ce, void*, UINT* passes, DWORD flags) { g_lastFlags = flags; *passes = 1; }
static void __fastcall fakeEnd(BYTE*, void*) {}
// reference device + implementation device
Dev g_ref; static Dev g_impl;
int main(int argc, char** argv) {
    void* dev = &g_impl; (void)dev;
    int seed = argc > 1 ? atoi(argv[1]) : 1; srand(seed);
    for (int i = 0; i < 8; ++i) { g_objs[i].vt = g_objVt; g_objs[i].refs = 1000; g_objs[i].id = i; }
    InitVt(); for (int i = 0; i < 80; ++i) g_fxVt[i] = (void*)dNop0; g_fxVt[71] = (void*)fxSetMgr; g_fxVt[72] = (void*)fxGetMgr;
    InitDev(&g_ref); InitDev(&g_impl);
    // the hooks patch the shared vtable: give the reference device its own unhooked copy
    static void* refVt[120]; memcpy(refVt, g_devVt, sizeof refVt); g_ref.vt = refVt;
    g_devPtr = &g_impl;
    InstallEffectStates();
    o_CEBegin = (CEBegin_t)fakeBegin; o_CEEnd = (CEEnd_t)fakeEnd; g_fxInstalled = true;
    g_fxDeferCfg = argc > 2 ? atoi(argv[2]) : 1;
    FxDeviceHooks(&g_impl);
    FakeFx fxs[4]; CE ces[4];
    for (int i = 0; i < 4; ++i) { fxs[i].vt = g_fxVt; fxs[i].mgr = nullptr; ces[i].fx = &fxs[i]; }
    int steps = 20000, fails = 0;
    for (int step = 0; step < steps && fails < 5; ++step) {
        int r = rand() % 100;
        if (r < 25 && g_stack.size() < 2) {                // Begin an effect (pass states)
            int fi = rand() % 4; bool busy = false; for (auto* a : g_stack) if (a->ce == &ces[fi]) busy = true;
            if (busy) continue;
            ActiveFx* a = new ActiveFx; a->ce = &ces[fi]; a->plain = (rand() % 10) == 0;
            int np = 1 + rand() % 2; a->passes.resize(np);
            for (int p = 0; p < np; ++p) { int n = 1 + rand() % 8; for (int k = 0; k < n; ++k) a->passes[p].push_back(RandOp()); }
            for (auto& p : a->passes) for (auto& o : p) a->keys.push_back(o);
            a->refSaved = g_ref;                            // reference: D3DX captures the touched states at Begin
            UINT passes;
            h_CEBegin((BYTE*)a->ce, nullptr, &passes, a->plain ? 1 : 0);   // plain: other flags -> no session
            if (a->plain) { a->sb = nullptr; void* sb; DEVF(59, D_u_p)(&g_impl, 1, &sb); a->sb = (SB*)sb; ((HRESULT(*)(void*))a->sb->vt[4])(a->sb); }
            g_stack.push_back(a);
            // run a pass immediately: BeginPass sets all pass states, then 1-2 draws
            for (auto& p : a->passes) {
                for (auto& o : p) { DevApply(&g_ref, o); if (a->ce->fx->mgr && !a->plain) MgrApply((void**)a->ce->fx->mgr, o); else DevApply(&g_impl, o); }
                int nd = rand() % 3;
                for (int k = 0; k < nd; ++k) {
                    
                    DEVF(82, D_u_u_u)(&g_impl, 0, 0, 0); ++g_draws;
                    if (!Same(&g_ref, &g_impl, "draw in effect", step)) ++fails;
                }
            }
        } else if (r < 45 && !g_stack.empty()) {            // End the innermost effect
            ActiveFx* a = g_stack.back(); g_stack.pop_back();
            // reference: restore exactly the touched states to their values at Begin
            for (auto& o : a->keys) {
                Op ro = o;
                switch (o.type) {
                case SM_RS: dSetRS(&g_ref, o.b, a->refSaved.rs[o.b]); break;
                case SM_TSS: dSetTSS(&g_ref, o.a, o.b, a->refSaved.tss[o.a][o.b]); break;
                case SM_SS: dSetSS(&g_ref, o.a, o.b, a->refSaved.ss[o.a][o.b]); break;
                case SM_TEX: { void* t = a->refSaved.tex[o.b]; void*& s = g_ref.tex[o.b]; s = t; break; }
                case SM_FVF: g_ref.fvf = a->refSaved.fvf; break;
                case SM_VS: g_ref.vs = a->refSaved.vs; break;
                case SM_PS: g_ref.ps = a->refSaved.ps; break;
                case SM_LE: g_ref.le[o.b] = a->refSaved.le[o.b]; break;
                case SM_XF: memcpy(g_ref.xf[XfIdx(o.b)], a->refSaved.xf[XfIdx(o.b)], 64); break;
                }
                (void)ro;
            }
            h_CEEnd((BYTE*)a->ce, nullptr);
            if (a->plain) {   // D3DX applies its state block (only the touched states, captured at Begin)
                ((HRESULT(*)(void*))a->sb->vt[5])(a->sb);
                Dev& sv = a->sb->saved;
                for (auto& o : a->keys) {
                    switch (o.type) {
                    case SM_RS: dSetRS(&g_impl, o.b, sv.rs[o.b]); break;
                    case SM_TSS: dSetTSS(&g_impl, o.a, o.b, sv.tss[o.a][o.b]); break;
                    case SM_SS: dSetSS(&g_impl, o.a, o.b, sv.ss[o.a][o.b]); break;
                    case SM_TEX: dSetTex(&g_impl, o.b, sv.tex[o.b]); break;
                    case SM_FVF: g_impl.fvf = sv.fvf; break;
                    case SM_VS: dSetVS(&g_impl, sv.vs); break;
                    case SM_PS: dSetPS(&g_impl, sv.ps); break;
                    case SM_LE: g_impl.le[o.b] = sv.le[o.b]; break;
                    case SM_XF: memcpy(g_impl.xf[XfIdx(o.b)], sv.xf[XfIdx(o.b)], 64); break;
                    }
                }
                delete a->sb;
            }
            delete a;
        } else if (r < 70) {                                // game sets a state directly
            Op o = RandOp(); DevApply(&g_ref, o); DevApply(&g_impl, o);
        } else if (r < 90) {                                // game draws
            DEVF(82, D_u_u_u)(&g_impl, 0, 0, 0);
            if (!Same(&g_ref, &g_impl, "draw", step)) ++fails;
        } else if (r < 95) {                                // game reads a state
            DWORD v1, v2; int st = rand() % 6; dGetRS(&g_ref, st, &v1); DEVF(58, D_u_p)(&g_impl, st, &v2);
            if (v1 != v2) { printf("get step %d: RS%d %u vs %u\n", step, st, v1, v2); ++fails; }
        } else if (r < 97) {                                // (vertex declarations: FVF 0 cannot be restored by any variant)

        } else {                                            // end of frame
            DEVF(42, D_p)(&g_impl, nullptr);
            if (!Same(&g_ref, &g_impl, "EndScene", step)) ++fails;
        }
    }
    // final
    while (!g_stack.empty()) { ActiveFx* a = g_stack.back(); g_stack.pop_back(); h_CEEnd((BYTE*)a->ce, nullptr); delete a; }
    FxFlush();
    for (int i = 1; i < 4; ++i) {
        int held = 0; for (int k = 0; k < 21; ++k) held += g_impl.tex[k] == &g_objs[i]; held += g_impl.vs == &g_objs[i]; held += g_impl.ps == &g_objs[i];
        if (g_objs[i].refs != 1000 + held) { printf("REF LEAK obj %d: refs %d expected %d\n", i, g_objs[i].refs, 1000 + held); fails++; }
    }
    printf("seed %d defer=%d: fails=%d draws=%d | begins=%u fwd=%u skip=%u restored=%u deferred=%u taken=%u flushed=%u dropped=%u\n",
           seed, g_fxDeferCfg, fails, g_draws, g_fxBegins, g_fxForwarded, g_fxSkipped, g_fxRestored, g_fxDeferred, g_fxTaken, g_fxFlushed, g_fxDropped);
    return fails ? 1 : 0;
}
