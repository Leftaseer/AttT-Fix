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
static bool InstCaptureDIP(void* dev, DWORD type, DWORD base, DWORD minIdx, DWORD numV, DWORD start, DWORD prim);   // instance.inc
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
    // with the system Direct3D 9 the deferred restore broke the 2D menu (cause not found yet): DXVK only.
    // Without these hooks the effect optimization restores at End and tree instancing is off.
    if (!g_dxvkActive) { g_fxDeferCfg = 0; LOG("effect states: deferred restore and tree instancing off with the system d3d9 (DXVK only)"); return; }
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
    FxCountCaller((DWORD)__builtin_return_address(0));
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
    if (memcmp((void*)0x004480C0, pb, 7) || memcmp((void*)0x004480F0, pe, 5)) { g_optFx = 0; LOG("effect states: unexpected code, not installed"); return; }
    o_CEBegin = (CEBegin_t)Detour((BYTE*)0x004480C0, pb, 7, (void*)h_CEBegin);
    o_CEEnd = (CEEnd_t)Detour((BYTE*)0x004480F0, pe, 5, (void*)h_CEEnd);
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
