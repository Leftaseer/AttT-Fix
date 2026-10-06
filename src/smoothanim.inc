// ---------------------------------------------------------------- object animation smoothing (1.0.4)
// Included into attfix.cpp after renderopt.inc.
//
// Vertex-animated meshes (forest foliage, trees, water, flags, butterflies ...) are drawn by 0x4773F0 (mesh part,
// args frame, lod). Their sub-object (+0x2C) is ST_VIDEO_TWEEN_ANIM / ST_VIDEO_SHAD_ANIM / ST_SOFT_ANIM: a table
// [sub+0x3C] of {int key; float tween} per animation frame, drawn as a hardware tween of key and key+1.
// The frame index advances by n (usually 1) on each 30 Hz tick (0x4306D0 for +0x1D8, CWater tick for +0x220).
// At render time the table entry of the current frame is replaced by the position "frame + alpha*n"
// (alpha = updater accumulator / step), then restored.
static int g_meshSmooth = 1;                        // [Smooth] Objects; Ctrl+3
static BYTE* g_tickUpd = nullptr;                   // updater whose Tick (vf5) is running (set by h_UpdaterUpdate)
static DWORD g_msDraws = 0, g_msBlended = 0, g_msSkipJump = 0, g_msAnyTween = 0, g_msCtx = 0;

struct FrameReg { DWORD addr; BYTE* upd; int n; double tTick, interval; };
enum { FREG_N = 8192 };
static FrameReg g_freg[FREG_N];
static FrameReg* FregFind(DWORD addr, bool create) {
    DWORD h = (addr >> 3) * 2654435761u;
    for (int i = 0; i < 32; ++i) {
        FrameReg& r = g_freg[(h + i) & (FREG_N - 1)];
        if (r.addr == addr) return &r;
        if (!r.addr) { if (!create) return nullptr; r.addr = addr; r.upd = nullptr; r.tTick = 0; r.interval = 33.33; return &r; }
    }
    if (!create) return nullptr;
    FrameReg& r = g_freg[h & (FREG_N - 1)]; r.addr = addr; r.upd = nullptr; r.tTick = 0; r.interval = 33.33; return &r;   // evict
}
static inline double NowMs() { return Now() * g_tickMs; }

// 0x4306D0: thiscall AdvanceFrame(int n) on a mesh object (+0x1C8 count, +0x1D8 frame)
typedef void (__fastcall *FrameAdv_t)(BYTE* obj, void* edx, int n);
static FrameAdv_t o_FrameAdv = nullptr;
static void __fastcall h_FrameAdv(BYTE* obj, void* edx, int n) {
    o_FrameAdv(obj, edx, n);
    if (!n || !g_tickUpd) return;                                       // only ticks from the fixed-step updater
    FrameReg* r = FregFind((DWORD)(obj + 0x1D8), true);
    double now = NowMs();
    if (r->tTick > 0) { double d = now - r->tTick; if (d > 5 && d < 200) r->interval = d; }
    r->upd = g_tickUpd; r->n = n; r->tTick = now;
}

// current object being drawn
struct AnimCtx { int* frameVar; BYTE* upd; int n; float alpha; };
static AnimCtx g_actx = { nullptr, nullptr, 0, 0 };
static float UpdAlpha(BYTE* upd, double tTick, double interval) {
    if (!upd || !Writable(upd + 0x24)) return 0;
    float step = *(float*)(upd + 0x24), acc = *(float*)(upd + 0x28);
    if (!(step > 1.0f && step < 1000.0f)) return 0;
    if (tTick > 0 && NowMs() - tTick > 2.5 * (interval > step ? interval : step)) return 0;   // animation stopped
    float a = acc / step;
    return a < 0 ? 0 : a > 1 ? 1 : a;
}
static bool CtxFromReg(int* frameVar) {
    FrameReg* r = FregFind((DWORD)frameVar, false);
    if (!r || !r->upd) return false;
    float a = UpdAlpha(r->upd, r->tTick, r->interval);
    if (a <= 0.001f) return false;
    g_actx.frameVar = frameVar; g_actx.upd = r->upd; g_actx.n = r->n; g_actx.alpha = a;
    return true;
}
struct CtxGuard {   // nested draws restore the outer context
    AnimCtx saved; bool on;
    CtxGuard(int* frameVar) : saved(g_actx) { on = g_meshSmooth && CtxFromReg(frameVar); if (!on) g_actx.frameVar = nullptr; }
    CtxGuard(int* frameVar, BYTE* upd) : saved(g_actx) {
        on = false;
        if (g_meshSmooth) { float a = UpdAlpha(upd, 0, 0); if (a > 0.001f) { g_actx = { frameVar, upd, 1, a }; on = true; } }
        if (!on) g_actx.frameVar = nullptr;
    }
    ~CtxGuard() { g_actx = saved; }
};

// 0x4773F0: thiscall DrawPart(frame, lod)
typedef void (__fastcall *DrawPart_t)(BYTE* part, void* edx, DWORD frame, DWORD lod);
static DrawPart_t o_DrawPart = nullptr;
struct TweenKey { int key; float t; };
static void __fastcall h_DrawPart(BYTE* part, void* edx, DWORD frame, DWORD lod) {
    BYTE* sub = *(BYTE**)(part + 0x2C);
    void* vt = sub ? *(void**)sub : nullptr;
    if (vt == (void*)0x0060EAA4 || vt == (void*)0x0060EACC || vt == (void*)0x0060EAF4) ++g_msAnyTween;
    if (g_actx.frameVar) ++g_msCtx;
    if (!g_actx.frameVar || (int)frame != *g_actx.frameVar) { o_DrawPart(part, edx, frame, lod); return; }
    UINT cnt = *(UINT*)(part + 0x28);
    if ((vt != (void*)0x0060EAA4 && vt != (void*)0x0060EACC && vt != (void*)0x0060EAF4) || cnt < 2 || frame >= cnt) { o_DrawPart(part, edx, frame, lod); return; }
    TweenKey* tab = *(TweenKey**)(sub + 0x3C);
    int f1 = (int)frame + g_actx.n;
    if (f1 >= (int)cnt) f1 -= cnt; else if (f1 < 0) f1 += cnt;
    if (!tab || f1 < 0 || f1 >= (int)cnt) { o_DrawPart(part, edx, frame, lod); return; }
    ++g_msDraws;
    float g0 = tab[frame].key + tab[frame].t, g1 = tab[f1].key + tab[f1].t;
    if (fabsf(g1 - g0) > 2.5f || tab[frame].key < 0 || tab[f1].key < 0) { ++g_msSkipJump; o_DrawPart(part, edx, frame, lod); return; }   // loop restart
    float g = g0 + (g1 - g0) * g_actx.alpha;
    int k = (int)floorf(g); float t = g - k;
    if (t < 1e-4f) t = 0;
    if (t > 0.9999f) { ++k; t = 0; }
    TweenKey save = tab[frame];
    tab[frame].key = k; tab[frame].t = t;
    ++g_msBlended;
    o_DrawPart(part, edx, frame, lod);
    tab[frame] = save;
}

// object-level draws that pass obj+0x1D8 as the frame
typedef void (__fastcall *ObjDraw1_t)(BYTE* obj, void* edx, DWORD a);
static ObjDraw1_t o_MeshRender48 = nullptr, o_MeshRender51 = nullptr, o_CTreeFoliage = nullptr;
static void __fastcall h_MeshRender48(BYTE* obj, void* edx, DWORD a) { CtxGuard g((int*)(obj + 0x1D8)); o_MeshRender48(obj, edx, a); }
static void __fastcall h_MeshRender51(BYTE* obj, void* edx, DWORD a) { CtxGuard g((int*)(obj + 0x1D8)); o_MeshRender51(obj, edx, a); }
static void __fastcall h_CTreeFoliage(BYTE* obj, void* edx, DWORD a) { CtxGuard g((int*)(obj + 0x1D8)); o_CTreeFoliage(obj, edx, a); }
typedef void (__fastcall *MeshDraw_t)(void* mesh, void* edx, DWORD frame, DWORD lod);
static void __fastcall h_MeshRender50(BYTE* obj, void*) {               // 0x4305F0, rewritten (short jump in the prologue)
    if (!obj[0x49]) return;
    CtxGuard g((int*)(obj + 0x1D8));
    ((MeshDraw_t)0x00477610)(*(void**)(obj + 0x1C4), nullptr, *(DWORD*)(obj + 0x1D8), *(DWORD*)(obj + 0x1D0));
}
static void __fastcall h_MeshRender49(BYTE* obj, void*, DWORD lod) {    // 0x430610, rewritten
    if (!obj[0x49]) return;
    CtxGuard g((int*)(obj + 0x1D8));
    ((MeshDraw_t)0x00477610)(*(void**)(obj + 0x1C4), nullptr, *(DWORD*)(obj + 0x1D8), lod);
}
typedef void (__fastcall *ObjDraw0_t)(BYTE* obj, void* edx);
static ObjDraw0_t o_WaterRender = nullptr;
static void __fastcall h_WaterRender(BYTE* obj, void* edx) { CtxGuard g((int*)(obj + 0x220), obj); o_WaterRender(obj, edx); }

static void InstallMeshSmooth() {
    static const BYTE pAdv[6] = { 0x8B, 0x91, 0xC8, 0x01, 0x00, 0x00 };
    static const BYTE pPart[5] = { 0x51, 0x55, 0x57, 0x8B, 0xF9 };
    static const BYTE pR48[8] = { 0x51, 0x56, 0x8B, 0xF1, 0x80, 0x7E, 0x49, 0x00 };
    static const BYTE pTree[10] = { 0x51, 0x56, 0x8B, 0xF1, 0x8B, 0x0D, 0xC4, 0xA2, 0x6C, 0x00 };
    static const BYTE pWater[7] = { 0x51, 0x66, 0xA1, 0xA8, 0xA8, 0x6C, 0x00 };
    static const BYTE p50[16] = { 0x80, 0x79, 0x49, 0x00, 0x74, 0x19, 0x8B, 0x81, 0xD0, 0x01, 0x00, 0x00, 0x8B, 0x91, 0xD8, 0x01 };
    static const BYTE p49[16] = { 0x80, 0x79, 0x49, 0x00, 0x74, 0x17, 0x8B, 0x44, 0x24, 0x04, 0x8B, 0x91, 0xD8, 0x01, 0x00, 0x00 };
    if (memcmp((void*)0x004306D0, pAdv, 6) || memcmp((void*)0x004773F0, pPart, 5)) { LOG("object animation smoothing: unexpected code, not installed"); g_meshSmooth = 0; return; }
    o_FrameAdv = (FrameAdv_t)Detour((BYTE*)0x004306D0, pAdv, 6, (void*)h_FrameAdv);
    o_DrawPart = (DrawPart_t)Detour((BYTE*)0x004773F0, pPart, 5, (void*)h_DrawPart);
    o_MeshRender48 = (ObjDraw1_t)Detour((BYTE*)0x00430570, pR48, 8, (void*)h_MeshRender48);
    o_MeshRender51 = (ObjDraw1_t)Detour((BYTE*)0x00430650, pR48, 8, (void*)h_MeshRender51);
    o_CTreeFoliage = (ObjDraw1_t)Detour((BYTE*)0x004E9C10, pTree, 10, (void*)h_CTreeFoliage);
    o_WaterRender = (ObjDraw0_t)Detour((BYTE*)0x004F8AE0, pWater, 7, (void*)h_WaterRender);
    if (!memcmp((void*)0x004305F0, p50, 16)) { BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)(void*)h_MeshRender50 - (0x004305F0 + 5); PatchBytes((void*)0x004305F0, j, 5); }
    if (!memcmp((void*)0x00430610, p49, 16)) { BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)(void*)h_MeshRender49 - (0x00430610 + 5); PatchBytes((void*)0x00430610, j, 5); }
    LOG("object animation smoothing installed (Objects=%d)", g_meshSmooth);
}
static void MeshSmoothStats() {
    int regs = 0; for (int i = 0; i < FREG_N; ++i) if (g_freg[i].addr) ++regs;
    PLOG("OBJANIM smooth=%d tween part draws: all=%lu with-context=%lu smoothed=%lu blended=%lu loop-restarts=%lu | part draws with context=%lu | animated frame vars=%d",
         g_meshSmooth, g_msAnyTween, g_msDraws, g_msBlended, g_msBlended, g_msSkipJump, g_msCtx, regs);
    g_msDraws = g_msBlended = g_msSkipJump = g_msAnyTween = g_msCtx = 0;
}

// ---------------------------------------------------------------- particle smoothing (1.0.4)
// CParticleSystem (vt 0x61BA64) ticks at its updater rate: time [sys+0x5E4] += step, then every particle state
// is evaluated analytically from that time (CParticle::Update 0x54AF30: position, velocity, colour, size, frame).
// The quads are built at render time by 0x5520D0. Here, for the duration of that call, every live particle is
// evaluated at "time + accumulator" (the exact moment being rendered) and restored afterwards.
// Births still happen on ticks; a particle that would expire before the rendered moment keeps its tick state.
static int g_partSmooth = 1;                        // [Smooth] Particles; Ctrl+5
static DWORD g_psSystems = 0, g_psParticles = 0;
typedef void (__fastcall *PSFill_t)(BYTE* sys, void* edx);
typedef void (__fastcall *PUpd_t)(BYTE* p, void* edx, float t);
static PSFill_t o_PSFill = nullptr;
static BYTE* g_psSave = nullptr; static size_t g_psSaveCap = 0;
enum { PART_SIZE = 0xD0 };
static void __fastcall h_PSFill(BYTE* sys, void* edx) {
    float step = *(float*)(sys + 0x24), acc = *(float*)(sys + 0x28);
    BYTE* head = *(BYTE**)(sys + 0x5C8);
    if (!g_partSmooth || !head || !(step > 1.0f && step < 1000.0f) || !(acc > 0.0f && acc < step)) { o_PSFill(sys, edx); return; }
    size_t n = 0;
    for (BYTE* nd = *(BYTE**)head; nd != head && n < 100000; nd = *(BYTE**)nd) ++n;
    if (n * PART_SIZE > g_psSaveCap) {
        size_t cap = n * PART_SIZE * 2; BYTE* b = (BYTE*)realloc(g_psSave, cap);
        if (!b) { o_PSFill(sys, edx); return; }
        g_psSave = b; g_psSaveCap = cap;
    }
    float t = *(float*)(sys + 0x5E4) + acc / 1000.0f;
    size_t i = 0;
    for (BYTE* nd = *(BYTE**)head; nd != head && i < n; nd = *(BYTE**)nd, ++i) {
        BYTE* p = nd + 8; BYTE* s = g_psSave + i * PART_SIZE;
        memcpy(s, p, PART_SIZE);
        if (!p[0x38]) continue;                                         // not alive
        ((PUpd_t)0x0054AF30)(p, nullptr, t);
        if (!p[0x38]) memcpy(p, s, PART_SIZE);                          // would expire before this moment: keep tick state
    }
    ++g_psSystems; g_psParticles += (DWORD)n;
    o_PSFill(sys, edx);
    i = 0;
    for (BYTE* nd = *(BYTE**)head; nd != head && i < n; nd = *(BYTE**)nd, ++i) memcpy(nd + 8, g_psSave + i * PART_SIZE, PART_SIZE);
}
static void InstallParticleSmooth() {
    static const BYTE p[6] = { 0x81, 0xEC, 0x38, 0x01, 0x00, 0x00 };
    static const BYTE pu[6] = { 0x83, 0xEC, 0x24, 0x56, 0x8B, 0xF1 };  // CParticle::Update prologue
    if (memcmp((void*)0x0054AF30, pu, 6)) { LOG("particle smoothing: CParticle::Update differs, not installed"); g_partSmooth = 0; return; }
    o_PSFill = (PSFill_t)Detour((BYTE*)0x005520D0, p, 6, (void*)h_PSFill);
    if (!o_PSFill) g_partSmooth = 0;
    LOG("particle smoothing %s (Particles=%d)", o_PSFill ? "installed" : "unavailable", g_partSmooth);
}
static void ParticleStats() {
    PLOG("PARTICLES smooth=%d systems drawn=%lu particles=%lu", g_partSmooth, g_psSystems, g_psParticles);
    g_psSystems = g_psParticles = 0;
}
