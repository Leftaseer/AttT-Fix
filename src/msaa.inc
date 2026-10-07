// ---------------------------------------------------------------- MSAA (1.0.5)
// Included into attfix.cpp in the D3D9 section (after D3DPP / PatchVtbl / anisotropic filtering).
//
// The game creates a LOCKABLE back buffer without multisampling. With [Video] MSAA=2/4/8 the back buffer and the
// automatic depth buffer are created multisampled (lockable is impossible with MSAA). Consequences handled here:
//  - render-to-texture (ID3DXRenderToSurface, plain SetRenderTarget) keeps the multisampled main depth buffer bound;
//    a multisampled depth buffer cannot be used with a non-multisampled target, so while such a target is bound a
//    non-multisampled depth surface of the same size/format is bound instead (and swapped back afterwards);
//  - LockRect of the back buffer (sun reference colour, a white flash, D3DX helpers) reads a resolved copy;
//  - GetRenderTargetData from a multisampled surface goes through a resolved copy.
// Ctrl+7 switches MSAA on/off at runtime through the engine's own device-restore path.
static int g_msaa = 4;                 // samples when on ([Video] MSAA, 0 = off at start -> 4x on Ctrl+7)
static int g_msaaOn = 0;               // runtime switch (Ctrl+7)
static int g_msaaActive = 0;           // samples of the current device
static volatile bool g_msaaResetPending = false;
static void* g_bb = nullptr; static void* g_autoDS = nullptr;     // no references held
static void* g_bbCopy = nullptr; static bool g_bbLocked = false;
static BYTE* g_sunLockCtx = nullptr;   // CSun being processed (0x5352E0 / 0x535850): its back buffer lock reads one pixel
static void* g_px1 = nullptr; static bool g_pxLocked = false;
static UINT g_bbW = 0, g_bbH = 0; static DWORD g_bbFmt = 0;
struct DSSub { void* orig; void* sub; };
static DSSub g_dsSub[8]; static int g_dsSubN = 0;
static void* g_appDS = nullptr; static bool g_rt0MS = false;
static DWORD g_msaaSubBinds = 0, g_msaaLocks = 0, g_msaaGRTD = 0;

typedef HRESULT (__stdcall *SetRT_t)(void*, DWORD, void*);
typedef HRESULT (__stdcall *SetDS_t)(void*, void*);
typedef HRESULT (__stdcall *GRTD_t)(void*, void*, void*);
typedef HRESULT (__stdcall *Lock_t)(void*, void*, const RECT*, DWORD);
typedef HRESULT (__stdcall *Unlock_t)(void*);
static SetRT_t o_SetRT = nullptr; static SetDS_t o_SetDS = nullptr; static GRTD_t o_GRTD = nullptr;
static Lock_t o_SurfLock = nullptr; static Unlock_t o_SurfUnlock = nullptr;

struct SDesc { DWORD Format, Type, Usage, Pool, MS, MSQ; UINT W, H; };
static bool MsSurfDesc(void* s, SDesc* d) { return s && ((HRESULT (__stdcall*)(void*, SDesc*))(*(void***)s)[12])(s, d) >= 0; }
static bool SurfMS(void* s) { if (!s) return false; if (s == g_autoDS || s == g_bb) return g_msaaActive != 0; SDesc d; return MsSurfDesc(s, &d) && d.MS != 0; }
static inline void Rel(void* p) { if (p) ((ULONG (__stdcall*)(void*))(*(void***)p)[2])(p); }

static void RTTraceInstall(void* dev); static int g_rtTraceArm = 0;
static void MsaaReleaseResources() {
    for (int i = 0; i < g_dsSubN; ++i) Rel(g_dsSub[i].sub);
    g_dsSubN = 0;
    Rel(g_bbCopy); g_bbCopy = nullptr; g_bbLocked = false;
    Rel(g_px1); g_px1 = nullptr; g_pxLocked = false;
    g_bb = g_autoDS = g_appDS = nullptr; g_rt0MS = false;
}
// choose what is really bound for the depth surface the game wants
static void* MsaaChooseDS(void* ds) {
    if (!ds || !g_msaaActive) return ds;
    bool dsMS = SurfMS(ds);
    if (dsMS == g_rt0MS || !dsMS) return ds;
    for (int i = 0; i < g_dsSubN; ++i) if (g_dsSub[i].orig == ds) return g_dsSub[i].sub;
    SDesc d; if (!MsSurfDesc(ds, &d) || g_dsSubN >= 8) return ds;
    void* dev = *(void**)0x006C8C10; void* sub = nullptr;
    // CreateDepthStencilSurface(W, H, Format, MultiSample, Quality, Discard, pp, pShared) = 29
    HRESULT hr = ((HRESULT (__stdcall*)(void*, UINT, UINT, DWORD, DWORD, DWORD, BOOL, void**, void*))(*(void***)dev)[29])(dev, d.W, d.H, d.Format, 0, 0, FALSE, &sub, nullptr);
    if (hr < 0 || !sub) { LOG("msaa: depth substitute %ux%u fmt %lu failed %08lX", d.W, d.H, d.Format, hr); return ds; }
    g_dsSub[g_dsSubN++] = { ds, sub };
    LOG("msaa: non-multisampled depth substitute %ux%u for render-to-texture", d.W, d.H);
    return sub;
}
static void* MsaaOrigDS(void* ds) { for (int i = 0; i < g_dsSubN; ++i) if (g_dsSub[i].sub == ds) return g_dsSub[i].orig; return ds; }
static void MsaaRebind(void* dev) {
    void* want = MsaaChooseDS(g_appDS);
    if (want != g_appDS) ++g_msaaSubBinds;
    o_SetDS(dev, want);
}
static HRESULT __stdcall h_SetRT(void* dev, DWORD idx, void* surf) {
    HRESULT hr = o_SetRT(dev, idx, surf);
    if (hr >= 0 && idx == 0 && g_msaaActive) {
        bool ms = SurfMS(surf);
        if (ms != g_rt0MS) { g_rt0MS = ms; MsaaRebind(dev); }
    }
    return hr;
}
static HRESULT __stdcall h_SetDS(void* dev, void* ds) {
    if (!g_msaaActive) return o_SetDS(dev, ds);
    g_appDS = MsaaOrigDS(ds);
    void* want = MsaaChooseDS(g_appDS);
    if (want != g_appDS) ++g_msaaSubBinds;
    return o_SetDS(dev, want);
}
// resolved copy of a multisampled surface (back buffer size), lockable
static void* MsaaResolve(void* src) {
    void* dev = *(void**)0x006C8C10; SDesc d;
    if (!MsSurfDesc(src, &d)) return nullptr;
    if (g_bbCopy && (g_bbW != d.W || g_bbH != d.H || g_bbFmt != d.Format)) { Rel(g_bbCopy); g_bbCopy = nullptr; }
    if (!g_bbCopy) {
        HRESULT hr = ((HRESULT (__stdcall*)(void*, UINT, UINT, DWORD, DWORD, DWORD, BOOL, void**, void*))(*(void***)dev)[28])(dev, d.W, d.H, d.Format, 0, 0, TRUE, &g_bbCopy, nullptr);
        if (hr < 0) { LOG("msaa: resolve target %ux%u failed %08lX", d.W, d.H, hr); g_bbCopy = nullptr; return nullptr; }
        g_bbW = d.W; g_bbH = d.H; g_bbFmt = d.Format;
    }
    HRESULT hr = ((HRESULT (__stdcall*)(void*, void*, const RECT*, void*, const RECT*, DWORD))(*(void***)dev)[34])(dev, src, nullptr, g_bbCopy, nullptr, 0);
    if (hr < 0) { LOG("msaa: resolve StretchRect failed %08lX", hr); return nullptr; }
    return g_bbCopy;
}
// the sun code reads exactly one pixel (y*pitch + x*4): resolve only that pixel and hand out a pointer with pitch 0
static HRESULT SunPixelLock(void* s, void* lr) {
    void* dev = *(void**)0x006C8C10; SDesc d;
    if (!MsSurfDesc(s, &d)) return -1;
    if (!g_px1 && ((HRESULT (__stdcall*)(void*, UINT, UINT, DWORD, DWORD, DWORD, BOOL, void**, void*))(*(void***)dev)[28])(dev, 1, 1, d.Format, 0, 0, TRUE, &g_px1, nullptr) < 0) { g_px1 = nullptr; return -1; }
    int x = *(int*)(g_sunLockCtx + 0x88), y = *(int*)(g_sunLockCtx + 0x8C);
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x >= (int)d.W) x = d.W - 1;
    if (y >= (int)d.H) y = d.H - 1;
    RECT rc = { x, y, x + 1, y + 1 };
    if (((HRESULT (__stdcall*)(void*, void*, const RECT*, void*, const RECT*, DWORD))(*(void***)dev)[34])(dev, s, &rc, g_px1, nullptr, 0) < 0) return -1;
    struct { INT Pitch; BYTE* pBits; } l;
    if (((Lock_t)(*(void***)g_px1)[13])(g_px1, &l, nullptr, 0x10 /*READONLY*/) < 0) return -1;
    ((INT*)lr)[0] = 0; ((BYTE**)lr)[1] = l.pBits - x * 4;
    g_pxLocked = true; g_bbLocked = true; ++g_msaaLocks;
    return 0;
}
static HRESULT __stdcall h_SurfLock(void* s, void* lr, const RECT* r, DWORD flags) {
    if (g_msaaActive && s == g_bb && !g_bbLocked && g_sunLockCtx && !r && SunPixelLock(s, lr) >= 0) return 0;
    if (g_msaaActive && s == g_bb && !g_bbLocked) {
        void* c = MsaaResolve(s);
        if (c) { HRESULT hr = ((Lock_t)(*(void***)c)[13])(c, lr, r, flags & ~0x4000u); if (hr >= 0) { g_bbLocked = true; ++g_msaaLocks; } return hr; }
    }
    return o_SurfLock(s, lr, r, flags);
}
static HRESULT __stdcall h_SurfUnlock(void* s) {
    if (s == g_bb && g_bbLocked && g_pxLocked) { g_bbLocked = g_pxLocked = false; return ((Unlock_t)(*(void***)g_px1)[14])(g_px1); }
    if (s == g_bb && g_bbLocked && g_bbCopy) { g_bbLocked = false; return ((Unlock_t)(*(void***)g_bbCopy)[14])(g_bbCopy); }
    return o_SurfUnlock(s);
}
static HRESULT __stdcall h_GRTD(void* dev, void* src, void* dst) {
    if (g_msaaActive && SurfMS(src)) { void* c = MsaaResolve(src); if (c) { ++g_msaaGRTD; return o_GRTD(dev, c, dst); } }
    return o_GRTD(dev, src, dst);
}

// before CreateDevice / Reset: multisampled back buffer if supported
static void AtocCheck(void* d3d, UINT adapter, DWORD devType, DWORD fmt); static void AtocDeviceReady(void* dev);
static void MsaaParams(void* d3d, UINT adapter, DWORD devType, D3DPP* p) {
    AtocCheck(d3d, adapter, devType, p->Fmt);
    int want = g_msaaOn ? g_msaa : 0;
    if (want < 2) { if (p->MS) LOG("msaa: off"); p->MS = 0; p->MSQ = 0; return; }
    if (want > 16) want = 16;
    typedef HRESULT (__stdcall *CDMST_t)(void*, UINT, DWORD, DWORD, BOOL, DWORD, DWORD*);
    CDMST_t chk = (CDMST_t)(*(void***)d3d)[11];
    DWORD fmt = p->Fmt ? p->Fmt : 22 /*X8R8G8B8*/;
    for (int s = want; s >= 2; --s) {
        DWORD q = 0;
        if (chk(d3d, adapter, devType, fmt, p->Windowed, s, &q) >= 0 && (!p->AutoDS || chk(d3d, adapter, devType, p->DSFmt, p->Windowed, s, nullptr) >= 0)) {
            if (p->Swap != 1 /*DISCARD*/) { LOG("msaa: swap effect %lu is not DISCARD, MSAA off", p->Swap); break; }
            p->MS = s; p->MSQ = 0; p->Flags &= ~1u /*LOCKABLE_BACKBUFFER*/;
            LOG("msaa: %dx (requested %d)", s, g_msaa);
            return;
        }
    }
    LOG("msaa: %dx not supported for fmt %lu, off", want, fmt);
    p->MS = 0; p->MSQ = 0;
}
// after a successful CreateDevice / Reset
static void MsaaDeviceReady(void* dev, D3DPP* p) {
    MsaaReleaseResources();
    g_msaaActive = p->MS;
    void** vt = *(void***)dev;
    if (!o_SetRT) {
        o_SetRT = (SetRT_t)PatchVtbl(vt, 37, (void*)h_SetRT);
        o_SetDS = (SetDS_t)PatchVtbl(vt, 39, (void*)h_SetDS);
        o_GRTD = (GRTD_t)PatchVtbl(vt, 32, (void*)h_GRTD);
    }
    void* bb = nullptr;
    if (((HRESULT (__stdcall*)(void*, UINT, UINT, DWORD, void**))vt[18])(dev, 0, 0, 0, &bb) >= 0 && bb) {
        g_bb = bb;
        if (!o_SurfLock) { void** svt = *(void***)bb; o_SurfLock = (Lock_t)PatchVtbl(svt, 13, (void*)h_SurfLock); o_SurfUnlock = (Unlock_t)PatchVtbl(svt, 14, (void*)h_SurfUnlock); }
        Rel(bb);
    }
    void* ds = nullptr;
    if (((HRESULT (__stdcall*)(void*, void**))vt[40])(dev, &ds) >= 0 && ds) { g_autoDS = ds; Rel(ds); }
    g_appDS = g_autoDS; g_rt0MS = g_msaaActive != 0;
    RTTraceInstall(dev); g_rtTraceArm = 300;
    AtocDeviceReady(dev);
}
static void MsaaStats() {
    if (g_msaaActive || g_msaaSubBinds || g_msaaLocks) PLOG("MSAA %dx: depth substitutions=%lu back buffer locks=%lu resolved GetRenderTargetData=%lu", g_msaaActive, g_msaaSubBinds, g_msaaLocks, g_msaaGRTD);
    g_msaaSubBinds = g_msaaLocks = g_msaaGRTD = 0;
}

// ---------------------------------------------------------------- diagnostics: one-frame render target trace
// 300 frames after every device (re)creation: which render targets get how many draws, depth binding, AA state.
typedef HRESULT (__stdcall *DIP_t)(void*, DWORD, INT, UINT, UINT, UINT, UINT);
typedef HRESULT (__stdcall *DP_t)(void*, DWORD, UINT, UINT);
typedef HRESULT (__stdcall *DPUP_t)(void*, DWORD, UINT, const void*, UINT);
typedef HRESULT (__stdcall *DIPUP_t)(void*, DWORD, UINT, UINT, UINT, const void*, DWORD, const void*, UINT);
static DIP_t o_DIP = nullptr; static DP_t o_DP = nullptr; static DPUP_t o_DPUP = nullptr; static DIPUP_t o_DIPUP = nullptr;
static bool g_rtTraceOn = false;
struct RTRec { void* rt; void* ds; DWORD draws; };
static RTRec g_rtRec[64]; static int g_rtRecN = 0;
static void RTCount() {
    if (!g_rtTraceOn) return;
    void* dev = *(void**)0x006C8C10; void* rt = nullptr; void* ds = nullptr;
    ((HRESULT (__stdcall*)(void*, DWORD, void**))(*(void***)dev)[38])(dev, 0, &rt);
    ((HRESULT (__stdcall*)(void*, void**))(*(void***)dev)[40])(dev, &ds);
    Rel(rt); Rel(ds);
    if (g_rtRecN && g_rtRec[g_rtRecN - 1].rt == rt && g_rtRec[g_rtRecN - 1].ds == ds) { ++g_rtRec[g_rtRecN - 1].draws; return; }
    if (g_rtRecN < 64) g_rtRec[g_rtRecN++] = { rt, ds, 1 };
}
static HRESULT __stdcall h_DIP(void* d, DWORD a, INT b, UINT c, UINT e, UINT f, UINT g) { RTCount(); return o_DIP(d, a, b, c, e, f, g); }
static HRESULT __stdcall h_DP(void* d, DWORD a, UINT b, UINT c) { RTCount(); return o_DP(d, a, b, c); }
static HRESULT __stdcall h_DPUP(void* d, DWORD a, UINT b, const void* c, UINT e) { RTCount(); return o_DPUP(d, a, b, c, e); }
static HRESULT __stdcall h_DIPUP(void* d, DWORD a, UINT b, UINT c, UINT e, const void* f, DWORD g, const void* h, UINT i) { RTCount(); return o_DIPUP(d, a, b, c, e, f, g, h, i); }
static void RTTraceInstall(void* dev) {
    if (o_DIP) return;
    void** vt = *(void***)dev;
    o_DP = (DP_t)PatchVtbl(vt, 81, (void*)h_DP); o_DIP = (DIP_t)PatchVtbl(vt, 82, (void*)h_DIP);
    o_DPUP = (DPUP_t)PatchVtbl(vt, 83, (void*)h_DPUP); o_DIPUP = (DIPUP_t)PatchVtbl(vt, 84, (void*)h_DIPUP);
}
static void RTTraceFrame(void* dev) {   // called once per frame after Present
    if (g_rtTraceOn) {
        g_rtTraceOn = false;
        DWORD aa = 0; ((HRESULT (__stdcall*)(void*, DWORD, DWORD*))(*(void***)dev)[58])(dev, 161 /*MULTISAMPLEANTIALIAS*/, &aa);
        LOG("frame trace (MSAA %dx, back buffer %p, auto depth %p, MULTISAMPLEANTIALIAS=%lu): %d render target runs", g_msaaActive, g_bb, g_autoDS, aa, g_rtRecN);
        for (int i = 0; i < g_rtRecN; ++i) {
            SDesc a = {}, b = {}; MsSurfDesc(g_rtRec[i].rt, &a); MsSurfDesc(g_rtRec[i].ds, &b);
            LOG("  rt %p %ux%u fmt %lu ms %lu usage %lx | ds %p %ux%u ms %lu | draws %lu%s", g_rtRec[i].rt, a.W, a.H, a.Format, a.MS, a.Usage,
                g_rtRec[i].ds, b.W, b.H, b.MS, g_rtRec[i].draws, g_rtRec[i].rt == g_bb ? "  <- back buffer" : "");
        }
        g_rtRecN = 0;
    }
    if (g_rtTraceArm > 0 && --g_rtTraceArm == 0) { g_rtTraceOn = true; g_rtRecN = 0; }
}

// ---------------------------------------------------------------- alpha to coverage (foliage edges with MSAA)
// MSAA only smooths polygon edges; alpha-tested foliage keeps hard pixel steps. With MSAA active, whenever alpha
// testing is enabled the driver's transparency multisampling is enabled too (NVIDIA "ATOC" render-state hack,
// also implemented by DXVK and AMD drivers): the alpha value becomes per-sample coverage.
static int g_atoc = 1;                  // [Video] AlphaToCoverage; Ctrl+8
static bool g_atocSupported = false, g_atocState = false;
typedef HRESULT (__stdcall *SetRS_t)(void*, DWORD, DWORD);
static SetRS_t o_SetRS = nullptr;
static DWORD g_alphaTest = 0, g_alphaBlend = 0;
static void AtocUpdate(void* dev) {
    // only alpha-TESTED geometry without blending (foliage cut-outs): with blending on (menus, UI, effects) the
    // alpha was applied twice - as coverage and as blend - and the options window turned pale with MSAA on
    bool on = g_atocSupported && g_atoc && g_msaaActive && g_alphaTest && !g_alphaBlend;
    if (on != g_atocState) { g_atocState = on; o_SetRS(dev, 181 /*D3DRS_ADAPTIVETESS_Y*/, on ? 0x434F5441 /*'ATOC'*/ : 0); }
}
static HRESULT __stdcall h_SetRS(void* dev, DWORD st, DWORD v) {
    HRESULT hr = o_SetRS(dev, st, v);
    if (st == 15 /*D3DRS_ALPHATESTENABLE*/) { g_alphaTest = v; AtocUpdate(dev); }
    else if (st == 27 /*D3DRS_ALPHABLENDENABLE*/) { g_alphaBlend = v; AtocUpdate(dev); }
    return hr;
}
static void AtocCheck(void* d3d, UINT adapter, DWORD devType, DWORD fmt) {
    typedef HRESULT (__stdcall *CDF_t)(void*, UINT, DWORD, DWORD, DWORD, DWORD, DWORD);
    g_atocSupported = ((CDF_t)(*(void***)d3d)[10])(d3d, adapter, devType, fmt ? fmt : 22, 0, 1 /*SURFACE*/, 0x434F5441) >= 0;
}
static void AtocDeviceReady(void* dev) {
    if (!o_SetRS) o_SetRS = (SetRS_t)PatchVtbl(*(void***)dev, 57, (void*)h_SetRS);
    g_atocState = false; g_alphaTest = 0; g_alphaBlend = 0;
    LOG("alpha to coverage: %s%s", g_atocSupported ? "supported" : "not supported by the driver", g_atocSupported && g_msaaActive && g_atoc ? ", active with MSAA" : "");
}

// CSun::UpdateScreenPos (0x5352E0) locks the back buffer once to take the sun's reference colour
typedef void (__fastcall *SunPos_t)(BYTE* sun, void* edx);
static SunPos_t o_SunPos = nullptr;
static void __fastcall h_SunPos(BYTE* sun, void* edx) { g_sunLockCtx = sun; o_SunPos(sun, edx); g_sunLockCtx = nullptr; }
static void* Detour(BYTE* target, const BYTE* expect, int len, void* hook);
static void InstallSunLockCtx() {
    static const BYTE p[6] = { 0x81, 0xEC, 0xE0, 0x01, 0x00, 0x00 };
    o_SunPos = (SunPos_t)Detour((BYTE*)0x005352E0, p, 6, (void*)h_SunPos);
}
