// ---------------------------------------------------------------- 13) mip levels and trilinear filtering (1.3.1)
// Included into attfix.cpp after shadow.inc.
//
// No world texture had smaller (mip) levels: the game's own DDS loader (CTexture, below) creates textures with the
// level count of the file, the .dds files of hi-res packs hold one level, and the other path (D3DX, 0x4E06DF) asks for
// one level explicitly. Far away the ground was sampled from the full-size texture: grainy, shimmering while moving,
// worse with 2x upscaled textures and anisotropic filtering. Besides, the terrain (continent*.ef), sky, water and slope
// effects set no MipFilter at all (D3D9 default: NONE).
//  - [Video] Mipmaps=1: one-level DXT1 textures of the game's loader get the full chain, built on the CPU at load
//    time (dxt1mip.h), and effects without any MipFilter get "MipFilter[n] = Linear;" in every pass for each stage
//    they bind a texture to (stages with MinFilter = Point and alpha-tested passes are left alone; UI effects all set
//    MipFilter explicitly and are untouched).
//  - [Video] WorldLodBias=0.0: also "MipMapLodBias[n] = <bias>;" in those passes; > 0 softer, < 0 sharper.
// The effect source is changed only in memory; if it does not compile, the original text is used.
static int g_mipFix = 1; static float g_worldLodBias = 0.0f;
static DWORD g_mipFx = 0, g_mipStages = 0, g_mipFail = 0, g_mipSeen = 0;
static DWORD g_texLoad = 0, g_texMip = 0, g_texOne = 0;
static DWORD g_mipBuilt = 0, g_mipBuiltLv = 0; static double g_mipBuiltMs = 0;
typedef HRESULT (WINAPI *D3DXCE_t)(void*, const void*, UINT, const void*, void*, DWORD, void*, void**, void**);
typedef HRESULT (WINAPI *D3DXCTFM_t)(void*, const void*, UINT, UINT, UINT, UINT, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, void*, void*, void**);
static D3DXCE_t o_D3DXCE = nullptr; static D3DXCTFM_t o_D3DXCTFM = nullptr;

static inline bool MipId(char c) { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_'; }
static inline bool MipSp(char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }
// stage number after "<word>" at q (word length wl): "<word> [ n ]"; -1 if not that form
static int MipStage(const char* t, size_t n, size_t q, size_t wl, size_t* after) {
    size_t r = q + wl; while (r < n && MipSp(t[r])) ++r;
    if (r >= n || t[r] != '[') return -1;
    ++r; while (r < n && MipSp(t[r])) ++r;
    if (r >= n || t[r] < '0' || t[r] > '9') return -1;
    int st = 0; while (r < n && t[r] >= '0' && t[r] <= '9') st = st * 10 + (t[r++] - '0');
    while (r < n && MipSp(t[r])) ++r;
    if (r >= n || t[r] != ']') return -1;
    if (after) *after = r + 1;
    return st;
}
static const char* MipFind(const char* t, size_t from, size_t to, const char* w) {   // whole word, t lower-case
    size_t wl = strlen(w);
    for (size_t p = from; p + wl <= to; ++p)
        if (t[p] == w[0] && !memcmp(t + p, w, wl) && (p == 0 || !MipId(t[p - 1])) && (p + wl >= to || !MipId(t[p + wl]))) return t + p;
    return nullptr;
}
// returns a malloc'ed new source (and its length) or nullptr when nothing is to change
static char* MipInject(const char* src, UINT len, UINT* outLen, int* nStages) {
    size_t n = len;
    char* t = (char*)malloc(n + 1); if (!t) return nullptr;
    // lower-case copy with comments and strings blanked
    for (size_t i = 0; i < n;) {
        char c = src[i];
        if (c == '/' && i + 1 < n && src[i + 1] == '/') { while (i < n && src[i] != '\n') t[i++] = ' '; continue; }
        if (c == '/' && i + 1 < n && src[i + 1] == '*') { t[i++] = ' '; t[i++] = ' '; while (i < n && !(src[i] == '*' && i + 1 < n && src[i + 1] == '/')) t[i++] = ' '; if (i < n) { t[i++] = ' '; if (i < n) t[i++] = ' '; } continue; }
        if (c == '"') { t[i++] = ' '; while (i < n && src[i] != '"' && src[i] != '\n') t[i++] = ' '; if (i < n) t[i++] = ' '; continue; }
        t[i++] = (c >= 'A' && c <= 'Z') ? (char)(c + 32) : (c == 0 ? ' ' : c);
    }
    t[n] = 0;
    bool hasMip = MipFind(t, 0, n, "mipfilter") != nullptr;
    bool doMip = g_mipFix && !hasMip, doBias = g_worldLodBias != 0.0f && !hasMip;
    if (!doMip && !doBias) { free(t); return nullptr; }
    struct Ins { size_t at; char txt[400]; } ins[64]; int nIns = 0;
    for (size_t p = 0; nIns < 64;) {
        const char* f = MipFind(t, p, n, "pass"); if (!f) break;
        size_t b = (size_t)(f - t) + 4;
        while (b < n && t[b] != '{' && t[b] != ';' && t[b] != '}') ++b;
        if (b >= n || t[b] != '{') { p = (size_t)(f - t) + 4; continue; }
        int depth = 0; size_t e = b;
        for (; e < n; ++e) { if (t[e] == '{') ++depth; else if (t[e] == '}' && --depth == 0) break; }
        if (e >= n) break;
        unsigned used = 0, point = 0;
        for (size_t q = b; q < e;) {
            const char* g = MipFind(t, q, e, "texture"); if (!g) break;
            q = (size_t)(g - t);
            int st = MipStage(t, e, q, 7, nullptr); if (st >= 0 && st < 8) used |= 1u << st;
            q += 7;
        }
        for (size_t q = b; q < e;) {
            const char* g = MipFind(t, q, e, "minfilter"); if (!g) break;
            q = (size_t)(g - t); size_t a = 0;
            int st = MipStage(t, e, q, 9, &a);
            if (st >= 0 && st < 8) { while (a < e && (MipSp(t[a]) || t[a] == '=')) ++a; if (a + 5 <= e && !memcmp(t + a, "point", 5)) point |= 1u << st; }
            q += 9;
        }
        used &= ~point;
        {   // alpha-tested passes (units: AlphaRef 0xF8) keep the original filtering: averaged alpha in the smaller
            // levels would make thin parts vanish in the distance
            const char* g = MipFind(t, b, e, "alphatestenable");
            if (g) { size_t a = (size_t)(g - t) + 15; while (a < e && (MipSp(t[a]) || t[a] == '=')) ++a; if (a + 4 <= e && !memcmp(t + a, "true", 4)) used = 0; }
        }
        if (used) {
            Ins& in = ins[nIns++]; in.at = b + 1; in.txt[0] = 0; size_t L = 0;
            for (int st = 0; st < 8; ++st) if (used & (1u << st)) {
                if (doMip) L += snprintf(in.txt + L, sizeof in.txt - L, "\r\n        MipFilter[%d] = Linear;", st);
                if (doBias && L < sizeof in.txt) L += snprintf(in.txt + L, sizeof in.txt - L, "\r\n        MipMapLodBias[%d] = %.2f;", st, g_worldLodBias);
                if (L >= sizeof in.txt) { L = sizeof in.txt - 1; break; }
                ++*nStages;
            }
        }
        p = e + 1;
    }
    free(t);
    if (!nIns) return nullptr;
    size_t extra = 0; for (int i = 0; i < nIns; ++i) extra += strlen(ins[i].txt);
    char* out = (char*)malloc(n + extra + 1); if (!out) return nullptr;
    size_t o = 0, s = 0;
    for (int i = 0; i < nIns; ++i) {
        memcpy(out + o, src + s, ins[i].at - s); o += ins[i].at - s; s = ins[i].at;
        size_t l = strlen(ins[i].txt); memcpy(out + o, ins[i].txt, l); o += l;
    }
    memcpy(out + o, src + s, n - s); o += n - s; out[o] = 0;
    *outLen = (UINT)o;
    return out;
}
static HRESULT WINAPI h_D3DXCE(void* dev, const void* src, UINT len, const void* defs, void* inc, DWORD fl, void* pool, void** fx, void** err) {
    ++g_mipSeen;
    if (src && len && len < (4u << 20)) {
        UINT nl = 0; int ns = 0;
        char* m = MipInject((const char*)src, len, &nl, &ns);
        if (m) {
            HRESULT hr = o_D3DXCE(dev, m, nl, defs, inc, fl, pool, fx, err);
            free(m);
            if (hr >= 0) { ++g_mipFx; g_mipStages += ns; return hr; }
            if (++g_mipFail <= 3) {
                const char* msg = (err && *err) ? (const char*)((void* (__stdcall*)(void*))(*(void***)*err)[3])(*err) : "";
                LOG("mipmaps: changed effect did not compile (hr %08lx), original used: %.200s", (unsigned long)hr, msg ? msg : "");
            }
            if (err && *err) { ComRelease(*err); *err = nullptr; }
        }
    }
    return o_D3DXCE(dev, src, len, defs, inc, fl, pool, fx, err);
}
// The game's texture loader (0x4E06DF, power-of-two images: nearly every texture) asks D3DX for ONE level
// (MipLevels = 1, pool DEFAULT, format = the file's), so no texture has smaller levels and a mip filter has nothing to
// use. With Mipmaps=1 that call gets the full chain, built by D3DX at load time - only for formats without smooth
// alpha (DXT1, RGB): alpha-tested units and foliage with DXT3/5 or 32-bit alpha keep one level (averaged alpha would
// thin them out in the distance).
static DWORD g_mipGen = 0, g_mipGenSkip = 0; static double g_mipGenMs = 0;
static inline bool MipFmtOk(DWORD f) {
    return f == 0x31545844 /*DXT1*/ || f == 20 /*R8G8B8*/ || f == 22 /*X8R8G8B8*/ || f == 23 /*R5G6B5*/ || f == 24 /*X1R5G5B5*/ || f == 50 /*L8*/;
}
static HRESULT WINAPI h_D3DXCTFM(void* dev, const void* src, UINT len, UINT w, UINT h, UINT mips, DWORD usage, DWORD fmt, DWORD pool, DWORD filt, DWORD mipf, DWORD ck, void* info, void* pal, void** out) {
    if (g_mipFix && mips == 1 && __builtin_return_address(0) == (void*)0x4E0708 && !(usage & 0x203 /*RT|DS|DYNAMIC*/)) {
        if (MipFmtOk(fmt)) {
            LARGE_INTEGER t0, t1, fq; QueryPerformanceCounter(&t0);
            HRESULT hr = o_D3DXCTFM(dev, src, len, w, h, 0 /*full chain*/, usage, fmt, pool, filt, mipf, ck, info, pal, out);
            QueryPerformanceCounter(&t1); QueryPerformanceFrequency(&fq);
            if (hr >= 0 && out && *out) {
                ++g_texLoad; ++g_mipGen; g_mipGenMs += (t1.QuadPart - t0.QuadPart) * 1000.0 / fq.QuadPart;
                DWORD lv = ((DWORD (__stdcall*)(void*))(*(void***)*out)[13])(*out);
                if (lv > 1) ++g_texMip; else ++g_texOne;
                return hr;
            }
        } else ++g_mipGenSkip;
    }
    HRESULT hr = o_D3DXCTFM(dev, src, len, w, h, mips, usage, fmt, pool, filt, mipf, ck, info, pal, out);
    if (hr >= 0 && out && *out) {
        ++g_texLoad;
        DWORD lv = ((DWORD (__stdcall*)(void*))(*(void***)*out)[13])(*out);   // GetLevelCount
        if (lv > 1) ++g_texMip; else ++g_texOne;
    }
    return hr;
}
static void InstallMipmaps() {
    if (g_mipFix || g_worldLodBias != 0.0f) {
        o_D3DXCE = (D3DXCE_t)PatchIAT("d3dx9_29.dll", "D3DXCreateEffect", (void*)h_D3DXCE);
        if (!o_D3DXCE) LOG("mipmaps: D3DXCreateEffect not hooked, off");
    }
    o_D3DXCTFM = (D3DXCTFM_t)PatchIAT("d3dx9_29.dll", "D3DXCreateTextureFromFileInMemoryEx", (void*)h_D3DXCTFM);
    LOG("mipmaps: world effects without a mip filter -> %s, world LOD bias %.2f", g_mipFix ? "trilinear" : "original", g_worldLodBias);
}
static void MipStats() {
    static DWORD lastSeen = 0, lastTex = 0, lastBuilt = 0;
    if (g_mipSeen == lastSeen && g_texLoad == lastTex && g_mipBuilt == lastBuilt) return;
    lastSeen = g_mipSeen; lastTex = g_texLoad; lastBuilt = g_mipBuilt;
    LOG("mipmaps: effects created %lu, changed %lu (%lu texture stages), failed %lu | D3DX textures %lu (with levels %lu, single %lu; levels asked for %lu, %.0f ms; alpha formats kept %lu) | game DDS textures given levels: %lu (%lu levels built, %.0f ms)",
        g_mipSeen, g_mipFx, g_mipStages, g_mipFail, g_texLoad, g_texMip, g_texOne, g_mipGen, g_mipGenMs, g_mipGenSkip, g_mipBuilt, g_mipBuiltLv, g_mipBuiltMs);
}

// ---- diagnostics: big textures created directly by the game, and the sampler states they are drawn with (Ctrl+0)
struct MipCre { void* ret; UINT w, h, lv; DWORD usage, fmt, pool, n; };
static MipCre g_mipCre[24]; static int g_mipCreN = 0;
static void MipNoteCreate(void* ret, UINT w, UINT h, UINT lv, DWORD usage, DWORD fmt, DWORD pool) {
    if (w < 1024 && h < 1024) return;
    if ((DWORD)ret < 0x401000 || (DWORD)ret > 0x5F0000) ret = nullptr;     // created inside D3DX / a DLL
    for (int i = 0; i < g_mipCreN; ++i) { MipCre& c = g_mipCre[i]; if (c.ret == ret && c.lv == lv && c.fmt == fmt && c.pool == pool && c.usage == usage) { ++c.n; return; } }
    if (g_mipCreN < 24) { g_mipCre[g_mipCreN++] = { ret, w, h, lv, usage, fmt, pool, 1 };
        LOG("mipmaps: texture %ux%u levels %u usage %lx fmt %lx pool %lu created from %p", w, h, lv, usage, fmt, pool, ret); }
}
struct MipDraw { void* tex; DWORD st, mn, mg, mp, an, w, h, lv, fmt; float bias; DWORD n; };
static MipDraw g_mipDraw[96]; static int g_mipDrawN = 0;
static void MipTraceDraw(void* dev) {
    void** vt = *(void***)dev;
    for (DWORD st = 0; st < 8; ++st) {
        void* t = nullptr;
        if (((HRESULT (__stdcall*)(void*, DWORD, void**))vt[64])(dev, st, &t) < 0 || !t) continue;
        void** tv = *(void***)t;
        DWORD type = ((DWORD (__stdcall*)(void*))tv[10])(t);           // GetType: 3 = texture
        DWORD lv = ((DWORD (__stdcall*)(void*))tv[13])(t);
        DWORD desc[8] = {};
        if (type == 3) ((HRESULT (__stdcall*)(void*, UINT, void*))tv[17])(t, 0, desc);   // GetLevelDesc
        ComRelease(t);
        if (type != 3 || (desc[6] < 512 && desc[7] < 512) || (desc[2] & 1)) continue;   // big, not render targets
        DWORD s[11] = {};
        for (DWORD k = 5; k <= 10; ++k) ((HRESULT (__stdcall*)(void*, DWORD, DWORD, DWORD*))vt[68])(dev, st, k, &s[k]);
        bool found = false;
        for (int i = 0; i < g_mipDrawN; ++i) { MipDraw& d = g_mipDraw[i];
            if (d.tex == t && d.st == st && d.mn == s[6] && d.mp == s[7] && d.an == s[10]) { ++d.n; found = true; break; } }
        if (!found && g_mipDrawN < 96) g_mipDraw[g_mipDrawN++] = { t, st, s[6], s[5], s[7], s[10], desc[6], desc[7], lv, desc[0], 0.0f, 1 }, memcpy(&g_mipDraw[g_mipDrawN - 1].bias, &s[8], 4);
    }
}
static void MipTraceFlush() {
    if (!g_mipDrawN) return;
    LOG("mipmaps: big textures drawn this frame (filter 0 none 1 point 2 linear 3 aniso):");
    for (int i = 0; i < g_mipDrawN; ++i) { MipDraw& d = g_mipDraw[i];
        LOG("  tex %p %lux%lu fmt %lx levels %lu stage %lu: min %lu mag %lu mip %lu aniso %lu bias %.2f | draws %lu", d.tex, d.w, d.h, d.fmt, d.lv, d.st, d.mn, d.mg, d.mp, d.an, d.bias, d.n); }
    g_mipDrawN = 0;
}

// ---- mip levels for the game's own DDS loader (CTexture, 0x4E02B4): the DEFAULT texture (created at 0x4E02E6)
// and its SYSTEMMEM staging copy (0x4E0321) get the level count of the file - 1 in hi-res packs. With Mipmaps=1 a
// one-level DXT1 texture is created with the full chain instead; the game still fills only level 0 of the staging
// copy (its loop follows the file's count), and right before UpdateTexture (0x4E0416) the smaller levels are built
// on the CPU (dxt1mip.h: decode, 2x2 box filter, re-encode; 1-bit alpha by majority), so the copy carries them all.
#include "dxt1mip.h"
static void* g_mipSys[64]; static int g_mipSysN = 0; static CRITICAL_SECTION g_mipCs; static bool g_mipCsInit = false;
static UINT MipCreateLevels(void* ret, UINT w, UINT h, UINT lv, DWORD usage, DWORD fmt, DWORD pool) {
    if (!g_mipFix || lv != 1 || fmt != 0x31545844 /*DXT1*/ || usage) return lv;
    if (ret != (void*)0x4E02E6 && ret != (void*)0x4E0321) return lv;
    if (w < 8 || h < 8 || (w & (w - 1)) || (h & (h - 1))) return lv;
    return 0;   // full chain
}
static void MipTrackSys(void* tex) {
    if (!g_mipCsInit) return;
    EnterCriticalSection(&g_mipCs);
    if (g_mipSysN < 64) g_mipSys[g_mipSysN++] = tex; else g_mipSys[63] = tex;
    LeaveCriticalSection(&g_mipCs);
}
// worker threads for the chain build (parallel-for over block rows; the caller works too). One build at a time:
// if another thread is already using the pool, the build runs serially on its own thread.
static struct MipPool {
    HANDLE ev[15], done; int n; volatile LONG next, left; int count, chunk; Dxt1RangeFn fn; void* ctx;
} g_mp = {};
static CRITICAL_SECTION g_mpCs; static bool g_mpInit = false;
static void MipPoolWork() {
    for (;;) {
        LONG c = InterlockedIncrement(&g_mp.next) - 1;
        int a = (int)c * g_mp.chunk; if (a >= g_mp.count) break;
        int b = a + g_mp.chunk; if (b > g_mp.count) b = g_mp.count;
        g_mp.fn(g_mp.ctx, a, b);
    }
}
static DWORD WINAPI MipWorker(LPVOID p) {
    int i = (int)(intptr_t)p;
    for (;;) {
        WaitForSingleObject(g_mp.ev[i], INFINITE);
        MipPoolWork();
        if (InterlockedDecrement(&g_mp.left) == 0) SetEvent(g_mp.done);
    }
    return 0;
}
static void MipPFor(int count, Dxt1RangeFn fn, void* ctx) {
    g_mp.fn = fn; g_mp.ctx = ctx; g_mp.count = count;
    int ch = count / (4 * (g_mp.n + 1)); g_mp.chunk = ch < 4 ? 4 : ch;
    g_mp.next = 0; g_mp.left = g_mp.n; ResetEvent(g_mp.done);
    for (int i = 0; i < g_mp.n; ++i) SetEvent(g_mp.ev[i]);
    MipPoolWork();
    WaitForSingleObject(g_mp.done, INFINITE);
}
static void MipPoolInit() {
    if (g_mpInit) return;
    InitializeCriticalSection(&g_mpCs);
    SYSTEM_INFO si; GetSystemInfo(&si);
    int n = (int)si.dwNumberOfProcessors - 1; if (n > 15) n = 15; if (n < 0) n = 0;
    g_mp.done = CreateEventA(nullptr, TRUE, FALSE, nullptr);
    for (int i = 0; i < n; ++i) {
        g_mp.ev[i] = CreateEventA(nullptr, FALSE, FALSE, nullptr);
        HANDLE th = CreateThread(nullptr, 64 * 1024, MipWorker, (LPVOID)(intptr_t)i, 0, nullptr);
        if (!th) { CloseHandle(g_mp.ev[i]); break; }
        CloseHandle(th); g_mp.n = i + 1;
    }
    g_mpInit = true;
    LOG("mipmaps: %d worker threads for building mip levels", g_mp.n);
}
typedef HRESULT (__stdcall *UpdTex_t)(void*, void*, void*);
static UpdTex_t o_UpdTex = nullptr;
static HRESULT __stdcall h_UpdTex(void* dev, void* src, void* dst) {
    bool mine = false;
    if (src && g_mipSysN) {
        EnterCriticalSection(&g_mipCs);
        for (int i = 0; i < g_mipSysN; ++i) if (g_mipSys[i] == src) { g_mipSys[i] = g_mipSys[--g_mipSysN]; mine = true; break; }
        LeaveCriticalSection(&g_mipCs);
    }
    if (mine) {
        LARGE_INTEGER t0, t1, fq; QueryPerformanceCounter(&t0);
        void** tv = *(void***)src;
        DWORD n = ((DWORD (__stdcall*)(void*))tv[13])(src);
        DWORD desc[8] = {};
        if (n > 1 && n <= 16 && ((HRESULT (__stdcall*)(void*, UINT, void*))tv[17])(src, 0, desc) >= 0 && desc[0] == 0x31545844) {
            typedef HRESULT (__stdcall *Lock_t)(void*, UINT, void*, const RECT*, DWORD);
            typedef HRESULT (__stdcall *Unlock_t)(void*, UINT);
            uint8_t* lvp[16]; int pitch[16]; DWORD locked = 0; bool ok = true;
            for (DWORD i = 0; i < n; ++i) {
                struct { INT Pitch; void* pBits; } lr = {};
                if (((Lock_t)tv[19])(src, i, &lr, nullptr, i ? 0 : 0x10 /*READONLY*/) < 0) { ok = false; break; }
                locked |= 1u << i; lvp[i] = (uint8_t*)lr.pBits; pitch[i] = lr.Pitch;
            }
            int w = (int)desc[6], h = (int)desc[7];
            uint8_t* tmp = ok ? (uint8_t*)malloc((size_t)w * h * 2) : nullptr;   // two half-size RGBA levels
            if (tmp) {
                if (g_mp.n > 0 && TryEnterCriticalSection(&g_mpCs)) { Dxt1BuildChain(lvp, pitch, (int)n, w, h, tmp, MipPFor); LeaveCriticalSection(&g_mpCs); }
                else Dxt1BuildChain(lvp, pitch, (int)n, w, h, tmp);
                free(tmp);
            }
            for (DWORD i = 0; i < n; ++i) if (locked & (1u << i)) ((Unlock_t)tv[20])(src, i);
            if (tmp) {
                QueryPerformanceCounter(&t1); QueryPerformanceFrequency(&fq);
                ++g_mipBuilt; g_mipBuiltLv += n - 1; g_mipBuiltMs += (t1.QuadPart - t0.QuadPart) * 1000.0 / fq.QuadPart;
            }
        }
    }
    return o_UpdTex(dev, src, dst);
}
static void MipDeviceHooks(void* dev) {
    if (!g_mipCsInit) { InitializeCriticalSection(&g_mipCs); g_mipCsInit = true; }
    if (!o_UpdTex && g_mipFix) { MipPoolInit(); o_UpdTex = (UpdTex_t)PatchVtbl(*(void***)dev, 31, (void*)h_UpdTex); }
}
