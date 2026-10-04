// AttTFix — proxy dinput8.dll for Ascension to the Throne (ATThrone.exe, Steam build 2007-12-11)
// Stage 1: diagnostics (log, engine exception texts, D3D device params, device-lost, minidumps), DPI awareness.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
#include <dwmapi.h>
#include <tlhelp32.h>
#define ATTFIX_VERSION "1.0"

// ---------------------------------------------------------------- log
static FILE* g_log = nullptr;
static char g_dir[MAX_PATH];
static CRITICAL_SECTION g_logcs;
static void LOG(const char* fmt, ...) {
    if (!g_log) return;
    EnterCriticalSection(&g_logcs);
    SYSTEMTIME t; GetLocalTime(&t);
    fprintf(g_log, "[%02d:%02d:%02d.%03d] ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_list a; va_start(a, fmt); vfprintf(g_log, fmt, a); va_end(a);
    fputc('\n', g_log); fflush(g_log);
    LeaveCriticalSection(&g_logcs);
}

static UINT MaxRefresh(UINT w, UINT h);
static int g_vsync = 1;
static int g_windowed;
static int g_dwmSync = 1; static int g_dwmOk = 0; typedef HRESULT (WINAPI *DwmFlush_t)(); static DwmFlush_t g_DwmFlush = nullptr;
typedef HRESULT (WINAPI *DwmTiming_t)(HWND, DWM_TIMING_INFO*); static DwmTiming_t g_DwmTiming = nullptr;   // g_dwmSync: 1 = vblank grid, 2 = DwmFlush
static int g_animBlend = 1; static int g_interp = 1;
static int g_refreshHz;
static int L_GetInput(void* L);
static void TraceFrame(DWORD frame, double nowMs, double ft, const char* sceneCls);
static void __fastcall h_UpdaterUpdate(BYTE* self, void* edx, float dt);
static float g_lastDt = 0;
static int g_traceSec = 60;
static int g_renderer = 0;
static int g_listenerHz = 60;
static DWORD g_listenerSkipped = 0, g_listenerDone = 0;
static int L_GetVideo(void* L);
static int L_SetFps(void* L);
static int g_samplerOn = 1;
static volatile DWORD g_curFrame = 0;
static double g_frameMs = 0;
static FILE* g_atr = nullptr; static int g_atrLeft = 1200; static bool g_atrArmed = false;   // timestamp of the current frame (ms)
static int g_profileEvery = 20;
static int g_showFps = 1;
static volatile bool g_skipHitch = false;   // set on focus changes / device lost
static void InstallFrameRewrite();
static void InterpApply(); static void InterpRestore(); static void InterpStats();
static void FrameEvent(const char* fmt, ...);
static int L_SetInput(void* L);
static void SubclassWindow(HWND h);
static void* g_d3d = nullptr;

// ---------------------------------------------------------------- IAT patch
static void** FindIAT(HMODULE mod, const char* dll, const char* func) {
    BYTE* base = (BYTE*)mod;
    auto dos = (IMAGE_DOS_HEADER*)base; auto nt = (IMAGE_NT_HEADERS*)(base + dos->e_lfanew);
    auto& dir = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    if (!dir.VirtualAddress || !dir.Size) return nullptr;
    for (auto imp = (IMAGE_IMPORT_DESCRIPTOR*)(base + dir.VirtualAddress); imp->Name; ++imp) {
        if (_stricmp((char*)(base + imp->Name), dll)) continue;
        if (!imp->OriginalFirstThunk || !imp->FirstThunk) continue;
        auto oft = (IMAGE_THUNK_DATA*)(base + imp->OriginalFirstThunk);
        auto ft = (IMAGE_THUNK_DATA*)(base + imp->FirstThunk);
        for (; oft->u1.AddressOfData; ++oft, ++ft) {
            if (IMAGE_SNAP_BY_ORDINAL(oft->u1.Ordinal)) continue;
            auto ibn = (IMAGE_IMPORT_BY_NAME*)(base + oft->u1.AddressOfData);
            if (!strcmp((char*)ibn->Name, func)) return (void**)&ft->u1.Function;
        }
    }
    return nullptr;
}
static void* PatchIAT(const char* dll, const char* func, void* hook) {
    void** slot = FindIAT(GetModuleHandleA(nullptr), dll, func);
    if (!slot) { LOG("IAT: %s!%s not found", dll, func); return nullptr; }
    DWORD old; VirtualProtect(slot, 4, PAGE_READWRITE, &old);
    void* orig = *slot; *slot = hook;
    VirtualProtect(slot, 4, old, &old);
    LOG("IAT: hooked %s!%s", dll, func);
    return orig;
}
static void* PatchVtbl(void** vtbl, int idx, void* hook) {
    DWORD old; VirtualProtect(&vtbl[idx], 4, PAGE_READWRITE, &old);
    void* orig = vtbl[idx]; vtbl[idx] = hook;
    VirtualProtect(&vtbl[idx], 4, old, &old);
    return orig;
}

// ---------------------------------------------------------------- minidump
typedef BOOL (WINAPI *MiniDumpWriteDump_t)(HANDLE, DWORD, HANDLE, int, void*, void*, void*);
struct MDEI { DWORD ThreadId; EXCEPTION_POINTERS* ExceptionPointers; BOOL ClientPointers; };
static void WriteDump(EXCEPTION_POINTERS* ep, const char* tag) {
    HMODULE dbg = LoadLibraryA("dbghelp.dll");
    auto fn = dbg ? (MiniDumpWriteDump_t)GetProcAddress(dbg, "MiniDumpWriteDump") : nullptr;
    if (!fn) { LOG("dump: dbghelp unavailable"); return; }
    SYSTEMTIME t; GetLocalTime(&t);
    char path[MAX_PATH];
    snprintf(path, sizeof path, "%sAttTFix_%s_%04d%02d%02d_%02d%02d%02d.dmp", g_dir, tag, t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute, t.wSecond);
    HANDLE h = CreateFileA(path, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, 0, nullptr);
    if (h == INVALID_HANDLE_VALUE) return;
    MDEI ei = { GetCurrentThreadId(), ep, FALSE };
    // MiniDumpWithIndirectlyReferencedMemory(0x40) | MiniDumpScanMemory(0x10) | MiniDumpWithDataSegs(0x1)
    BOOL ok = fn(GetCurrentProcess(), GetCurrentProcessId(), h, 0x40 | 0x10 | 0x1, ep ? &ei : nullptr, nullptr, nullptr);
    CloseHandle(h);
    LOG("dump: %s -> %s", ok ? "written" : "FAILED", path);
}

// ---------------------------------------------------------------- engine exceptions (_CxxThrowException)
// Engine exception object = VC8 std::string (28 bytes): +4 union{char buf[16]; char* ptr}, +20 size, +24 capacity
static const DWORD ENGINE_THROWINFO = 0x0069916C;
typedef void (__stdcall *CxxThrow_t)(void*, void*);
static CxxThrow_t o_CxxThrow;
static void __stdcall h_CxxThrow(void* obj, void* ti) {
    void* ret = __builtin_return_address(0);
    char msg[1024] = "?";
    if (obj && (DWORD)ti == ENGINE_THROWINFO && !IsBadReadPtr(obj, 28)) {
        BYTE* s = (BYTE*)obj; DWORD size = *(DWORD*)(s + 20), cap = *(DWORD*)(s + 24);
        const char* p = cap >= 16 ? *(const char**)(s + 4) : (const char*)(s + 4);
        if (size < 4096 && !IsBadReadPtr(p, size)) { DWORD n = size < sizeof msg - 1 ? size : sizeof msg - 1; memcpy(msg, p, n); msg[n] = 0; }
    }
    LOG("C++ throw from %p (throwinfo %p): %s", ret, ti, msg);
    FrameEvent("C++ throw: %.80s", msg);
    o_CxxThrow(obj, ti);
}

// ---------------------------------------------------------------- crash filter
typedef LPTOP_LEVEL_EXCEPTION_FILTER (WINAPI *SUEF_t)(LPTOP_LEVEL_EXCEPTION_FILTER);
static SUEF_t o_SUEF;
static LPTOP_LEVEL_EXCEPTION_FILTER g_gameFilter;
static void FlushLuaOut();
static LONG WINAPI OurFilter(EXCEPTION_POINTERS* ep) {
    FlushLuaOut();
    auto er = ep->ExceptionRecord; auto c = ep->ContextRecord;
    LOG("CRASH code=%08lX addr=%p EAX=%08lX EBX=%08lX ECX=%08lX EDX=%08lX ESI=%08lX EDI=%08lX EBP=%08lX ESP=%08lX",
        er->ExceptionCode, er->ExceptionAddress, c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    if (er->ExceptionCode == 0xC0000005 && er->NumberParameters >= 2)
        LOG("  access violation: %s %08lX", er->ExceptionInformation[0] ? "write" : "read", (DWORD)er->ExceptionInformation[1]);
    // short stack scan: return addresses inside exe .text
    DWORD* sp = (DWORD*)c->Esp; char buf[512]; int len = 0, n = 0;
    for (int i = 0; i < 2048 && n < 24 && !IsBadReadPtr(sp + i, 4); ++i) {
        DWORD v = sp[i]; if (v >= 0x401000 && v < 0x607000) { len += snprintf(buf + len, sizeof buf - len, " %08lX", v); ++n; }
    }
    LOG("  stack:%s", n ? buf : " -");
    WriteDump(ep, "crash");
    return g_gameFilter ? g_gameFilter(ep) : EXCEPTION_CONTINUE_SEARCH;
}
static LPTOP_LEVEL_EXCEPTION_FILTER WINAPI h_SUEF(LPTOP_LEVEL_EXCEPTION_FILTER f) {
    LOG("game installs crash filter %p", f);
    g_gameFilter = f;
    return o_SUEF(OurFilter);
}

// ---------------------------------------------------------------- D3D9
struct D3DPP { UINT W, H; DWORD Fmt; UINT BBCount; DWORD MS, MSQ, Swap; HWND hwnd; BOOL Windowed, AutoDS; DWORD DSFmt, Flags; UINT Refresh, Interval; };
typedef HRESULT (__stdcall *CreateDevice_t)(void*, UINT, DWORD, HWND, DWORD, D3DPP*, void**);
typedef HRESULT (__stdcall *Reset_t)(void*, D3DPP*);
typedef HRESULT (__stdcall *TCL_t)(void*);
typedef HRESULT (__stdcall *Present_t)(void*, const void*, const void*, HWND, const void*);
typedef void* (__stdcall *D3DCreate_t)(UINT);
static CreateDevice_t o_CreateDevice; static Reset_t o_Reset; static TCL_t o_TCL; static Present_t o_Present; static D3DCreate_t o_D3DCreate;
static void LogPP(const char* tag, D3DPP* p) {
    LOG("%s: %ux%u fmt=%lu bb=%u ms=%lu swap=%lu windowed=%d autods=%d dsfmt=%lu flags=%lx refresh=%u interval=%lx hwnd=%p",
        tag, p->W, p->H, p->Fmt, p->BBCount, p->MS, p->Swap, p->Windowed, p->AutoDS, p->DSFmt, p->Flags, p->Refresh, p->Interval, p->hwnd);
}
static HRESULT __stdcall h_Reset(void* dev, D3DPP* p) {
    if (!p->Windowed && p->Refresh == 0) { UINT hz = MaxRefresh(p->W, p->H); if (hz > 60) p->Refresh = hz; }
    p->Interval = g_vsync ? 1 : 0x80000000;
    LogPP("Device::Reset", p);
    HRESULT hr = o_Reset(dev, p);
    LOG("Device::Reset -> %08lX", hr);
    return hr;
}
static LONG g_lastTCL = 0;
static HRESULT __stdcall h_TCL(void* dev) {
    HRESULT hr = o_TCL(dev);
    if (hr != g_lastTCL) { LOG("TestCooperativeLevel: %08lX -> %08lX", g_lastTCL, hr); g_lastTCL = hr; }
    return hr;
}
static LONG g_lastPresent = 0; static DWORD g_frames = 0;
static HRESULT __stdcall h_Present(void* dev, const void* a, const void* b, HWND c, const void* d) {
    HRESULT hr = o_Present(dev, a, b, c, d);
    if (hr != g_lastPresent) { LOG("Present: %08lX -> %08lX (frame %lu)", g_lastPresent, hr, g_frames); g_lastPresent = hr; }
    ++g_frames;
    return hr;
}
static HRESULT __stdcall h_CreateDevice(void* d3d, UINT ad, DWORD type, HWND wnd, DWORD flags, D3DPP* p, void** out) {
    SubclassWindow(wnd);
    RECT r; GetClientRect(wnd, &r);
    LOG("CreateDevice adapter=%u type=%lu flags=%lx window client=%ldx%ld", ad, type, flags, r.right, r.bottom);
    LogPP("  params", p);
    p->Interval = g_vsync ? 1 /*D3DPRESENT_INTERVAL_ONE*/ : 0x80000000 /*IMMEDIATE*/;
    g_windowed = p->Windowed;
    UINT hz = (!p->Windowed && p->Refresh == 0) ? MaxRefresh(p->W, p->H) : 0;
    if (hz > 60) { p->Refresh = hz; LOG("  fullscreen refresh rate -> %u Hz", hz); }
    HRESULT hr = o_CreateDevice(d3d, ad, type, wnd, flags, p, out);
    if (hr < 0 && hz > 60) { p->Refresh = 0; LOG("  failed with %u Hz (%08lX), retrying at default", hz, hr); hr = o_CreateDevice(d3d, ad, type, wnd, flags, p, out); }
    LOG("CreateDevice -> %08lX", hr);
    if (hr >= 0 && out && *out) {
        void** vt = *(void***)*out;
        if (!o_Reset) {
            o_TCL = (TCL_t)PatchVtbl(vt, 3, (void*)h_TCL);
            o_Reset = (Reset_t)PatchVtbl(vt, 16, (void*)h_Reset);
            o_Present = (Present_t)PatchVtbl(vt, 17, (void*)h_Present);
        }
    }
    return hr;
}
static void* __stdcall h_D3DCreate(UINT sdk) {
    void* d3d = nullptr;
    if (g_renderer == 1) {
        char p[MAX_PATH]; snprintf(p, sizeof p, "%sdxvk\\d3d9.dll", g_dir);
        HMODULE m = LoadLibraryA(p);
        auto f = m ? (D3DCreate_t)GetProcAddress(m, "Direct3DCreate9") : nullptr;
        if (f) { d3d = f(sdk); LOG("renderer: DXVK (%s) -> %p", p, d3d); }
        else LOG("renderer: DXVK requested but %s could not be loaded (error %lu), using system d3d9", p, GetLastError());
    }
    if (!d3d) d3d = o_D3DCreate(sdk);
    LOG("Direct3DCreate9(%u) -> %p", sdk, d3d);
    if (d3d && !g_d3d) g_d3d = d3d;
    if (d3d && !o_CreateDevice) {
        void** vt = *(void***)d3d;
        // GetAdapterDisplayMode = 8
        struct { UINT W, H, Refresh; DWORD Fmt; } mode;
        typedef HRESULT (__stdcall *GADM_t)(void*, UINT, void*);
        if (((GADM_t)vt[8])(d3d, 0, &mode) >= 0) LOG("desktop mode %ux%u @%uHz fmt=%lu", mode.W, mode.H, mode.Refresh, mode.Fmt);
        o_CreateDevice = (CreateDevice_t)PatchVtbl(vt, 16, (void*)h_CreateDevice);
    }
    return d3d;
}


// ---------------------------------------------------------------- display modes

struct Mode { UINT w, h, hz; };
static Mode g_modes[256]; static int g_nmodes = 0;
static UINT MaxRefresh(UINT w, UINT h);
static void EnumModes() {
    if (g_nmodes) return;
    // Windows display modes (available before the engine creates Direct3D)
    DEVMODEA dm; ZeroMemory(&dm, sizeof dm); dm.dmSize = sizeof dm;
    for (DWORD i = 0; EnumDisplaySettingsA(nullptr, i, &dm); ++i) {
        if (dm.dmBitsPerPel != 32 || dm.dmPelsWidth < 800 || dm.dmPelsHeight < 600) continue;
        UINT W = dm.dmPelsWidth, H = dm.dmPelsHeight, R = dm.dmDisplayFrequency;
        int j = 0; for (; j < g_nmodes; ++j) if (g_modes[j].w == W && g_modes[j].h == H) break;
        if (j < g_nmodes) { if (R > g_modes[j].hz) g_modes[j].hz = R; continue; }
        if (g_nmodes < 256) g_modes[g_nmodes++] = { W, H, R };
    }
    for (int a = 0; a < g_nmodes; ++a) for (int b = a + 1; b < g_nmodes; ++b)
        if (g_modes[b].w < g_modes[a].w || (g_modes[b].w == g_modes[a].w && g_modes[b].h < g_modes[a].h)) { Mode t = g_modes[a]; g_modes[a] = g_modes[b]; g_modes[b] = t; }
    char buf[2048]; int len = 0;
    for (int a = 0; a < g_nmodes && len < 1900; ++a) len += snprintf(buf + len, sizeof buf - len, " %ux%u@%u", g_modes[a].w, g_modes[a].h, g_modes[a].hz);
    LOG("display modes (%d):%s", g_nmodes, buf);
}
static UINT MaxRefresh(UINT w, UINT h) { EnumModes(); for (int i = 0; i < g_nmodes; ++i) if (g_modes[i].w == w && g_modes[i].h == h) return g_modes[i].hz; return 0; }


// ---------------------------------------------------------------- extended logging
// Lua output: engine routes print(), Lua PANIC messages and the debug console through a
// function pointer at 0x8D1208 (void(const char*)); by default it points to a no-op.
typedef void (*LuaOut_t)(const char*);
static LuaOut_t* const pLuaOut = (LuaOut_t*)0x008D1208;
static LuaOut_t o_LuaOut = nullptr;
static char g_outBuf[2048]; static size_t g_outLen = 0;
static void FlushLuaOut() { if (g_outLen) { g_outBuf[g_outLen] = 0; LOG("lua out: %s", g_outBuf); g_outLen = 0; } }
static void h_LuaOut(const char* s) {
    if (s) for (const char* p = s; *p; ++p) {
        if (*p == '\n' || g_outLen >= sizeof g_outBuf - 2) { FlushLuaOut(); if (*p == '\n') continue; }
        if (*p != '\r') g_outBuf[g_outLen++] = *p;
    }
    if (s && strstr(s, "PANIC")) FlushLuaOut();
    if (o_LuaOut) o_LuaOut(s);
}
static void InstallLuaOut() {
    if (*pLuaOut != h_LuaOut) { o_LuaOut = *pLuaOut; *pLuaOut = h_LuaOut; LOG("Lua output hooked (was %p)", (void*)o_LuaOut); }
}

static void LogCallerStack(const char* tag) {
    DWORD* sp; __asm__ volatile("movl %%esp, %0" : "=r"(sp));
    char buf[512]; int len = 0, n = 0;
    for (int i = 0; i < 4096 && n < 20 && !IsBadReadPtr(sp + i, 4); ++i) {
        DWORD v = sp[i]; if (v >= 0x401000 && v < 0x607000) { len += snprintf(buf + len, sizeof buf - len, " %08lX", v); ++n; }
    }
    LOG("  %s stack:%s", tag, n ? buf : " -");
}
// process exit
typedef void (__cdecl *exit_t)(int);
static exit_t o_exit;
static void LogGuardHits();
static void DumpProfile(const char*);
static void __cdecl h_exit(int code) { FlushLuaOut(); LogGuardHits(); DumpProfile("final"); LOG("sound listener: %lu updates, %lu skipped", g_listenerDone, g_listenerSkipped); LOG("exit(%d) called from %p", code, __builtin_return_address(0)); LogCallerStack("exit"); o_exit(code); }
typedef void (WINAPI *ExitProcess_t)(UINT);
static ExitProcess_t o_ExitProcess;
static void WINAPI h_ExitProcess(UINT code) { FlushLuaOut(); LOG("ExitProcess(%u) called from %p", code, __builtin_return_address(0)); LogCallerStack("ExitProcess"); o_ExitProcess(code); }
// message boxes
typedef int (WINAPI *MBA_t)(HWND, LPCSTR, LPCSTR, UINT);
typedef int (WINAPI *MBW_t)(HWND, LPCWSTR, LPCWSTR, UINT);
static MBA_t o_MBA; static MBW_t o_MBW;
static int WINAPI h_MBA(HWND h, LPCSTR t, LPCSTR c, UINT f) { LOG("MessageBoxA [%s]: %s", c ? c : "", t ? t : ""); return o_MBA(h, t, c, f); }
static int WINAPI h_MBW(HWND h, LPCWSTR t, LPCWSTR c, UINT f) {
    char a[1024] = "", b[256] = "";
    if (t) WideCharToMultiByte(1251, 0, t, -1, a, sizeof a, nullptr, nullptr);
    if (c) WideCharToMultiByte(1251, 0, c, -1, b, sizeof b, nullptr, nullptr);
    LOG("MessageBoxW [%s]: %s", b, a); return o_MBW(h, t, c, f);
}
// window messages (focus / Alt-Tab / minimize / resize)
static WNDPROC o_WndProc = nullptr; static HWND g_hwnd = nullptr;
static LRESULT CALLBACK h_WndProc(HWND h, UINT m, WPARAM w, LPARAM l) {
    switch (m) {
    case WM_ACTIVATEAPP: LOG("wnd: WM_ACTIVATEAPP %s", w ? "activated" : "deactivated"); g_skipHitch = true; break;
    case WM_ACTIVATE:    LOG("wnd: WM_ACTIVATE state=%u minimized=%u", LOWORD(w), HIWORD(w)); break;
    case WM_SIZE:        LOG("wnd: WM_SIZE type=%u %ux%u", (UINT)w, LOWORD(l), HIWORD(l)); break;
    case WM_SYSCOMMAND:  if ((w & 0xFFF0) == SC_MINIMIZE || (w & 0xFFF0) == SC_RESTORE || (w & 0xFFF0) == SC_MAXIMIZE) LOG("wnd: WM_SYSCOMMAND %04X", (UINT)(w & 0xFFF0)); break;
    case WM_DISPLAYCHANGE: LOG("wnd: WM_DISPLAYCHANGE %ux%u bpp=%u", LOWORD(l), HIWORD(l), (UINT)w); break;
    case WM_CLOSE:       LOG("wnd: WM_CLOSE"); break;
    case WM_DESTROY:     LOG("wnd: WM_DESTROY"); break;
    }
    return CallWindowProcW(o_WndProc, h, m, w, l);
}
static void SubclassWindow(HWND h) {
    if (!h || g_hwnd == h) return;
    g_hwnd = h;
    o_WndProc = (WNDPROC)SetWindowLongW(h, GWL_WNDPROC, (LONG)h_WndProc);
    LOG("window %p subclassed for logging (orig proc %p)", h, (void*)o_WndProc);
}

// ---------------------------------------------------------------- engine Lua bridge
// Lua 5.1 (float lua_Number) statically linked into ATThrone.exe
typedef int (*lua_CFunction)(void* L);
static void** const pLuaState = (void**)0x008D122C;            // lua_State* used by the engine
typedef void (*lua_pushcclosure_t)(void* L, lua_CFunction f, int n);
typedef void (*lua_setfield_t)(void* L, int idx, const char* k);
static const lua_pushcclosure_t e_pushcclosure = (lua_pushcclosure_t)0x004031F0;
static const lua_setfield_t     e_setfield     = (lua_setfield_t)0x004034F0;
#define LUA_GLOBALSINDEX (-10002)
// direct stack access: L->top at +8, L->base at +12; TValue = {value(4), tt(4)}; TString chars at +16
struct TV { union { float n; void* p; int b; } v; int tt; };
static int   LArgs(void* L) { return (int)((*(TV**)((BYTE*)L + 8)) - (*(TV**)((BYTE*)L + 12))); }
static TV*   LArg(void* L, int i) { return *(TV**)((BYTE*)L + 12) + (i - 1); }
static float LNum(void* L, int i) { if (i > LArgs(L)) return 0; TV* t = LArg(L, i); return t->tt == 3 ? t->v.n : 0; }
static const char* LStr(void* L, int i) { if (i > LArgs(L)) return ""; TV* t = LArg(L, i); return t->tt == 4 ? (const char*)t->v.p + 16 : ""; }
static void  LPushNum(void* L, float n) { TV*& top = *(TV**)((BYTE*)L + 8); top->v.n = n; top->tt = 3; ++top; }
static void Register(const char* name, lua_CFunction f) { void* L = *pLuaState; e_pushcclosure(L, f, 0); e_setfield(L, LUA_GLOBALSINDEX, name); }

static int L_Log(void* L) { const char* m = LStr(L, 1); LOG("lua: %s", m); if (!strncmp(m, "scene ", 6)) FrameEvent("%s", m); return 0; }
static int L_ModeCount(void* L) { EnumModes(); LPushNum(L, (float)g_nmodes); return 1; }
static int L_Mode(void* L) { int i = (int)LNum(L, 1); if (i < 0 || i >= g_nmodes) { LPushNum(L, 0); LPushNum(L, 0); return 2; } LPushNum(L, (float)g_modes[i].w); LPushNum(L, (float)g_modes[i].h); return 2; }
static int* const g_scrW = (int*)0x006C8964; static int* const g_scrH = (int*)0x006C8960;
static int L_Current(void* L) { LPushNum(L, (float)*g_scrW); LPushNum(L, (float)*g_scrH); return 2; }
static int L_SetResolution(void* L) {
    int wh[2] = { (int)LNum(L, 1), (int)LNum(L, 2) };
    char path[MAX_PATH]; snprintf(path, sizeof path, "%sgraphic.cfg", g_dir);
    FILE* f = fopen(path, "r+b");
    if (f && wh[0] >= 640 && wh[1] >= 480) { fwrite(wh, 4, 2, f); fclose(f); LOG("graphic.cfg: resolution set to %dx%d", wh[0], wh[1]); }
    else { if (f) fclose(f); LOG("graphic.cfg: SetResolution(%d,%d) failed", wh[0], wh[1]); }
    return 0;
}

static int g_pendW = 0, g_pendH = 0, g_pendFS = -1;
static int L_SetPending(void* L) {
    g_pendW = (int)LNum(L, 1); g_pendH = (int)LNum(L, 2);
    TV* t = LArgs(L) >= 3 ? LArg(L, 3) : nullptr;
    g_pendFS = (t && t->tt == 1) ? (t->v.b ? 1 : 0) : -1;   // LUA_TBOOLEAN = 1
    LOG("pending settings: %dx%d fullscreen=%d", g_pendW, g_pendH, g_pendFS);
    return 0;
}
static bool ReadCfg(BYTE* buf) { char p[MAX_PATH]; snprintf(p, sizeof p, "%sgraphic.cfg", g_dir); FILE* f = fopen(p, "rb"); if (!f) return false; size_t n = fread(buf, 1, 66, f); fclose(f); return n == 66; }
static bool WriteCfg(const BYTE* buf) { char p[MAX_PATH]; snprintf(p, sizeof p, "%sgraphic.cfg", g_dir); FILE* f = fopen(p, "wb"); if (!f) return false; fwrite(buf, 1, 66, f); fclose(f); return true; }
static void LogCfg(const char* tag, const BYTE* c) {
    LOG("%s: %dx%d fmt=%d tex=%d fullscreen=%d b17=%d depth=%d b22=%d b23=%d grass/shadow/refl=%d%d%d b39-41=%d%d%d gamma=%.2f",
        tag, *(int*)c, *(int*)(c + 4), *(int*)(c + 8), *(int*)(c + 12), c[16], c[17], *(int*)(c + 18), c[22], c[23], c[24], c[25], c[26], c[39], c[40], c[41], *(double*)(c + 58));
}
// Lua C function "ChangeSettings" (orig at 0x44D9D0) reimplemented: run the engine's writer, then enforce what the menu shows.
static int h_ChangeSettings(void* L) {
    BYTE before[66] = {0}, after[66] = {0};
    bool hb = ReadCfg(before);
    typedef void* (*GetEngine_t)();
    typedef void (__fastcall *Method_t)(void* self, void* edx);
    void* eng = ((GetEngine_t)0x0042F160)();
    void* lvl = *(void**)((BYTE*)eng + 0x70);
    LOG("ChangeSettings (%s)", lvl ? "in game" : "main menu");
    if (lvl) ((Method_t)0x005406F0)(lvl, nullptr); else ((Method_t)0x0044D0C0)(eng, nullptr);
    if (ReadCfg(after)) {
        if (hb) LogCfg("  cfg before", before);
        LogCfg("  cfg engine", after);
        bool ch = false;
        if (g_pendW >= 640 && g_pendH >= 480) { *(int*)after = g_pendW; *(int*)(after + 4) = g_pendH; ch = true; }
        if (g_pendFS >= 0) { after[16] = (BYTE)g_pendFS; ch = true; }
        if (ch && WriteCfg(after)) LogCfg("  cfg final ", after);
    }
    g_pendW = g_pendH = 0; g_pendFS = -1;
    return 0;
}

// ---------------------------------------------------------------- widescreen UI canvas
static int g_wsEnabled = 1;
struct Canvas { int cw, ch, ox, oy, rw, rh; };
static Canvas GetCanvas() {
    Canvas c; c.rw = *g_scrW; c.rh = *g_scrH;
    float s = (float)c.rw / 800.f; if ((float)c.rh / 600.f < s) s = (float)c.rh / 600.f;
    c.cw = (int)(800.f * s + 0.5f); c.ch = (int)(600.f * s + 0.5f);
    if (c.cw > c.rw) c.cw = c.rw;
    if (c.ch > c.rh) c.ch = c.rh;
    c.ox = (c.rw - c.cw) / 2; c.oy = (c.rh - c.ch) / 2;
    return c;
}
static char g_iniPath[MAX_PATH];
static int g_skipIntro = 0;
static int L_GetIntro(void* L) { LPushNum(L, (float)g_skipIntro); return 1; }
static int L_SetIntro(void* L) {
    g_skipIntro = LNum(L, 1) != 0;
    WritePrivateProfileStringA("Video", "SkipIntro", g_skipIntro ? "1" : "0", g_iniPath);
    LOG("options: intro videos %s (next start)", g_skipIntro ? "skipped" : "shown");
    return 0;
}
// ---- language: the Russian localization is Resource1.pak (overrides Resource0), Localization.pak is the same set
// of 53 files in English (normally swapped in by the Steam launcher). Language=en opens Localization.pak instead.
static int g_langSetting = 0, g_langActive = 0;   // 0 = ru, 1 = en
static DWORD g_langRedirects = 0;
typedef HANDLE (WINAPI *CFA_t)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static CFA_t o_CFA = nullptr;
static HANDLE WINAPI h_CFA(LPCSTR name, DWORD acc, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disp, DWORD flags, HANDLE tmpl) {
    if (g_langActive == 1 && name) {
        size_t n = strlen(name);
        if (n >= 13 && !_stricmp(name + n - 13, "Resource1.pak") && (n == 13 || name[n - 14] == '\\' || name[n - 14] == '/')) {
            char alt[MAX_PATH]; snprintf(alt, sizeof alt, "%.*sLocalization.pak", (int)(n - 13), name);
            HANDLE h = o_CFA(alt, acc, share, sa, disp, flags, tmpl);
            if (h != INVALID_HANDLE_VALUE) { if (g_langRedirects++ < 4) LOG("language en: %s -> %s", name, alt); return h; }
        }
    }
    return o_CFA(name, acc, share, sa, disp, flags, tmpl);
}
// wide path: kernelbase!CreateFileA converts and calls CreateFileW, std::ifstream may use it directly
typedef HANDLE (WINAPI *CFW_t)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static CFW_t o_CFW = nullptr;
static DWORD g_pakOpens = 0;
static HANDLE WINAPI h_CFW(LPCWSTR name, DWORD acc, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disp, DWORD flags, HANDLE tmpl) {
    if (name) {
        size_t n = wcslen(name);
        if (n >= 4 && !_wcsicmp(name + n - 4, L".pak") && g_pakOpens++ < 12) LOG("open %ls", name);
        if (g_langActive == 1 && n >= 13 && !_wcsicmp(name + n - 13, L"Resource1.pak") && (n == 13 || name[n - 14] == L'\\' || name[n - 14] == L'/')) {
            wchar_t alt[MAX_PATH]; _snwprintf(alt, MAX_PATH, L"%.*lsLocalization.pak", (int)(n - 13), name); alt[MAX_PATH - 1] = 0;
            HANDLE h = o_CFW(alt, acc, share, sa, disp, flags, tmpl);
            if (h != INVALID_HANDLE_VALUE) { if (g_langRedirects++ < 4) LOG("language en: %ls -> %ls", name, alt); return h; }
        }
    }
    return o_CFW(name, acc, share, sa, disp, flags, tmpl);
}
// hot-patch hook: "mov edi,edi" + 5 bytes of padding before the function (standard on Windows system DLLs)
static void* HotPatch(void* fn, void* hook) {
    BYTE* f = (BYTE*)fn;
    if (!f || f[0] != 0x8B || f[1] != 0xFF) return nullptr;
    for (int i = 1; i <= 5; ++i) if (f[-i] != 0xCC && f[-i] != 0x90) return nullptr;
    DWORD old; if (!VirtualProtect(f - 5, 7, PAGE_EXECUTE_READWRITE, &old)) return nullptr;
    f[-5] = 0xE9; *(DWORD*)(f - 4) = (DWORD)hook - (DWORD)f;
    *(volatile WORD*)f = 0xF9EB;   // jmp short -5
    VirtualProtect(f - 5, 7, old, &old); FlushInstructionCache(GetCurrentProcess(), f - 5, 7);
    return f + 2;
}
static void InstallLanguage() {
    if (g_langActive != 1) { LOG("language: ru (Resource1.pak)"); return; }
    char p[MAX_PATH]; snprintf(p, sizeof p, "%sLocalization.pak", g_dir);
    if (GetFileAttributesA(p) == INVALID_FILE_ATTRIBUTES) { LOG("language en requested but %s is missing -> ru", p); g_langActive = 0; return; }
    o_CFA = (CFA_t)GetProcAddress(GetModuleHandleA("kernel32.dll"), "CreateFileA");
    {   HMODULE kb = GetModuleHandleA("kernelbase.dll"); if (!kb) kb = GetModuleHandleA("kernel32.dll");
        void* w = (void*)GetProcAddress(kb, "CreateFileW");
        o_CFW = (CFW_t)HotPatch(w, (void*)h_CFW);
        LOG("language: CreateFileW %s (%p)", o_CFW ? "hot-patched" : "NOT hooked", w); }
    // the paks are opened both by the exe (CreateFileA) and through std::ifstream (MSVCR80 -> CreateFileA)
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, GetCurrentProcessId());
    MODULEENTRY32 me; me.dwSize = sizeof me; int patched = 0;
    HMODULE self = nullptr; GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)&InstallLanguage, &self);
    if (snap != INVALID_HANDLE_VALUE && Module32First(snap, &me)) do {
        if (me.hModule == self) continue;
        if (me.hModule != GetModuleHandleA(nullptr) && _stricmp(me.szModule, "msvcr80.dll") && _stricmp(me.szModule, "msvcp80.dll")) continue;
        void** slot = FindIAT(me.hModule, "KERNEL32.dll", "CreateFileA");
        if (slot && *slot != (void*)h_CFA) { DWORD old; VirtualProtect(slot, 4, PAGE_READWRITE, &old); *slot = (void*)h_CFA; VirtualProtect(slot, 4, old, &old); ++patched; LOG("language: CreateFileA hooked in %s", me.szModule); }
    } while (Module32Next(snap, &me));
    if (snap != INVALID_HANDLE_VALUE) CloseHandle(snap);
    LOG("language: en (Localization.pak instead of Resource1.pak), %d modules", patched);
}
static int L_GetLang(void* L) { LPushNum(L, (float)g_langSetting); LPushNum(L, (float)g_langActive); return 2; }
static int L_SetLang(void* L) {
    g_langSetting = LNum(L, 1) != 0 ? 1 : 0;
    WritePrivateProfileStringA("Game", "Language", g_langSetting ? "en" : "ru", g_iniPath);
    LOG("options: language -> %s (next start)", g_langSetting ? "en" : "ru");
    return 0;
}
static int L_Canvas(void* L) {
    Canvas c = GetCanvas();
    LPushNum(L, (float)c.cw); LPushNum(L, (float)c.ch); LPushNum(L, (float)c.ox); LPushNum(L, (float)c.oy);
    LPushNum(L, (float)c.rw); LPushNum(L, (float)c.rh); LPushNum(L, (float)g_wsEnabled);
    return 7;
}

static const char g_script[] =
#include "attfix_lua.h"
;

// engine DoFile(name): thiscall at 0x432620 (ret 4); RunBuffer(buf,len,name): thiscall at 0x57D220 (ret 0xC)
typedef void (__fastcall *DoFile_t)(void* vm, void* edx, const char* name);
typedef void (__fastcall *RunBuf_t)(void* vm, void* edx, const char* buf, int len, const char* name);
static DoFile_t o_DoFile;
static const RunBuf_t e_RunBuf = (RunBuf_t)0x0057D220;
static int g_modeStack[64]; static int g_modeDepth = 0;
static void SetLuaScreen(void* vm, int canvas) {
    Canvas c = GetCanvas();
    int w = canvas ? c.cw : c.rw, h = canvas ? c.ch : c.rh;
    char chunk[300];
    int n = snprintf(chunk, sizeof chunk,
        "if type(Config)=='table' then Config.ScreenWidth=%d; Config.ScreenHeight=%d; "
        "Config.RealScreenWidth=%d; Config.RealScreenHeight=%d end", w, h, c.rw, c.rh);
    e_RunBuf(vm, nullptr, chunk, n, "=AttTFixScreen");
}
static char g_seen[16384] = "|"; static size_t g_seenLen = 1;
static void __fastcall h_DoFile(void* vm, void* edx, const char* name) {
    InstallLuaOut();
    if (name) {   // log each script name the first time it is loaded
        char key[160]; snprintf(key, sizeof key, "|%s|", name);
        size_t add = strlen(key) - 1;   // "name|"
        FrameEvent("DoFile %s", name);
        if (!strstr(g_seen, key) && g_seenLen + add < sizeof g_seen) { LOG("DoFile %s", name); memcpy(g_seen + g_seenLen, key + 1, add + 1); g_seenLen += add; }
    }
    // Widescreen: per-file layout mode. Menu files are laid out on a centered 4:3 canvas, everything else
    // (in-game HUD) keeps the original stretched layout. The mode is applied to Config.ScreenWidth/Height
    // while each file loads (scripts capture it in file-level locals) and scenes get tagged with it.
    int mode = 0;   // 0 = real screen, 1 = canvas
    bool track = g_wsEnabled && name && _stricmp(name, "Config") && _stricmp(name, "LocalTexts");
    if (track) {
        static const char* canvasFiles[] = { "GUIScenes", "SceneOptions", "SceneLoad", "SceneSave", "Infobox" };
        for (const char* cf : canvasFiles) if (!_stricmp(name, cf)) mode = 1;
        if (g_modeDepth < 64) g_modeStack[g_modeDepth] = mode;
        ++g_modeDepth;
        SetLuaScreen(vm, mode);
    }
    o_DoFile(vm, edx, name);
    if (track) {
        --g_modeDepth;
        char chunk[300];
        int n = snprintf(chunk, sizeof chunk,
            "if type(GUIScene)=='table' then for k,v in pairs(GUIScene) do "
            "if type(v)=='table' and v.__attfix_mode==nil then v.__attfix_mode=%d end end end", mode);
        e_RunBuf(vm, nullptr, chunk, n, "=AttTFixTag");
        SetLuaScreen(vm, g_modeDepth > 0 && g_modeDepth <= 64 ? g_modeStack[g_modeDepth - 1] : 0);
    }
    if (name && !_stricmp(name, "camera")) {
        Canvas c = GetCanvas(); char chunk[300];
        int n = snprintf(chunk, sizeof chunk, "if type(Camera)=='table' then for _,k in ipairs({'WorldLevel','TacticLevel'}) do "
            "if type(Camera[k])=='table' then Camera[k].Aspect = %d/%d end end end", c.rw, c.rh);
        e_RunBuf(vm, nullptr, chunk, n, "=AttTFixAspect");
        LOG("camera: Aspect set to %dx%d", c.rw, c.rh);
    }
    if (name && (!_stricmp(name, "GUIScenes") || !_stricmp(name, "SceneOptions"))) {
        LOG("%s loaded; registering Lua functions and running embedded script", name);
        Register("AttTFix_Log", L_Log);
        Register("AttTFix_ModeCount", L_ModeCount);
        Register("AttTFix_Mode", L_Mode);
        Register("AttTFix_Current", L_Current);
        Register("AttTFix_SetResolution", L_SetResolution);
        Register("AttTFix_SetPending", L_SetPending);
        Register("AttTFix_Canvas", L_Canvas);
        Register("AttTFix_GetInput", L_GetInput);
        Register("AttTFix_SetInput", L_SetInput);
        Register("AttTFix_GetVideo", L_GetVideo);
        Register("AttTFix_SetFps", L_SetFps);
        Register("AttTFix_GetIntro", L_GetIntro);
        Register("AttTFix_SetIntro", L_SetIntro);
        Register("AttTFix_GetLang", L_GetLang);
        Register("AttTFix_SetLang", L_SetLang);
        { const char v[] = "AttTFix_Version = \"" ATTFIX_VERSION "\""; e_RunBuf(vm, nullptr, v, (int)sizeof(v) - 1, "=AttTFixVer"); }
        e_RunBuf(vm, nullptr, g_script, (int)sizeof(g_script) - 1, "=AttTFix");
    }
}
static void* Detour(BYTE* target, const BYTE* expect, int len, void* hook) {
    if (memcmp(target, expect, len)) { LOG("detour %p: unexpected bytes, skipped", target); return nullptr; }
    BYTE* tramp = (BYTE*)VirtualAlloc(nullptr, 32, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(tramp, target, len);
    tramp[len] = 0xE9; *(DWORD*)(tramp + len + 1) = (DWORD)(target + len) - (DWORD)(tramp + len + 5);
    DWORD old; VirtualProtect(target, len, PAGE_EXECUTE_READWRITE, &old);
    target[0] = 0xE9; *(DWORD*)(target + 1) = (DWORD)hook - (DWORD)(target + 5);
    for (int i = 5; i < len; ++i) target[i] = 0x90;
    VirtualProtect(target, len, old, &old);
    FlushInstructionCache(GetCurrentProcess(), target, len);
    LOG("detour %p installed", target);
    return tramp;
}



// ---------------------------------------------------------------- performance & input settings
static int g_fpsLimit = 0, g_allCores = 1, g_fpsTitle = 1;
static double g_cursorMul = 2.0;                 // engine constant: cursor px per mouse count (orig 2.0)
static float  g_cursorSpeed = 1.0f, g_cameraSpeed = 1.0f;
static float* const g_camRotBattle = (float*)0x006C344C;   // orig 0.5
static float* const g_camRotWorld  = (float*)0x006C3DB8;   // orig 0.5

static void ApplyInputSettings() {
    g_cursorMul = 2.0 * g_cursorSpeed;
    DWORD old;
    VirtualProtect(g_camRotBattle, 4, PAGE_READWRITE, &old); *g_camRotBattle = 0.5f * g_cameraSpeed; VirtualProtect(g_camRotBattle, 4, old, &old);
    VirtualProtect(g_camRotWorld, 4, PAGE_READWRITE, &old);  *g_camRotWorld  = 0.5f * g_cameraSpeed; VirtualProtect(g_camRotWorld, 4, old, &old);
}
static void WriteIniFloat(const char* sec, const char* key, float v) { char b[32]; snprintf(b, sizeof b, "%.2f", v); WritePrivateProfileStringA(sec, key, b, g_iniPath); }
static float ReadIniFloat(const char* sec, const char* key, float def) { char b[32]; GetPrivateProfileStringA(sec, key, "", b, sizeof b, g_iniPath); return b[0] ? (float)atof(b) : def; }

typedef BOOL (WINAPI *SPAM_t)(HANDLE, DWORD_PTR);
static SPAM_t o_SPAM;
static BOOL WINAPI h_SPAM(HANDLE h, DWORD_PTR mask) {
    if (g_allCores) { LOG("SetProcessAffinityMask(%lx) ignored: game may use all CPU cores", (DWORD)mask); return TRUE; }
    return o_SPAM(h, mask);
}

// Frame limiter: called once per frame from the main loop instead of the frame timer (0x4E4220)
static LARGE_INTEGER g_qpf, g_nextFrame; static HANDLE g_waitTimer = nullptr;
static int g_monHz = 0; static HMONITOR g_mon = nullptr; static int g_gridOk = -1;
static BOOL CALLBACK MonEnum(HMONITOR m, HDC, LPRECT, LPARAM) {
    MONITORINFOEXA mi; mi.cbSize = sizeof mi; DEVMODEA dm; ZeroMemory(&dm, sizeof dm); dm.dmSize = sizeof dm;
    if (GetMonitorInfoA(m, &mi) && EnumDisplaySettingsA(mi.szDevice, ENUM_CURRENT_SETTINGS, &dm))
        LOG("monitor %s %ldx%ld @ %lu Hz%s", mi.szDevice, mi.rcMonitor.right - mi.rcMonitor.left, mi.rcMonitor.bottom - mi.rcMonitor.top,
            dm.dmDisplayFrequency, (mi.dwFlags & MONITORINFOF_PRIMARY) ? " (primary)" : "");
    return TRUE;
}
static int WindowMonitorHz() {   // refresh rate of the monitor the game window is on (re-checked when it moves)
    if (!g_hwnd) return g_refreshHz;
    HMONITOR m = MonitorFromWindow(g_hwnd, MONITOR_DEFAULTTONEAREST);
    if (m != g_mon) {
        g_mon = m; g_gridOk = -1;
        MONITORINFOEXA mi; mi.cbSize = sizeof mi; DEVMODEA dm; ZeroMemory(&dm, sizeof dm); dm.dmSize = sizeof dm;
        g_monHz = (GetMonitorInfoA(m, &mi) && EnumDisplaySettingsA(mi.szDevice, ENUM_CURRENT_SETTINGS, &dm) && dm.dmDisplayFrequency > 1) ? (int)dm.dmDisplayFrequency : g_refreshHz;
        static bool listed = false; if (!listed) { listed = true; EnumDisplayMonitors(nullptr, nullptr, MonEnum, 0); }
        LOG("game window on %s: %d Hz", mi.szDevice, g_monHz);
    }
    return g_monHz > 0 ? g_monHz : g_refreshHz;
}
extern "C" void __cdecl FrameLimiter() {
    // windowed VSync: start each frame right after a vblank (timing from the compositor), one frame per refresh.
    // A plain timer at the refresh rate drifts in phase against the real vblank (frame shown twice / skipped).
    if (g_fpsLimit <= 0 && g_vsync && g_windowed && g_dwmOk && g_dwmSync == 1 && g_DwmTiming) {
        DWM_TIMING_INFO ti; memset(&ti, 0, sizeof ti); ti.cbSize = sizeof ti;
        int hz = WindowMonitorHz();
        bool okT = g_DwmTiming(nullptr, &ti) >= 0 && ti.qpcRefreshPeriod > 0 && ti.qpcVBlank > 0;
        if (okT && hz > 0) {   // DWM may compose at another monitor's rate (e.g. 240 Hz) -> use its phase only if the rate matches
            double dwmHz = (double)g_qpf.QuadPart / (double)ti.qpcRefreshPeriod;
            int ok = fabs(dwmHz - hz) < hz * 0.03;
            if (ok != g_gridOk) { g_gridOk = ok; LOG("vsync pacing: monitor %d Hz, compositor %.2f Hz -> %s", hz, dwmHz, ok ? "vblank grid" : "timer at monitor rate"); }
            okT = ok != 0;
        }
        if (okT) {
            LARGE_INTEGER now; QueryPerformanceCounter(&now);
            LONGLONG per = (LONGLONG)ti.qpcRefreshPeriod, t = (LONGLONG)ti.qpcVBlank + g_qpf.QuadPart / 4000;   // vblank + 0.25 ms
            if (now.QuadPart - t > per * 64) t += ((now.QuadPart - t) / per - 1) * per;                         // stale timestamp
            while (t <= now.QuadPart) t += per;
            if (g_nextFrame.QuadPart && t - g_nextFrame.QuadPart < per / 2 && t - g_nextFrame.QuadPart > -per / 2 && t <= g_nextFrame.QuadPart) t += per;
            LONGLONG remain = t - now.QuadPart, us = remain * 1000000 / g_qpf.QuadPart;
            if (us > 1500 && g_waitTimer) {
                LARGE_INTEGER due; due.QuadPart = -(LONGLONG)(us - 1000) * 10;
                if (SetWaitableTimer(g_waitTimer, &due, 0, nullptr, nullptr, FALSE)) WaitForSingleObject(g_waitTimer, INFINITE);
            } else if (us > 1500) Sleep((DWORD)((us - 1000) / 1000));
            do { QueryPerformanceCounter(&now); } while (now.QuadPart < t);
            g_nextFrame.QuadPart = t;
            return;
        }
    }
    int lim = g_fpsLimit;
    if (lim <= 0 && g_vsync && g_windowed && (!g_dwmOk || g_dwmSync == 1)) lim = WindowMonitorHz();   // windowed: Present doesn't wait for vblank
    if (lim <= 0) return;
    LARGE_INTEGER now; QueryPerformanceCounter(&now);
    LONGLONG period = g_qpf.QuadPart / lim;
    if (g_nextFrame.QuadPart == 0 || now.QuadPart >= g_nextFrame.QuadPart) {   // late or first: no catch-up burst
        g_nextFrame.QuadPart = now.QuadPart + period; return;
    }
    LONGLONG remain = g_nextFrame.QuadPart - now.QuadPart;
    if (remain > 0) {
        LONGLONG us = remain * 1000000 / g_qpf.QuadPart;
        if (us > 1500 && g_waitTimer) {   // coarse sleep, leave ~1 ms for spinning
            LARGE_INTEGER due; due.QuadPart = -(LONGLONG)(us - 1000) * 10;
            if (SetWaitableTimer(g_waitTimer, &due, 0, nullptr, nullptr, FALSE)) WaitForSingleObject(g_waitTimer, INFINITE);
        } else if (us > 1500) Sleep((DWORD)((us - 1000) / 1000));
        do { QueryPerformanceCounter(&now); } while (now.QuadPart < g_nextFrame.QuadPart);
    }
    g_nextFrame.QuadPart += period;
}
static void PatchBytes(void* at, const void* src, int n) {
    DWORD old; VirtualProtect(at, n, PAGE_EXECUTE_READWRITE, &old); memcpy(at, src, n); VirtualProtect(at, n, old, &old);
    FlushInstructionCache(GetCurrentProcess(), at, n);
}
static void InstallPerfPatches() {
    // cursor speed: operand of "fld qword ptr [0x60A308]" at 0x442AEE -> &g_cursorMul
    static const BYTE cur[6] = { 0xDD, 0x05, 0x08, 0xA3, 0x60, 0x00 };
    if (!memcmp((void*)0x00442AEE, cur, 6)) { DWORD a = (DWORD)&g_cursorMul; PatchBytes((BYTE*)0x00442AF0, &a, 4); LOG("cursor speed patch installed"); }
    else LOG("cursor speed patch: unexpected bytes");
    InstallFrameRewrite();
    ApplyInputSettings();
}

// Lua: settings get/set (cursor/camera speed) from the options menu
static int L_GetVideo(void* L) { LPushNum(L, (float)g_vsync); LPushNum(L, (float)g_fpsLimit); LPushNum(L, (float)g_refreshHz); return 3; }
static int L_SetFps(void* L) {   // (vsync 0/1, limit fps; 0 = none)
    g_vsync = LNum(L, 1) != 0; g_fpsLimit = (int)LNum(L, 2); if (g_fpsLimit < 0) g_fpsLimit = 0;
    char b[16]; snprintf(b, sizeof b, "%d", g_vsync); WritePrivateProfileStringA("Video", "VSync", b, g_iniPath);
    snprintf(b, sizeof b, "%d", g_fpsLimit); WritePrivateProfileStringA("Video", "FpsLimit", b, g_iniPath);
    LOG("fps: vsync=%d limit=%d", g_vsync, g_fpsLimit);
    return 0;
}
static int L_GetInput(void* L) { LPushNum(L, g_cursorSpeed); LPushNum(L, g_cameraSpeed); return 2; }
static int L_SetInput(void* L) {
    float c = LNum(L, 1), k = LNum(L, 2);
    if (c >= 0.1f && c <= 10.f) g_cursorSpeed = c;
    if (k >= 0.1f && k <= 10.f) g_cameraSpeed = k;
    ApplyInputSettings();
    WriteIniFloat("Mouse", "CursorSpeed", g_cursorSpeed); WriteIniFloat("Mouse", "CameraSpeed", g_cameraSpeed);
    LOG("input: cursor x%.2f camera x%.2f", g_cursorSpeed, g_cameraSpeed);
    return 0;
}


// ---------------------------------------------------------------- frame: reimplementation of CEngine frame (0x44A9C0) + profiler
// Original (MSVC, fastcall this=engine):
//   state=2; timers->Tick(); dt = timers->gameDt; ++frameNo; [0x6C8C24]->Update(dt); input->Update(dt);
//   handle PrintScreen (screenshot) / Pause keys; obj90->vf1(dt); scene->vf5(dt); obj8c->vf1(dt)
static const char* RttiName(void* obj) {
    static char buf[96];
    if (!obj || IsBadReadPtr(obj, 4)) return "null";
    void** vt = *(void***)obj; if (IsBadReadPtr(vt - 1, 4)) return "?";
    BYTE* col = (BYTE*)vt[-1]; if (IsBadReadPtr(col, 16)) return "?";
    BYTE* td = *(BYTE**)(col + 12); if (IsBadReadPtr(td, 16)) return "?";
    const char* n = (const char*)(td + 8);   // ".?AVName@NS@@"
    if (IsBadReadPtr(n, 4) || n[0] != '.') return "?";
    const char* p = n + 4; int i = 0;
    while (*p && i < 90) { if (p[0] == '@' && p[1] == '@') break; buf[i++] = (*p == '@') ? '<' : *p; ++p; }
    buf[i] = 0; return buf;
}
enum { S_TIMER, S_SYS, S_INPUT, S_OBJ90, S_SCENE, S_OBJ8C, S_CLEAR, S_RSCENE, S_RCURSOR, S_ENDSCENE, S_PRESENT, S_OUTSIDE, S_COUNT };
static const char* g_secName[S_COUNT] = { "u.timer", "u.sys", "u.input", "u.cursor", "u.scene", "u.camera",
                                          "r.clear", "r.scene", "r.cursor", "r.endscene", "r.present", "other" };

static char g_secClass[S_COUNT][64];
static double g_tickMs = 0;                       // ms per QPC tick
static LONGLONG g_lastFrameStart = 0, g_lastFrameEnd = 0;
static double g_sec[S_COUNT];                     // ms of current frame
// statistics window
static const int WIN = 4096;
static float g_ft[WIN]; static int g_nft = 0;
static double g_secSum[S_COUNT]; static double g_winStartMs = 0; static DWORD g_frameNo = 0;
static FILE* g_perf = nullptr; static int g_perfOn = 1; static float g_hitchMs = 0;
static char g_events[1024]; static size_t g_evLen = 0;   // events of the current frame (scene loads, DoFile, throws)
static void FrameEvent(const char* fmt, ...) {
    if (g_evLen > sizeof g_events - 80) return;
    va_list a; va_start(a, fmt);
    int n = vsnprintf(g_events + g_evLen, sizeof g_events - g_evLen, fmt, a); va_end(a);
    if (n > 0) { g_evLen += n; if (g_evLen < sizeof g_events - 2) { g_events[g_evLen++] = ';'; g_events[g_evLen] = 0; } }
}
static void PLOG(const char* fmt, ...) {
    if (!g_perf) return;
    SYSTEMTIME t; GetLocalTime(&t);
    fprintf(g_perf, "[%02d:%02d:%02d.%03d] ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_list a; va_start(a, fmt); vfprintf(g_perf, fmt, a); va_end(a);
    fputc('\n', g_perf); fflush(g_perf);
}
static int CmpF(const void* a, const void* b) { float x = *(const float*)a, y = *(const float*)b; return x < y ? -1 : x > y; }
static float g_median = 0; static double g_lastFt = 0;
static void FlushStats(double nowMs) {
    if (g_nft == 0) return;
    static float tmp[WIN]; memcpy(tmp, g_ft, g_nft * sizeof(float)); qsort(tmp, g_nft, sizeof(float), CmpF);
    double sum = 0; for (int i = 0; i < g_nft; ++i) sum += tmp[i];
    double avg = sum / g_nft; float p50 = tmp[g_nft / 2], p99 = tmp[(int)(g_nft * 0.99)], mx = tmp[g_nft - 1];
    // 1% low fps = average of the worst 1% frames
    int nw = g_nft / 100; if (nw < 1) nw = 1; double ws = 0; for (int i = g_nft - nw; i < g_nft; ++i) ws += tmp[i];
    g_median = p50;
    char secs[600]; int len = 0;
    for (int i = 0; i < S_COUNT; ++i) len += snprintf(secs + len, sizeof secs - len, " %s%s%s%s=%.2f", g_secName[i], g_secClass[i][0] ? "[" : "", g_secClass[i], g_secClass[i][0] ? "]" : "", g_secSum[i] / g_nft);
    MEMORYSTATUSEX mem; mem.dwLength = sizeof mem; GlobalMemoryStatusEx(&mem);
    unsigned vaMB = (unsigned)((mem.ullTotalVirtual - mem.ullAvailVirtual) >> 20), vaTotal = (unsigned)(mem.ullTotalVirtual >> 20);
    PLOG("STATS %4.1fs frames=%d fps=%.1f 1%%low=%.1f | frame ms avg=%.2f p50=%.2f p99=%.2f max=%.2f | VA %u/%u MB | avg ms:%s",
         (nowMs - g_winStartMs) / 1000.0, g_nft, g_nft * 1000.0 / (nowMs - g_winStartMs), 1000.0 * nw / ws, avg, p50, p99, mx, vaMB, vaTotal, secs);
    g_nft = 0; for (int i = 0; i < S_COUNT; ++i) g_secSum[i] = 0; g_winStartMs = nowMs;
}
static inline LONGLONG Now() { LARGE_INTEGER t; QueryPerformanceCounter(&t); return t.QuadPart; }

typedef float (__fastcall *TimerTick_t)(void* timer, void* edx);
typedef void  (__fastcall *Upd_t)(void* self, void* edx, float dt);
typedef void  (__fastcall *Method0_t)(void* self, void* edx);
static void StartSampler(); static void DumpProfile(const char*); static void HitchProfile(DWORD, char*, int);
static void __fastcall h_Frame(BYTE* e, void* /*edx*/) {
    static bool started = false; if (!started) { started = true; StartSampler(); }
    FrameLimiter();
    LONGLONG t0 = Now();
    // frame-to-frame accounting (time outside the frame function = message pump, etc.)
    if (g_lastFrameStart) {
        double ft = (t0 - g_lastFrameStart) * g_tickMs;
        double known = 0; for (int i = 0; i < S_OUTSIDE; ++i) known += g_sec[i];
        g_sec[S_OUTSIDE] = ft - known > 0 ? ft - known : 0;
        g_lastFt = ft;
        if (g_nft < WIN) g_ft[g_nft++] = (float)ft;
        for (int i = 0; i < S_COUNT; ++i) g_secSum[i] += g_sec[i];
        double thr = g_hitchMs > 0 ? g_hitchMs : (g_median > 0 ? (g_median * 2.5 > 25 ? g_median * 2.5 : 25) : 50);
        if (g_skipHitch) { g_skipHitch = false; thr = 1e9; }
        if (g_perfOn && ft > thr && g_frameNo > 30) {
            char secs[600]; int len = 0;
            for (int i = 0; i < S_COUNT; ++i) len += snprintf(secs + len, sizeof secs - len, " %s=%.2f", g_secName[i], g_sec[i]);
            char hp[700]; HitchProfile(g_frameNo, hp, sizeof hp);
            PLOG("HITCH frame %lu: %.2f ms (median %.2f) |%s | events: %s%s", g_frameNo, ft, g_median, secs, g_evLen ? g_events : "-", hp);
        }
        double nowMs = t0 * g_tickMs;
        TraceFrame(g_frameNo, nowMs, ft, g_secClass[S_SCENE]);
        if (g_winStartMs == 0) g_winStartMs = nowMs;
        if (nowMs - g_winStartMs >= 5000.0 && g_perfOn) {
            FlushStats(nowMs);
            InterpStats();
            static int windows = 0;
            if (g_profileEvery > 0 && ++windows * 5 >= g_profileEvery) { windows = 0; DumpProfile("last period"); }
        }
    }
    {   // FPS in window title
        static LONGLONG tStart = 0; static int frames = 0; static wchar_t orig[128] = L"";
        if (g_fpsTitle && g_hwnd) {
            if (!orig[0]) GetWindowTextW(g_hwnd, orig, 128);
            ++frames;
            if (!tStart) tStart = t0;
            double el = (t0 - tStart) * g_tickMs;
            if (el >= 500.0) {
                wchar_t title[200];
                swprintf(title, 200, L"%ls  |  %.0f FPS  %.2f ms", orig, frames * 1000.0 / el, el / frames);
                SetWindowTextW(g_hwnd, title);
                tStart = t0; frames = 0;
            }
        }
    }
    g_lastFrameStart = t0; { static LONGLONG base = 0; if (!base) base = t0; g_frameMs = (t0 - base) * g_tickMs; } g_evLen = 0; g_events[0] = 0; ++g_frameNo; g_curFrame = g_frameNo;
    for (int i = 0; i < S_COUNT; ++i) g_sec[i] = 0;

    LONGLONG a = t0, b;
    *(DWORD*)(e + 0xAC) = 2;
    BYTE* timers = *(BYTE**)(e + 0x7C);
    ((TimerTick_t)0x004E4220)(timers + 8, nullptr);
    float dt = *(float*)(timers + 0x1C); g_lastDt = dt;
    *(DWORD*)(e + 0xA8) += 1;
    b = Now(); g_sec[S_TIMER] = (b - a) * g_tickMs; a = b;

    void* sys = *(void**)0x006C8C24;
    ((Upd_t)0x004DEED0)(sys, nullptr, dt);
    b = Now(); g_sec[S_SYS] = (b - a) * g_tickMs; a = b;

    BYTE* input = *(BYTE**)(e + 0x80);
    { void* o = input + 4; ((Upd_t)(*(void***)o)[1])(o, nullptr, dt); }
    DWORD cnt = *(DWORD*)(input + 0x664); BYTE* keys = *(BYTE**)(input + 0x660);
    for (DWORD i = 0; i < cnt; ++i) {
        if (!keys[i * 2 + 1] || keys[i * 2] == 0x3D) continue;
        if (keys[i * 2] == 0xB7) ((Method0_t)0x00449FE0)(e, nullptr);                 // PrintScreen -> screenshot
        else if (keys[i * 2] == 0xC5) { BYTE* p = timers + 8 + 0x10; *p = (*p == 0); }  // Pause
    }
    b = Now(); g_sec[S_INPUT] = (b - a) * g_tickMs; a = b;

    void* o90 = *(void**)(e + 0x90);
    ((Upd_t)(*(void***)o90)[1])(o90, nullptr, dt);
    b = Now(); g_sec[S_OBJ90] = (b - a) * g_tickMs; a = b;

    void* scene = *(void**)(e + 0x5C);
    ((Upd_t)(*(void***)scene)[5])(scene, nullptr, dt);
    b = Now(); g_sec[S_SCENE] = (b - a) * g_tickMs; a = b;

    void* o8c = *(BYTE**)(e + 0x8C) + 4;
    ((Upd_t)(*(void***)o8c)[1])(o8c, nullptr, dt);
    b = Now(); g_sec[S_OBJ8C] = (b - a) * g_tickMs;
    g_lastFrameEnd = b; (void)g_lastFrameEnd;

    // class names of the participants (they change: menu / world / battle)
    static void* lastScene = nullptr;
    if (scene != lastScene) {
        lastScene = scene;
        snprintf(g_secClass[S_SCENE], 64, "%s", RttiName(scene));
        snprintf(g_secClass[S_RSCENE], 64, "%s", g_secClass[S_SCENE]);
        snprintf(g_secClass[S_OBJ90], 64, "%s", RttiName(o90));
        snprintf(g_secClass[S_OBJ8C], 64, "%s", RttiName(o8c));
        snprintf(g_secClass[S_SYS], 64, "%s", RttiName(sys));
        snprintf(g_secClass[S_INPUT], 64, "%s", RttiName(input + 4));
        PLOG("scene object changed: %s (obj90=%s obj8c=%s sys=%s input=%s)", g_secClass[S_SCENE], g_secClass[S_OBJ90], g_secClass[S_OBJ8C], g_secClass[S_SYS], g_secClass[S_INPUT]);
        FrameEvent("scene object -> %s", g_secClass[S_SCENE]);
    }
}

// ---------------------------------------------------------------- render: reimplementation of CEngine render (0x44E480)
// Original: state=1; camera->flag208=0; Clear(target|z, engine+0xA0, 1.0); BeginScene; scene->vf6(); cursor->vf2();
// EndScene; if (Present() < 0) { if (TestCooperativeLevel() == D3DERR_DEVICENOTRESET) Restore(); else throw "D3DERR_DEVICENOTRESET"; }
// The original throws (crash) on plain D3DERR_DEVICELOST, i.e. right after Alt-Tab in fullscreen. Fixed here.
static void** const pDevice = (void**)0x006C8C10;
typedef HRESULT (__stdcall *Clear_t)(void*, DWORD, const void*, DWORD, DWORD, float, DWORD);
typedef HRESULT (__stdcall *Dev0_t)(void*);
typedef HRESULT (__stdcall *Present_t2)(void*, const void*, const void*, HWND, const void*);
typedef void (__fastcall *VM0_t)(void* self, void* edx);
static void* g_font = nullptr;
static double g_ovFps = 0, g_ovMs = 0, g_ovUpd = 0, g_ovRen = 0, g_ovPres = 0, g_ovMax = 0;
static void FontRelease() { if (g_font) { ((ULONG (__stdcall*)(void*))(*(void***)g_font)[2])(g_font); g_font = nullptr; } }
static DWORD g_toastUntil = 0; static char g_toast[96] = "";
static void Toast(const char* t) { snprintf(g_toast, sizeof g_toast, "%s", t); g_toastUntil = GetTickCount() + 2500; LOG("toggle: %s", t); }
static bool KeyPressed(int vk, bool& down) {
    bool k = (GetAsyncKeyState(vk) & 0x8000) != 0, r = k && !down && GetForegroundWindow() == g_hwnd;
    down = k; return r;
}
static void DrawOverlay(void* dev) {
    static bool d9 = false, d10 = false, d11 = false;
    if (KeyPressed(VK_F11, d11)) g_showFps = !g_showFps;
    if (KeyPressed(VK_F9, d9)) { g_animBlend = !g_animBlend; Toast(g_animBlend ? "F9  animation blending: ON" : "F9  animation blending: OFF (original 30 fps)"); }
    static bool d8 = false;
    if (KeyPressed(VK_F8, d8)) { if (g_atr) { fclose(g_atr); g_atr = nullptr; } g_atrArmed = true; g_atrLeft = 1200; Toast("F8  animation trace: recording 1200 hero draws"); }
    if (KeyPressed(VK_F10, d10)) { g_interp = !g_interp; Toast(g_interp ? "F10 movement/camera smoothing: ON" : "F10 movement/camera smoothing: OFF (original)"); }
    bool toast = g_toastUntil && GetTickCount() < g_toastUntil;
    if (!g_showFps && !toast) return;
    if (!g_font) {
        static bool failed = false; if (failed) return;
        typedef HRESULT (WINAPI *CF_t)(void*, INT, UINT, UINT, UINT, BOOL, DWORD, DWORD, DWORD, DWORD, LPCSTR, void**);
        HMODULE x = GetModuleHandleA("d3dx9_29.dll");
        CF_t cf = x ? (CF_t)GetProcAddress(x, "D3DXCreateFontA") : nullptr;
        int h = *g_scrH / 60; if (h < 14) h = 14;
        if (!cf || cf(dev, h, 0, 700, 1, FALSE, DEFAULT_CHARSET, 0, ANTIALIASED_QUALITY, 0, "Consolas", &g_font) < 0) { failed = true; LOG("overlay: font creation failed"); return; }
    }
    char line[400]; int n = 0; line[0] = 0;
    if (g_showFps)
        n += snprintf(line + n, sizeof line - n, "%.0f FPS  %.2f ms (max %.1f)   [F11 hide]\nupdate %.2f  render %.2f  present %.2f\nsmooth: move %s  anim %s  (F10/F9)%s\n",
                      g_ovFps, g_ovMs, g_ovMax, g_ovUpd, g_ovRen, g_ovPres, g_interp ? "on" : "off", g_animBlend ? "on" : "off",
                      g_windowed && g_vsync && g_fpsLimit <= 0 ? (!g_dwmOk ? "  sync: timer" : g_dwmSync == 2 ? "  sync: flush" : g_gridOk == 1 ? "  sync: vblank" : "  sync: timer") : "");
    if (toast) snprintf(line + n, sizeof line - n, "%s", g_toast);
    typedef INT (__stdcall *DT_t)(void*, void*, LPCSTR, INT, RECT*, DWORD, DWORD);
    DT_t dt = (DT_t)(*(void***)g_font)[14];
    RECT r1 = { 12, 10, 3000, 600 }, r2 = { 10, 8, 3000, 600 };
    dt(g_font, nullptr, line, -1, &r1, DT_NOCLIP, 0xC0000000);
    dt(g_font, nullptr, line, -1, &r2, DT_NOCLIP, 0xFFFFE070);
}
static void UpdateOverlayStats() {   // every 0.5 s from the per-frame sections
    static double acc[4] = {0}; static int n = 0; static double mx = 0; static LONGLONG t0 = 0;
    LONGLONG now = Now(); if (!t0) t0 = now;
    double upd = 0; for (int i = S_TIMER; i <= S_OBJ8C; ++i) upd += g_sec[i];
    double ren = g_sec[S_CLEAR] + g_sec[S_RSCENE] + g_sec[S_RCURSOR] + g_sec[S_ENDSCENE];
    acc[0] += g_lastFt; acc[1] += upd; acc[2] += ren; acc[3] += g_sec[S_PRESENT]; if (g_lastFt > mx) mx = g_lastFt; ++n;
    double el = (now - t0) * g_tickMs;
    if (el >= 500.0 && n > 0) {
        g_ovFps = n * 1000.0 / el; g_ovMs = acc[0] / n; g_ovUpd = acc[1] / n; g_ovRen = acc[2] / n; g_ovPres = acc[3] / n; g_ovMax = mx;
        acc[0] = acc[1] = acc[2] = acc[3] = 0; n = 0; mx = 0; t0 = now;
    }
}
static void __fastcall h_Render(BYTE* e, void* /*edx*/) {
    void* dev = *pDevice; void** vt = *(void***)dev;
    LONGLONG a = Now(), b;
    *(DWORD*)(e + 0xAC) = 1;
    *(DWORD*)(*(BYTE**)(e + 0x8C) + 0x208) = 0;
    ((Clear_t)vt[43])(dev, 0, nullptr, 3, *(DWORD*)(e + 0xA0), 1.0f, 0);
    ((Dev0_t)vt[41])(dev);                                   // BeginScene
    b = Now(); g_sec[S_CLEAR] = (b - a) * g_tickMs; a = b;
    InterpApply();
    void* scene = *(void**)(e + 0x5C); ((VM0_t)(*(void***)scene)[6])(scene, nullptr);
    InterpRestore();
    b = Now(); g_sec[S_RSCENE] = (b - a) * g_tickMs; a = b;
    void* cur = *(void**)(e + 0x90); ((VM0_t)(*(void***)cur)[2])(cur, nullptr);
    UpdateOverlayStats();
    DrawOverlay(dev);
    b = Now(); g_sec[S_RCURSOR] = (b - a) * g_tickMs; a = b;
    ((Dev0_t)vt[42])(dev);                                   // EndScene
    b = Now(); g_sec[S_ENDSCENE] = (b - a) * g_tickMs; a = b;
    HRESULT hr = ((Present_t2)vt[17])(dev, nullptr, nullptr, nullptr, nullptr);
    ++g_frames;
    if (g_dwmOk && g_dwmSync == 2 && g_windowed && g_vsync && g_fpsLimit <= 0 && hr >= 0) {   // WindowedSync=flush: wait for the compositor
        if (g_DwmFlush() < 0) { g_dwmOk = 0; LOG("DwmFlush failed, falling back to timer pacing"); }
    }
    if (hr < 0) {
        HRESULT tcl = ((Dev0_t)vt[3])(dev);
        static HRESULT lastTcl = 0;
        if (tcl != lastTcl) { LOG("Present failed %08lX, TestCooperativeLevel %08lX", hr, tcl); lastTcl = tcl; }
        if (tcl == (HRESULT)0x88760869) {                    // D3DERR_DEVICENOTRESET: restore (engine code)
            FontRelease();
            LOG("device restore (engine 0x44DD20)");
            ((VM0_t)0x0044DD20)(e, nullptr);
            lastTcl = 0;
            FrameEvent("device restored");
        } else {                                             // D3DERR_DEVICELOST etc.: wait until it can be reset
            g_skipHitch = true;
            Sleep(20);
        }
    }
    b = Now(); g_sec[S_PRESENT] = (b - a) * g_tickMs;
}
static void InstallRenderRewrite() {
    static const BYTE expect[6] = { 0x64, 0xA1, 0x00, 0x00, 0x00, 0x00 };
    BYTE* t = (BYTE*)0x0044E480;
    if (memcmp(t, expect, 6)) { LOG("render rewrite: unexpected bytes"); return; }
    BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)(void*)h_Render - (DWORD)(t + 5);
    PatchBytes(t, j, 5);
    DEVMODEA dm; ZeroMemory(&dm, sizeof dm); dm.dmSize = sizeof dm;
    if (EnumDisplaySettingsA(nullptr, ENUM_CURRENT_SETTINGS, &dm)) g_refreshHz = dm.dmDisplayFrequency;
    if (g_dwmSync) {
        HMODULE dwm = LoadLibraryA("dwmapi.dll");
        g_DwmFlush = dwm ? (DwmFlush_t)GetProcAddress(dwm, "DwmFlush") : nullptr;
        g_DwmTiming = dwm ? (DwmTiming_t)GetProcAddress(dwm, "DwmGetCompositionTimingInfo") : nullptr;
        typedef HRESULT (WINAPI *DIC_t)(BOOL*); DIC_t dic = dwm ? (DIC_t)GetProcAddress(dwm, "DwmIsCompositionEnabled") : nullptr;
        BOOL on = FALSE; if (g_DwmFlush && dic && dic(&on) >= 0 && on) g_dwmOk = 1;
    }
    LOG("windowed vsync pacing: %s", !g_dwmOk ? "timer at desktop refresh" : g_dwmSync == 2 ? "DwmFlush" : "vblank grid from DWM timing");
    if (g_dwmOk && g_DwmTiming) { DWM_TIMING_INFO ti; memset(&ti, 0, sizeof ti); ti.cbSize = sizeof ti;
        if (g_DwmTiming(nullptr, &ti) >= 0) LOG("DWM timing: refresh %u/%u Hz, period %.3f ms", ti.rateRefresh.uiNumerator, ti.rateRefresh.uiDenominator,
                                                ti.qpcRefreshPeriod * 1000.0 / (double)g_qpf.QuadPart); }
    LOG("render function replaced (desktop refresh %d Hz, overlay %s, F11 toggles)", g_refreshHz, g_showFps ? "on" : "off");
}


// ---------------------------------------------------------------- optimizations
// 1) 3D sound listener (0x518D90, virtual thiscall(dt)): the original pushes position/orientation to
//    IDirectSound3DListener and calls CommitDeferredSettings EVERY frame. On modern Windows DirectSound is
//    software-emulated; the commit recalculates all 3D buffers and contends with the mixer thread's lock
//    (~0.6-1 ms per frame + spikes). Camera update stays per-frame, the listener is updated at ListenerHz.
static LONGLONG g_lastListener = 0;
static void __fastcall h_ListenerUpdate(void* self, void* edx, float dt) {
    h_UpdaterUpdate((BYTE*)self, edx, dt);
    LONGLONG now = Now();
    if (g_listenerHz > 0 && g_lastListener && (now - g_lastListener) * g_tickMs < 1000.0 / g_listenerHz) { ++g_listenerSkipped; return; }
    g_lastListener = now; ++g_listenerDone;
    BYTE* cam = ((BYTE* (*)())0x00424E70)();
    float* pos = (float*)(cam + 0x44);
    ((void (*)(float*, int))0x004C19A0)(pos, 1);                       // SetPosition (deferred)
    float dir[3] = { *(float*)(cam + 0x21C) - pos[0], *(float*)(cam + 0x220) - pos[1], *(float*)(cam + 0x224) - pos[2] };
    float up[3] = { 0.0f, *(float*)0x0068AE40, 0.0f };
    ((void (*)(float*, float*, int))0x004C1AA0)(dir, up, 1);           // SetOrientation (deferred)
    ((void (*)())0x004C18F0)();                                         // CommitDeferredSettings (+1 s housekeeping)
}
static void InstallOptimizations() {
    if (g_tickMs == 0) { LARGE_INTEGER f; QueryPerformanceFrequency(&f); g_tickMs = 1000.0 / (double)f.QuadPart; }
    static const BYTE p[8] = { 0x83, 0xEC, 0x18, 0xD9, 0x44, 0x24, 0x1C, 0x56 };
    BYTE* t = (BYTE*)0x00518D90;
    if (g_listenerHz > 0 && !memcmp(t, p, 8)) {
        BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)(void*)h_ListenerUpdate - (DWORD)(t + 5);
        PatchBytes(t, j, 5); LOG("optimization: 3D sound listener updated at %d Hz instead of every frame", g_listenerHz);
    } else LOG("optimization: sound listener patch %s", g_listenerHz > 0 ? "skipped (unexpected bytes)" : "disabled");
}


// ---------------------------------------------------------------- fixed-step updaters (0x424D90)
// Engine components derive from an "Updater": Update(dt) accumulates time (+0x28) and calls Tick() (vf5) every
// fixed step (+0x24), then vf9(ticks). Rendering is not interpolated between ticks -> motion judder at high FPS.
// Reimplemented 1:1 with per-class accounting for the trace.
struct UpdInfo { void* vt; char name[48]; float step; DWORD calls, ticks, frameTicks; int interp; DWORD iCount; };
static UpdInfo g_upd[64]; static int g_nupd = 0;
static FILE* g_trace = nullptr; static double g_traceStartMs = 0;

// ---------------------------------------------------------------- render interpolation ([Smooth])
// World objects move in 30 Hz logic ticks (position/rotation change only inside Tick), rendering is not interpolated,
// and the camera target is copied from the hero BEFORE its tick -> the hero is one step off for a frame (jitter).
// For whitelisted render objects (CRenderObject3D base, world matrix at +0x168) we remember the matrix as it was before
// the last tick; right before the scene is drawn the matrix is replaced by lerp(prev, current, acc/step) and the camera
// target is set to the hero's interpolated position; after drawing everything is restored (game logic sees nothing).
static float g_maxJump = 6.0f;
static char g_interpClasses[512] = "CHero,CNpc,SAO,CWorldUnit,CTacticCreature,CWorldHeroCreature,LuaTacticCreature,Arrow";
struct IEnt { BYTE* obj; void* vt; DWORD lastUpd; int valid; float prevM[16]; float saved[16];
               int haveLast, cvalid; double tChange, period; float lastM[16], prevC[16]; UpdInfo* u; };
static const int IMASK = 8191; static IEnt g_ient[IMASK + 1];
static IEnt* g_iApplied[4096]; static int g_nApplied = 0;
static BYTE* g_hero = nullptr; static DWORD g_heroFrame = 0;
static bool g_camSaved = false; static float g_camSave[3]; static BYTE* g_camObj = nullptr;
static DWORD g_iFrames = 0, g_iObjs = 0, g_iJumps = 0, g_iCam = 0; static float g_iHeroMax = 0, g_iHeroSum = 0; static DWORD g_iHeroN = 0;
static bool ClassListed(const char* name) {
    size_t n = strlen(name); const char* p = g_interpClasses;
    while (*p) {
        while (*p == ',' || *p == ' ') ++p;
        const char* q = p; while (*q && *q != ',' && *q != ' ') ++q;
        if ((size_t)(q - p) == n && !strncmp(p, name, n)) return true;
        p = q;
    }
    return false;
}
static inline bool MatSane(const float* m) {
    for (int i = 0; i < 16; ++i) if (!(m[i] == m[i]) || m[i] > 1e7f || m[i] < -1e7f) return false;
    return fabsf(m[3]) < 1e-3f && fabsf(m[7]) < 1e-3f && fabsf(m[11]) < 1e-3f && fabsf(m[15] - 1.0f) < 1e-3f;
}
static IEnt* IGet(BYTE* obj) {
    DWORD h = ((DWORD)obj >> 3) * 2654435761u; IEnt* reuse = nullptr;
    for (int i = 0; i < 64; ++i) {
        IEnt* e = &g_ient[(h + i) & IMASK];
        if (e->obj == obj) return e;
        if (!e->obj) { if (!reuse) reuse = e; break; }
        if (!reuse && g_curFrame - e->lastUpd > 40) reuse = e;
    }
    if (!reuse) return nullptr;
    reuse->obj = obj; reuse->vt = nullptr; reuse->lastUpd = 0; reuse->valid = 0; reuse->haveLast = 0; reuse->cvalid = 0;
    return reuse;
}
// called from the updater loop for whitelisted classes, before the ticks of this frame
static inline void InterpBeforeTicks(BYTE* self, bool willTick, UpdInfo* u) {
    IEnt* e = IGet(self); if (!e) return;
    e->u = u;
    void* vt = *(void**)self;
    if (e->vt != vt || e->lastUpd + 12 < g_curFrame) { e->valid = 0; e->haveLast = 0; e->cvalid = 0; }
    else if (e->lastUpd + 1 < g_curFrame) e->valid = 0;   // new / reused / not updated last frame
    e->vt = vt; e->lastUpd = g_curFrame;
    if (willTick) { memcpy(e->prevM, self + 0x168, 64); e->valid = MatSane(e->prevM); }
    if (vt == (void*)0x0060C1AC) { g_hero = self; g_heroFrame = g_curFrame; }
}
static void InterpApply() {
    g_nApplied = 0; g_camSaved = false;
    if (!g_interp) return;
    ++g_iFrames;
    const float mj2 = g_maxJump * g_maxJump;
    for (int i = 0; i <= IMASK && g_nApplied < 4096; ++i) {
        IEnt* e = &g_ient[i];
        if (!e->obj || g_curFrame - e->lastUpd > 12) continue;   // some objects are updated only on logic-tick frames
        BYTE* o = e->obj;
        if (*(void**)o != e->vt) { e->valid = 0; e->haveLast = 0; e->cvalid = 0; continue; }
        float* M = (float*)(o + 0x168);
        if (!MatSane(M)) continue;
        // change detection: catches movement done by any object (troop logic, scripts), not only the own tick
        if (!e->haveLast) { memcpy(e->lastM, M, 64); e->haveLast = 1; e->cvalid = 0; e->tChange = g_frameMs; e->period = 33.333; }
        else if (memcmp(e->lastM, M, 64)) {
            double iv = g_frameMs - e->tChange;
            if (iv >= 12.0 && iv <= 80.0) e->period = e->period * 0.75 + iv * 0.25;
            memcpy(e->prevC, e->lastM, 64); memcpy(e->lastM, M, 64); e->tChange = g_frameMs; e->cvalid = 1;
        }
        float a; const float* P;
        if (o == g_hero && e->valid && e->lastUpd == g_curFrame) {                                       // hero: exact phase of its own tick
            float step = *(float*)(o + 0x24), acc = *(float*)(o + 0x28);
            if (!(step > 0.0f)) continue;
            a = acc / step; P = e->prevM;
        } else if (e->cvalid) {
            a = (float)((g_frameMs - e->tChange) / (e->period > 1.0 ? e->period : 33.333)); P = e->prevC;
            if (a >= 1.0f) continue;
        } else continue;
        if (!(a > 0.0f)) a = 0.0f;
        if (a > 1.0f) a = 1.0f;
        float dx = M[12] - P[12], dy = M[13] - P[13], dz = M[14] - P[14], d2 = dx * dx + dy * dy + dz * dz;
        if (!(d2 <= mj2)) { ++g_iJumps; e->valid = 0; e->cvalid = 0; continue; }             // teleport / spawn: no blending
        if (P[0] * M[0] + P[1] * M[1] + P[2] * M[2] < 0.0f) continue;          // >90 deg turn in one tick
        if (d2 == 0.0f && !memcmp(P, M, 48)) continue;                       // did not move
        memcpy(e->saved, M, 64);
        for (int r = 0; r < 3; ++r) {                                        // lerp rows, keep row length (scale)
            float* row = M + r * 4; const float* pr = P + r * 4; const float* cr = e->saved + r * 4;
            float lp = sqrtf(pr[0] * pr[0] + pr[1] * pr[1] + pr[2] * pr[2]), lc = sqrtf(cr[0] * cr[0] + cr[1] * cr[1] + cr[2] * cr[2]);
            for (int k = 0; k < 3; ++k) row[k] = pr[k] + (cr[k] - pr[k]) * a;
            float l = sqrtf(row[0] * row[0] + row[1] * row[1] + row[2] * row[2]), want = lp + (lc - lp) * a;
            if (l > 1e-6f) { float f = want / l; row[0] *= f; row[1] *= f; row[2] *= f; }
        }
        M[12] = P[12] + dx * a; M[13] = P[13] + dy * a; M[14] = P[14] + dz * a;
        g_iApplied[g_nApplied++] = e; if (e->u) ++e->u->iCount;
        if (o == g_hero) { float d = sqrtf(d2); if (d > g_iHeroMax) g_iHeroMax = d; g_iHeroSum += d; ++g_iHeroN; }
    }
    g_iObjs += g_nApplied;
    // camera follows the hero's rendered position (the engine copies it before the tick -> 1 frame lag)
    BYTE* hero = g_hero; BYTE* cam = *(BYTE**)0x006CA2C4;
    if (hero && g_heroFrame == g_curFrame && cam && *(void**)cam == (void*)0x006097FC && *(void**)hero == (void*)0x0060C1AC
        && *(BYTE*)(hero + 0x4B4)) {
        float* M = (float*)(hero + 0x168);
        g_camObj = cam; g_camSaved = true;
        g_camSave[0] = *(float*)(cam + 0x50); g_camSave[1] = *(float*)(cam + 0x58);
        *(float*)(cam + 0x50) = M[12]; *(float*)(cam + 0x58) = M[14]; *(BYTE*)(cam + 0x70) = 1;
        ((void (__fastcall*)(void*, void*, int))0x004363D0)(cam, nullptr, 1);   // rebuild view + frustum now
        ++g_iCam;
        static bool once = false; if (!once) { once = true; LOG("smooth: camera %p follows hero %p", cam, hero); }
    }
}
static void InterpRestore() {
    for (int i = 0; i < g_nApplied; ++i) {
        IEnt* e = g_iApplied[i];
        if (*(void**)e->obj == e->vt) memcpy(e->obj + 0x168, e->saved, 64);
    }
    g_nApplied = 0;
    if (g_camSaved && *(BYTE**)0x006CA2C4 == g_camObj) {
        BYTE* hero = g_hero; BYTE* cam = g_camObj;
        // the logic state: hero's real position (what the engine would have copied after the tick)
        if (hero && *(void**)hero == (void*)0x0060C1AC) { *(float*)(cam + 0x50) = *(float*)(hero + 0x64); *(float*)(cam + 0x58) = *(float*)(hero + 0x6C); }
        else { *(float*)(cam + 0x50) = g_camSave[0]; *(float*)(cam + 0x58) = g_camSave[1]; }
        *(BYTE*)(cam + 0x70) = 1;
    }
    g_camSaved = false;
}

// ---------------------------------------------------------------- skeletal animation blending ([Smooth] Animation)
// Skinned meshes (SkinMeshObject) store an integer key frame at +0x1D8 that advances once per 30 Hz logic tick; the
// CPU skinning (CSkeletonMeshSubObject, 0x4B9110) takes the 6-float keys (pitch, yaw, roll, x, y, z per bone) of exactly
// that frame -> limbs move at 30 fps. We remember, per mesh object, the previous frame and when it changed, and feed the
// skinning a blend between previous and current keys (alpha = time since the change / tick period), i.e. the same
// one-tick-behind interpolation as for positions.
static float g_animMaxRad = 1.2f;

struct AEnt { BYTE* obj; void* anim; int cur, prev; double tChange, period; DWORD lastSeen; };
static const int AMASK = 4095; static AEnt g_aent[AMASK + 1];
static DWORD g_aBlends = 0, g_aSkips = 0, g_aCalls = 0;
static AEnt* AGet(BYTE* obj) {
    DWORD h = ((DWORD)obj >> 3) * 2654435761u; AEnt* reuse = nullptr;
    for (int i = 0; i < 32; ++i) {
        AEnt* e = &g_aent[(h + i) & AMASK];
        if (e->obj == obj) return e;
        if (!e->obj) { if (!reuse) reuse = e; break; }
        if (!reuse && g_curFrame - e->lastSeen > 30) reuse = e;
    }
    if (!reuse) return nullptr;
    reuse->obj = obj; reuse->anim = nullptr; reuse->lastSeen = 0;
    return reuse;
}
static AEnt* SkinEnter(BYTE* m) {
    if (!g_animBlend) return nullptr;
    AEnt* e = AGet(m); if (!e) return nullptr;
    void* anim = *(void**)(m + 0x1EC); int f = *(int*)(m + 0x1D8);
    if (e->anim != anim || e->lastSeen + 3 < g_curFrame) {
        e->anim = anim; e->cur = f; e->prev = -1; e->tChange = g_frameMs; e->period = 33.333;
    } else if (f != e->cur) {
        double iv = g_frameMs - e->tChange;
        if (iv >= 12.0 && iv <= 80.0) e->period = e->period * 0.75 + iv * 0.25;
        e->prev = e->cur; e->cur = f; e->tChange = g_frameMs;
    }
    e->lastSeen = g_curFrame;
    return e;
}
typedef void (__fastcall *SkinDraw4_t)(void* lod, void* edx, void* anim, int frame, void* p238, void* eff);
typedef void (__fastcall *SkinDraw3_t)(void* lod, void* edx, void* anim, int frame, void* p238);
static inline void* SkinLod(BYTE* m, unsigned lod) {
    unsigned n = *(unsigned*)(m + 0x1CC); if (lod >= n) lod = n - 1;
    return (*(void***)(m + 0x1E0))[lod];
}
// The key frames of all tracks of the mesh's animation (skeleton bones as well as rigid CMatrixMeshSubObject parts)
// are blended IN PLACE for the duration of one mesh draw and restored right after it (rendering is single-threaded;
// the animation data is shared by all meshes using it, so it must not stay modified).
struct KSave { float* dst; int n; };
static KSave g_kSave[256]; static int g_nKSave = 0;
static float g_kPool[262144]; static int g_kPoolUsed = 0; static int g_kDepth = 0;
static bool Writable(void* p) {   // cached per 64 KB region
    static DWORD cacheKey[512]; static BYTE cacheVal[512];
    DWORD k = (DWORD)p >> 16; int i = (k * 2654435761u) >> 23;
    if (cacheKey[i] == k && cacheVal[i]) return cacheVal[i] == 1;
    MEMORY_BASIC_INFORMATION mi; bool ok = false;
    if (VirtualQuery(p, &mi, sizeof mi) == sizeof mi && mi.State == MEM_COMMIT)
        ok = (mi.Protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE)) != 0 && !(mi.Protect & PAGE_GUARD);
    cacheKey[i] = k; cacheVal[i] = ok ? 1 : 2;
    if (!ok) LOG("animation blending: key data at %p not writable, skipped", p);
    return ok;
}
// ---- hero animation trace (AttTFix_anim.csv): first 1200 draws of the hero's mesh once it animates, F8 = again
static BYTE* HeroMesh() {
    BYTE* h = g_hero; if (!h || *(void**)h != (void*)0x0060C1AC) return nullptr;
    BYTE* c = *(BYTE**)(h + 0x1DC); if (!c || IsBadReadPtr(c, 0x1C8)) return nullptr;
    return *(BYTE**)(c + 0x1C4);
}
static void AnimTrace(BYTE* m, AEnt* e, const char* what, double a, int ntr, float before, float after, float prevv) {
    static BYTE* hm = nullptr; static DWORD hmFrame = 0;
    if (hmFrame != g_curFrame) { hm = HeroMesh(); hmFrame = g_curFrame; }
    if (!hm || m != hm || !g_atrArmed || g_atrLeft <= 0) return;
    if (!g_atr) {
        if (!e || e->prev < 0) return;                       // start once the hero animates
        char p[MAX_PATH]; snprintf(p, sizeof p, "%sAttTFix_anim.csv", g_dir); g_atr = fopen(p, "w");
        if (!g_atr) { g_atrArmed = false; return; }
        fprintf(g_atr, "frame;ms;depth;mesh_frame;cur;prev;period;alpha;result;tracks;key_cur_before;key_after;key_prev;anim\n");
        LOG("anim trace started (hero mesh %p)", m);
    }
    fprintf(g_atr, "%lu;%.2f;%d;%d;%d;%d;%.2f;%.3f;%s;%d;%.5f;%.5f;%.5f;%p\n", g_curFrame, g_frameMs, g_kDepth, *(int*)(m + 0x1D8),
            e ? e->cur : -9, e ? e->prev : -9, e ? e->period : 0.0, a, what, ntr, before, after, prevv, e ? e->anim : nullptr);
    if (--g_atrLeft == 0) { fclose(g_atr); g_atr = nullptr; g_atrArmed = false; LOG("anim trace finished"); }
}
// Euler keys (pitch, yaw, roll as used by D3DXMatrixRotationYawPitchRoll = Rz*Rx*Ry for row vectors).
// Small changes: linear per component. Larger ones (Euler flips near +-90 deg pitch etc.): quaternion slerp.
static inline float WrapPi(float d) { while (d > 3.14159265f) d -= 6.2831853f; while (d < -3.14159265f) d += 6.2831853f; return d; }
static void EulerToQuat(const float* e, float* q) {
    float sp = sinf(e[0] * 0.5f), cp = cosf(e[0] * 0.5f), sy = sinf(e[1] * 0.5f), cy = cosf(e[1] * 0.5f), sr = sinf(e[2] * 0.5f), cr = cosf(e[2] * 0.5f);
    // qx*qz
    float ax = sp * cr, ay = -sp * sr, az = cp * sr, aw = cp * cr;
    // qy*(qx*qz)
    q[0] = cy * ax + sy * az; q[1] = cy * ay + sy * aw; q[2] = cy * az - sy * ax; q[3] = cy * aw - sy * ay;
}
static void QuatToEuler(const float* q, float* e) {
    float x = q[0], y = q[1], z = q[2], w = q[3];
    float r12 = 2 * (y * z - x * w), r02 = 2 * (x * z + y * w), r22 = 1 - 2 * (x * x + y * y), r10 = 2 * (x * y + z * w), r11 = 1 - 2 * (x * x + z * z);
    e[0] = atan2f(-r12, sqrtf(r02 * r02 + r22 * r22)); e[1] = atan2f(r02, r22); e[2] = atan2f(r10, r11);
}
static DWORD g_aQuat = 0;
static inline void BlendBone(float* o, const float* p, const float* c, float a) {
    float d0 = WrapPi(c[0] - p[0]), d1 = WrapPi(c[1] - p[1]), d2 = WrapPi(c[2] - p[2]);
    if (fabsf(d0) < 0.6f && fabsf(d1) < 0.6f && fabsf(d2) < 0.6f) { o[0] = p[0] + d0 * a; o[1] = p[1] + d1 * a; o[2] = p[2] + d2 * a; return; }
    float q0[4], q1[4]; EulerToQuat(p, q0); EulerToQuat(c, q1);
    float dot = q0[0] * q1[0] + q0[1] * q1[1] + q0[2] * q1[2] + q0[3] * q1[3];
    if (dot < 0) { dot = -dot; for (int i = 0; i < 4; ++i) q1[i] = -q1[i]; }
    if (dot < 0.54f) { o[0] = c[0]; o[1] = c[1]; o[2] = c[2]; ++g_aSkips; return; }   // > ~115 deg in one tick: snap
    float k0, k1;
    if (dot > 0.9995f) { k0 = 1 - a; k1 = a; }
    else { float th = acosf(dot), st = sinf(th); k0 = sinf((1 - a) * th) / st; k1 = sinf(a * th) / st; }
    float q[4], l = 0; for (int i = 0; i < 4; ++i) { q[i] = q0[i] * k0 + q1[i] * k1; l += q[i] * q[i]; }
    l = 1.0f / sqrtf(l); for (int i = 0; i < 4; ++i) q[i] *= l;
    QuatToEuler(q, o); ++g_aQuat;
}
static void KeysPatch(AEnt* e, BYTE* m) {
    if (g_kDepth) { AnimTrace(m, e, "nested", -1, 0, 0, 0, 0); return; }
    g_nKSave = 0; g_kPoolUsed = 0;
    if (!g_animBlend) { AnimTrace(m, e, "off", -1, 0, 0, 0, 0); return; }
    if (!e || e->prev < 0 || e->prev == e->cur || !e->anim) { AnimTrace(m, e, "noprev", -1, 0, 0, 0, 0); return; }
    double a = (g_frameMs - e->tChange) / (e->period > 1.0 ? e->period : 33.333);
    if (a >= 0.999) AnimTrace(m, e, "alpha>=1", a, 0, 0, 0, 0);
    if (a >= 0.999) return;
    if (a < 0) a = 0;
    float fa = (float)a;
    BYTE* anim = (BYTE*)e->anim;
    int** tb = *(int***)(anim + 4); int** te = *(int***)(anim + 8);
    if (!tb || te < tb || te - tb > 256) return;
    int f = *(int*)(m + 0x1D8);
    bool any = false;
    for (int** t = tb; t < te; ++t) {
        int* tr = *t; if (!tr) continue;
        float* base = (float*)tr[0]; unsigned frames = (unsigned)tr[2], bones = (unsigned)tr[3];
        if (!base || !frames || !bones || bones > 1024) continue;
        if (!Writable(base) || !Writable(base + (size_t)frames * bones * 6 - 1)) continue;
        unsigned fc = (unsigned)f < frames ? (unsigned)f : 0, fp = (unsigned)e->prev;
        if (fp >= frames || fp == fc) continue;
        int n = (int)bones * 6;
        if (g_nKSave >= 256 || g_kPoolUsed + n > (int)(sizeof g_kPool / sizeof(float))) { ++g_aSkips; break; }
        float* c = base + (size_t)fc * n; const float* pv = base + (size_t)fp * n;
        float* sv = g_kPool + g_kPoolUsed;
        memcpy(sv, c, n * sizeof(float));
        for (unsigned b = 0; b < bones; ++b) {
            float* o = c + b * 6; const float* p = pv + b * 6; const float* cc = sv + b * 6;
            BlendBone(o, p, cc, fa);
            for (int k = 3; k < 6; ++k) o[k] = p[k] + (cc[k] - p[k]) * fa;
        }
        g_kSave[g_nKSave].dst = c; g_kSave[g_nKSave].n = n; ++g_nKSave; g_kPoolUsed += n; any = true;
    }
    if (any) ++g_aBlends;
    {   float b = 0, af = 0, pv = 0;
        if (g_nKSave > 0 && g_kSave[0].n > 7) { b = g_kPool[7]; af = g_kSave[0].dst[7]; }
        if (tb < te && *tb) { int* tr = *tb; unsigned bones = (unsigned)tr[3], fr = (unsigned)tr[2];
            if ((unsigned)e->prev < fr && bones > 1) pv = ((float*)tr[0])[(size_t)e->prev * bones * 6 + 7]; }
        AnimTrace(m, e, any ? "blend" : "skip", a, g_nKSave, b, af, pv); }
}
static void KeysRestore() {
    int off = 0;
    for (int i = 0; i < g_nKSave; ++i) { memcpy(g_kSave[i].dst, g_kPool + off, g_kSave[i].n * sizeof(float)); off += g_kSave[i].n; }
    g_nKSave = 0; g_kPoolUsed = 0;
}
static void SkinDiag(BYTE* m, void* lod) {   // log the structure of the first few distinct animations
    static void* seen[24]; static int ns = 0;
    void* anim = *(void**)(m + 0x1EC); if (ns >= 24 || !anim || !lod) return;
    for (int i = 0; i < ns; ++i) if (seen[i] == anim) return;
    seen[ns++] = anim;
    char buf[600]; int n = snprintf(buf, sizeof buf, "skin mesh %p (%s) anim %p frame %d:", m, RttiName(m), anim, *(int*)(m + 0x1D8));
    int** tb = *(int***)((BYTE*)anim + 4); int** te = *(int***)((BYTE*)anim + 8);
    n += snprintf(buf + n, sizeof buf - n, " tracks=%d", tb && te >= tb ? (int)(te - tb) : -1);
    for (int** t = tb; t && t < te && t < tb + 4; ++t) if (*t) n += snprintf(buf + n, sizeof buf - n, " [frames %d bones %d]", (*t)[2], (*t)[3]);
    void** sb = *(void***)((BYTE*)lod + 8); void** se = *(void***)((BYTE*)lod + 12);
    for (void** q = sb; q && q < se && q < sb + 8 && n < 560; ++q) n += snprintf(buf + n, sizeof buf - n, " %s", *q ? RttiName(*q) : "null");
    LOG("%s", buf);
}
#define SKIN_BEGIN(m) ++g_aCalls; AEnt* e_ = SkinEnter(m); KeysPatch(e_, m); ++g_kDepth;
#define SKIN_END()    --g_kDepth; if (!g_kDepth) KeysRestore();
static void __fastcall h_SkinDraw(BYTE* m, void*, unsigned lod) {           // 0x4C0DE0
    SKIN_BEGIN(m)
    void* l = SkinLod(m, lod); SkinDiag(m, l);
    ((Method0_t)0x004AC890)(m, nullptr);
    ((SkinDraw4_t)0x004C0620)(l, nullptr, *(void**)(m + 0x1EC), *(int*)(m + 0x1D8), m + 0x238, *(void**)(m + 0x3C));
    SKIN_END()
}
static void __fastcall h_SkinDrawNoWorld(BYTE* m, void*, unsigned lod) {    // 0x4C0EA0
    SKIN_BEGIN(m)
    SkinDiag(m, SkinLod(m, lod));
    ((SkinDraw4_t)0x004C0620)(SkinLod(m, lod), nullptr, *(void**)(m + 0x1EC), *(int*)(m + 0x1D8), m + 0x238, *(void**)(m + 0x3C));
    SKIN_END()
}
static void __fastcall h_SkinDraw3(BYTE* m, void*, unsigned lod) {          // 0x4C0E60
    SKIN_BEGIN(m)
    ((SkinDraw3_t)0x004C0680)(SkinLod(m, lod), nullptr, *(void**)(m + 0x1EC), *(int*)(m + 0x1D8), m + 0x238);
    SKIN_END()
}
static void __fastcall h_SkinDraw3Cur(BYTE* m, void*) {                     // 0x4C0E30 (lod = +0x1D0, unclamped)
    SKIN_BEGIN(m)
    void* l = (*(void***)(m + 0x1E0))[*(unsigned*)(m + 0x1D0)];
    ((SkinDraw3_t)0x004C0680)(l, nullptr, *(void**)(m + 0x1EC), *(int*)(m + 0x1D8), m + 0x238);
    SKIN_END()
}
static void InstallAnimBlend() {
    struct { DWORD at; BYTE b[6]; void* fn; } fns[] = {
        { 0x004C0DE0, { 0x56, 0x8B, 0xF1, 0x8B, 0x86, 0xCC }, (void*)h_SkinDraw },
        { 0x004C0E30, { 0x8B, 0x91, 0xD8, 0x01, 0x00, 0x00 }, (void*)h_SkinDraw3Cur },
        { 0x004C0E60, { 0x8B, 0x81, 0xCC, 0x01, 0x00, 0x00 }, (void*)h_SkinDraw3 },
        { 0x004C0EA0, { 0x8B, 0x81, 0xCC, 0x01, 0x00, 0x00 }, (void*)h_SkinDrawNoWorld },
    };
    for (auto& f : fns) if (memcmp((void*)f.at, f.b, 6)) { LOG("animation blending: unexpected bytes at %08lX, disabled", f.at); return; }
    for (auto& f : fns) { BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)f.fn - (f.at + 5); PatchBytes((BYTE*)f.at, j, 5); }
    LOG("animation blending installed (skinned meshes, max %.2f rad per tick)", g_animMaxRad);
}
static void InterpStats() {
    if (!g_iFrames && !g_aCalls) return;
    PLOG("SMOOTH frames=%lu objects/frame=%.1f jumps=%lu camera=%lu hero step avg=%.3f max=%.3f",
         g_iFrames, (double)g_iObjs / g_iFrames, g_iJumps, g_iCam, g_iHeroN ? g_iHeroSum / g_iHeroN : 0.0f, g_iHeroMax);
    g_iFrames = g_iObjs = g_iJumps = g_iCam = 0; g_iHeroMax = g_iHeroSum = 0; g_iHeroN = 0;
    { char b[400]; int n = 0; b[0] = 0;
      for (int i = 0; i < g_nupd && n < 380; ++i) if (g_upd[i].iCount) { n += snprintf(b + n, sizeof b - n, " %s=%lu", g_upd[i].name, g_upd[i].iCount); g_upd[i].iCount = 0; }
      if (n) PLOG("SMOOTH by class (object-frames):%s", b); }
    if (g_aCalls) PLOG("ANIM mesh draws=%lu blended=%lu bones via quaternion=%lu snapped=%lu", g_aCalls, g_aBlends, g_aQuat, g_aSkips);
    g_aQuat = 0;
    g_aCalls = g_aBlends = g_aSkips = 0;
}
static UpdInfo* UpdFor(BYTE* self) {
    void* vt = *(void**)self;
    for (int i = 0; i < g_nupd; ++i) if (g_upd[i].vt == vt) return &g_upd[i];
    if (g_nupd >= 64) return nullptr;
    UpdInfo* u = &g_upd[g_nupd++]; u->vt = vt; snprintf(u->name, 48, "%s", RttiName(self)); u->step = *(float*)(self + 0x24);
    u->calls = u->ticks = u->frameTicks = 0;
    u->interp = 0;
    if (ClassListed(u->name)) u->interp = (*(void***)self)[10] == (void*)0x004AB7D0 ? 1 : -1;
    LOG("updater: %s vt=%p step=%.2f ms%s", u->name, vt, u->step,
        u->interp > 0 ? " [smooth]" : u->interp < 0 ? " [smooth: not a render object, skipped]" : "");
    return u;
}
typedef void (__fastcall *VTick_t)(void* self, void* edx);
typedef void (__fastcall *VAfter_t)(void* self, void* edx, int n);
static void __fastcall h_UpdaterUpdate(BYTE* self, void* /*edx*/, float dt) {
    UpdInfo* u = UpdFor(self);
    float acc = *(float*)(self + 0x28) + dt;
    *(float*)(self + 0x28) = acc;
    if (u && u->interp > 0) InterpBeforeTicks(self, *(float*)(self + 0x24) <= acc, u);
    if (*(float*)(self + 0x24) <= acc) {
        int n = 0; float step;
        do {
            ((VTick_t)(*(void***)self)[5])(self, nullptr);
            step = *(float*)(self + 0x24);
            ++n;
            acc = *(float*)(self + 0x28) - step;
            *(float*)(self + 0x28) = acc;
        } while (step <= acc);
        ((VAfter_t)(*(void***)self)[9])(self, nullptr, n);
        if (u) { u->ticks += n; u->frameTicks += n; }
    }
    if (u) ++u->calls;
}
static void TraceFrame(DWORD frame, double nowMs, double ft, const char* sceneCls) {
    if (g_traceSec <= 0) return;
    bool world = sceneCls && (!strcmp(sceneCls, "CWorldLevel") || !strcmp(sceneCls, "CTacticLevel"));
    if (!g_trace) {
        if (!world) { for (int i = 0; i < g_nupd; ++i) g_upd[i].frameTicks = 0; return; }
        char p[MAX_PATH]; snprintf(p, sizeof p, "%sAttTFix_trace.csv", g_dir);
        g_trace = fopen(p, "w"); g_traceStartMs = nowMs;
        if (g_trace) fprintf(g_trace, "frame;time_ms;frame_ms;dt_ms;scene;updater_ticks\n");
    }
    if (!g_trace) return;
    if (nowMs - g_traceStartMs > g_traceSec * 1000.0) { fclose(g_trace); g_trace = (FILE*)1; g_traceSec = 0; LOG("trace finished"); return; }
    if (g_trace == (FILE*)1) return;
    fprintf(g_trace, "%lu;%.2f;%.3f;%.3f;%s;", frame, nowMs - g_traceStartMs, ft, g_lastDt * 1000.0f, sceneCls ? sceneCls : "");
    for (int i = 0; i < g_nupd; ++i) { if (g_upd[i].frameTicks) fprintf(g_trace, "%s=%lu ", g_upd[i].name, g_upd[i].frameTicks); g_upd[i].frameTicks = 0; }
    fputc('\n', g_trace);
}
static void InstallUpdaterRewrite() {
    static const BYTE p[8] = { 0xD9, 0x44, 0x24, 0x04, 0x56, 0x8B, 0xF1, 0xD8 };
    BYTE* t = (BYTE*)0x00424D90;
    if (memcmp(t, p, 8)) { LOG("updater rewrite: unexpected bytes"); return; }
    BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)(void*)h_UpdaterUpdate - (DWORD)(t + 5);
    PatchBytes(t, j, 5); LOG("updater loop replaced (trace %d s)", g_traceSec);
}

static void InstallFrameRewrite() {
    static const BYTE expect[8] = { 0x51, 0x53, 0x55, 0x56, 0x8B, 0xF1, 0x8B, 0x4E };
    BYTE* t = (BYTE*)0x0044A9C0;
    if (memcmp(t, expect, 8)) { LOG("frame rewrite: unexpected bytes, profiler disabled"); return; }
    BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)(void*)h_Frame - (DWORD)(t + 5);
    PatchBytes(t, j, 5);
    LARGE_INTEGER f; QueryPerformanceFrequency(&f); g_tickMs = 1000.0 / (double)f.QuadPart;
    if (g_perfOn) {
        char p[MAX_PATH]; snprintf(p, sizeof p, "%sAttTFix_perf.log", g_dir);
        char prev[MAX_PATH]; snprintf(prev, sizeof prev, "%sAttTFix_perf.prev.log", g_dir); DeleteFileA(prev); MoveFileA(p, prev);
        g_perf = fopen(p, "w");
        PLOG("AttTFix performance log. STATS every 5 s; HITCH = frame longer than %s", g_hitchMs > 0 ? "HitchMs" : "max(25 ms, 2.5 x median)");
        PLOG("sections: u.* = update (timer, sys=[0x6C8C24], input+keys, cursor, scene logic, camera), r.* = render (clear+BeginScene, scene draw, cursor+overlay, EndScene, Present incl. vsync/GPU wait), other = message pump + frame limiter");
    }
    LOG("frame function replaced (profiler %s)", g_perfOn ? "on" : "off");
    InstallRenderRewrite();
    InstallOptimizations();
    InstallUpdaterRewrite();
    InstallAnimBlend();
}


// ---------------------------------------------------------------- sampling profiler
// A background thread suspends the game thread ~1000x/s, records EIP (exclusive) and the return addresses found
// on the stack (inclusive), mapped to function starts from Ghidra (funcs_table.h). Code outside the exe is
// attributed to its module (d3d9, driver, kernel...).
#include "funcs_table.h"
static const int NF = sizeof(g_funcStarts) / sizeof(g_funcStarts[0]);
static int FuncIndex(DWORD a) {
    if (a < 0x401000 || a >= 0x607000) return -1;
    int lo = 0, hi = NF - 1;
    while (lo < hi) { int mid = (lo + hi + 1) / 2; if (g_funcStarts[mid] <= a) lo = mid; else hi = mid - 1; }
    return lo;
}
static const struct { DWORD a; const char* n; } g_knownNames[] = {
    { 0x44A9C0, "Engine::Frame(orig)" }, { 0x44E480, "Engine::Render(orig)" }, { 0x53C5D0, "CWorldLevel::Update" },
    { 0x5180C0, "CTacticLevel::Update" }, { 0x4B1E20, "Scene::Render" }, { 0x4E4220, "Timer::Tick" },
    { 0x432620, "Script::DoFile" }, { 0x57D220, "Script::RunBuffer" }, { 0x46CB50, "CInput::Poll" },
    { 0x442AD0, "CCursor::Update" }, { 0x521BC0, "Camera::SetProjection" }, { 0x4C53A0, "Sound3D::Stop" },
};
static const char* FuncName(int idx, char* buf) {
    DWORD a = g_funcStarts[idx];
    for (auto& k : g_knownNames) if (k.a == a) return k.n;
    sprintf(buf, "FUN_%08lX", a); return buf;
}
static DWORD* g_excl = nullptr; static DWORD* g_incl = nullptr; static DWORD g_samples = 0, g_samplesExe = 0;
struct ModCount { HMODULE m; DWORD n; char name[32]; };
static ModCount g_mods[48]; static int g_nmods = 0;
static CRITICAL_SECTION g_profCs; static HANDLE g_mainThread = nullptr; static DWORD g_mainStackBase = 0;
static volatile LONG g_samplerRun = 0;
struct Sample { DWORD frame; int excl; short ninc; int inc[20]; };
static Sample g_ring[1024]; static volatile LONG g_ringPos = 0;
static bool IsReturnAddr(DWORD v) {
    if (v < 0x401006 || v >= 0x607000) return false;
    const BYTE* p = (const BYTE*)v;
    if (p[-5] == 0xE8) return true;                               // call rel32
    if (p[-2] == 0xFF && (p[-1] & 0xF8) == 0xD0) return true;      // call reg
    if (p[-3] == 0xFF && (p[-2] & 0xF8) == 0x50) return true;      // call [reg+disp8]
    if (p[-6] == 0xFF && (p[-5] == 0x15 || (p[-5] & 0xF8) == 0x90)) return true;   // call [abs] / [reg+disp32]
    if (p[-2] == 0xFF && (p[-1] & 0xF8) == 0x10) return true;      // call [reg]
    return false;
}
static DWORD WINAPI SamplerThread(void*) {
    SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_TIME_CRITICAL);
    static DWORD stackCopy[1024];
    while (g_samplerRun) {
        Sleep(1);
        CONTEXT c; c.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
        if (SuspendThread(g_mainThread) == (DWORD)-1) continue;
        int nWords = 0; BOOL okc = GetThreadContext(g_mainThread, &c);
        if (okc) {
            DWORD sp = c.Esp, lim = g_mainStackBase;
            if (lim > sp) { nWords = (int)((lim - sp) / 4); if (nWords > 1024) nWords = 1024; memcpy(stackCopy, (void*)sp, nWords * 4); }
        }
        ResumeThread(g_mainThread);
        if (!okc) continue;
        Sample smp; smp.frame = g_curFrame; smp.ninc = 0;
        smp.excl = FuncIndex(c.Eip);
        EnterCriticalSection(&g_profCs);
        ++g_samples;
        if (smp.excl >= 0) { ++g_samplesExe; ++g_excl[smp.excl]; }
        else {   // outside the exe: attribute to module
            HMODULE m = nullptr;
            GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)c.Eip, &m);
            int j = 0; for (; j < g_nmods; ++j) if (g_mods[j].m == m) break;
            if (j == g_nmods && g_nmods < 48) {
                g_mods[j].m = m; g_mods[j].n = 0; char path[MAX_PATH] = "?";
                if (m) GetModuleFileNameA(m, path, MAX_PATH);
                const char* bn = strrchr(path, '\\'); snprintf(g_mods[j].name, 32, "%s", bn ? bn + 1 : path); ++g_nmods;
            }
            if (j < g_nmods) ++g_mods[j].n;
        }
        // inclusive: functions on the stack (unique), plus the current one
        if (smp.excl >= 0) { smp.inc[smp.ninc++] = smp.excl; ++g_incl[smp.excl]; }
        for (int i = 0; i < nWords && smp.ninc < 20; ++i) {
            DWORD v = stackCopy[i];
            if (!IsReturnAddr(v)) continue;
            int f = FuncIndex(v); if (f < 0) continue;
            bool dup = false; for (int k = 0; k < smp.ninc; ++k) if (smp.inc[k] == f) { dup = true; break; }
            if (dup) continue;
            smp.inc[smp.ninc++] = f; ++g_incl[f];
        }
        LeaveCriticalSection(&g_profCs);
        LONG pos = InterlockedIncrement(&g_ringPos) & 1023;
        g_ring[pos] = smp;
    }
    return 0;
}
static void StartSampler() {
    if (!g_samplerOn || g_samplerRun) return;
    DWORD tib; __asm__ volatile("movl %%fs:4, %0" : "=r"(tib)); g_mainStackBase = tib;   // TEB.StackBase of the game thread
    g_mainThread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, GetCurrentThreadId());
    if (!g_mainThread) { LOG("sampler: OpenThread failed"); return; }
    g_excl = (DWORD*)calloc(NF, 4); g_incl = (DWORD*)calloc(NF, 4);
    InitializeCriticalSection(&g_profCs);
    g_samplerRun = 1;
    CloseHandle(CreateThread(nullptr, 0, SamplerThread, nullptr, 0, nullptr));
    LOG("sampling profiler started (~1 kHz)");
}
static void PLOG(const char* fmt, ...);
static void DumpProfile(const char* why) {
    if (!g_samplerRun || !g_samples) return;
    EnterCriticalSection(&g_profCs);
    DWORD total = g_samples;
    // top lists
    static int idx[64]; char nb[32], line[2048]; int len;
    for (int pass = 0; pass < 2; ++pass) {
        DWORD* arr = pass == 0 ? g_excl : g_incl;
        int n = 0;
        for (int i = 0; i < NF; ++i) {
            if (!arr[i]) continue;
            int pos = n < 20 ? n++ : 20;
            if (pos == 20) { if (arr[i] <= arr[idx[19]]) continue; pos = 19; }
            idx[pos] = i;
            while (pos > 0 && arr[idx[pos]] > arr[idx[pos - 1]]) { int t = idx[pos]; idx[pos] = idx[pos - 1]; idx[pos - 1] = t; --pos; }
        }
        len = 0;
        for (int i = 0; i < n; ++i) len += snprintf(line + len, sizeof line - len, " %s=%.1f%%", FuncName(idx[i], nb), 100.0 * arr[idx[i]] / total);
        PLOG("PROFILE %s (%lu samples) %s:%s", why, total, pass == 0 ? "self time" : "incl. time", line);
    }
    len = 0;
    len += snprintf(line + len, sizeof line - len, " ATThrone.exe=%.1f%%", 100.0 * g_samplesExe / total);
    for (int j = 0; j < g_nmods; ++j) len += snprintf(line + len, sizeof line - len, " %s=%.1f%%", g_mods[j].name, 100.0 * g_mods[j].n / total);
    PLOG("PROFILE %s modules:%s", why, line);
    memset(g_excl, 0, NF * 4); memset(g_incl, 0, NF * 4); g_samples = g_samplesExe = 0;
    for (int j = 0; j < g_nmods; ++j) g_mods[j].n = 0;
    LeaveCriticalSection(&g_profCs);
}
static void HitchProfile(DWORD frame, char* out, int outSize) {   // top functions sampled during a given frame
    out[0] = 0; if (!g_samplerRun) return;
    static int fi[64]; static int cnt[64]; int nf = 0, ns = 0;
    for (int k = 0; k < 1024; ++k) {
        const Sample& s = g_ring[k]; if (s.frame != frame) continue; ++ns;
        for (int j = 0; j < s.ninc; ++j) {
            int f = s.inc[j], q = 0; for (; q < nf; ++q) if (fi[q] == f) break;
            if (q == nf) { if (nf == 64) continue; fi[nf] = f; cnt[nf++] = 0; }
            ++cnt[q];
        }
    }
    if (!ns) return;
    int len = snprintf(out, outSize, " | sampled %d:", ns); char nb[32];
    for (int t = 0; t < 8; ++t) {   // top 8 by inclusive count
        int best = -1; for (int q = 0; q < nf; ++q) if (cnt[q] > 0 && (best < 0 || cnt[q] > cnt[best])) best = q;
        if (best < 0) break;
        len += snprintf(out + len, outSize - len, " %s(%d)", FuncName(fi[best], nb), cnt[best]); cnt[best] = 0;
    }
}

// ---------------------------------------------------------------- engine bug fixes
// Null-"this" guard: stub = test ecx,ecx / jnz orig / inc [counter] / ret N ; orig: <prolog> / jmp target+len
static volatile LONG g_guardHits[8]; static const char* g_guardName[8]; static int g_nGuards = 0;
static bool GuardNullThis(const char* nameTag, BYTE* target, const BYTE* expect, int len, WORD retImm) {
    if (memcmp(target, expect, len)) { LOG("guard %s: unexpected bytes, skipped", nameTag); return false; }
    int id = g_nGuards++; g_guardName[id] = nameTag;
    BYTE* st = (BYTE*)VirtualAlloc(nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    BYTE* p = st;
    *p++ = 0x85; *p++ = 0xC9;                                   // test ecx,ecx
    *p++ = 0x75; *p++ = 9;                                      // jnz +9
    *p++ = 0xFF; *p++ = 0x05; *(DWORD*)p = (DWORD)&g_guardHits[id]; p += 4;   // inc dword [hits]
    *p++ = 0xC2; *(WORD*)p = retImm; p += 2;                    // ret N
    memcpy(p, target, len); p += len;                           // original prolog
    *p++ = 0xE9; *(DWORD*)p = (DWORD)(target + len) - (DWORD)(p + 4); p += 4;
    DWORD old; VirtualProtect(target, len, PAGE_EXECUTE_READWRITE, &old);
    target[0] = 0xE9; *(DWORD*)(target + 1) = (DWORD)st - (DWORD)(target + 5);
    for (int i = 5; i < len; ++i) target[i] = 0x90;
    VirtualProtect(target, len, old, &old); FlushInstructionCache(GetCurrentProcess(), target, len);
    LOG("guard %s installed at %p", nameTag, target);
    return true;
}
static void LogGuardHits() { for (int i = 0; i < g_nGuards; ++i) if (g_guardHits[i]) LOG("guard %s prevented %ld null-pointer calls", g_guardName[i], g_guardHits[i]); }

// First-chance access violations inside the game's code (the engine's own __except hides them)
static volatile LONG g_avCount = 0;
static LONG CALLBACK VectoredAV(EXCEPTION_POINTERS* ep) {
    auto er = ep->ExceptionRecord;
    if (er->ExceptionCode != 0xC0000005) return EXCEPTION_CONTINUE_SEARCH;
    DWORD a = (DWORD)er->ExceptionAddress;
    if (a < 0x401000 || a >= 0x607000) return EXCEPTION_CONTINUE_SEARCH;
    LONG n = InterlockedIncrement(&g_avCount);
    if (n > 20) return EXCEPTION_CONTINUE_SEARCH;
    auto c = ep->ContextRecord;
    LOG("ACCESS VIOLATION #%ld at %08lX (%s %08lX) EAX=%08lX EBX=%08lX ECX=%08lX EDX=%08lX ESI=%08lX EDI=%08lX EBP=%08lX ESP=%08lX",
        n, a, er->ExceptionInformation[0] ? "write" : "read", (DWORD)er->ExceptionInformation[1],
        c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    DWORD* sp = (DWORD*)c->Esp; char buf[512]; int len = 0, k = 0;
    for (int i = 0; i < 2048 && k < 24 && !IsBadReadPtr(sp + i, 4); ++i) {
        DWORD v = sp[i]; if (v >= 0x401000 && v < 0x607000) { len += snprintf(buf + len, sizeof buf - len, " %08lX", v); ++k; }
    }
    LOG("  stack:%s", k ? buf : " -");
    FrameEvent("access violation at %08lX", a);
    if (n == 1) WriteDump(ep, "av");
    return EXCEPTION_CONTINUE_SEARCH;
}

// ---------------------------------------------------------------- dinput8 proxy
typedef HRESULT (WINAPI *DI8Create_t)(HINSTANCE, DWORD, REFIID, LPVOID*, void*);
static DI8Create_t o_DI8Create;
extern "C" __declspec(dllexport) HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID* o, void* u) {
    if (!o_DI8Create) {
        char p[MAX_PATH]; GetSystemDirectoryA(p, MAX_PATH); strcat(p, "\\dinput8.dll");
        HMODULE m = LoadLibraryA(p);
        o_DI8Create = m ? (DI8Create_t)GetProcAddress(m, "DirectInput8Create") : nullptr;
        if (!o_DI8Create) { LOG("FATAL: system dinput8 not loaded"); return E_FAIL; }
    }
    return o_DI8Create(h, v, r, o, u);
}

// ---------------------------------------------------------------- init
static void Init() {
    GetModuleFileNameA(nullptr, g_dir, MAX_PATH);
    char* s = strrchr(g_dir, '\\'); if (s) s[1] = 0;
    InitializeCriticalSection(&g_logcs);
    char path[MAX_PATH]; snprintf(path, sizeof path, "%sAttTFix.log", g_dir);
    { char prev[MAX_PATH]; snprintf(prev, sizeof prev, "%sAttTFix.prev.log", g_dir); DeleteFileA(prev); MoveFileA(path, prev); }
    g_log = fopen(path, "w");
    OSVERSIONINFOA ov = { sizeof ov }; GetVersionExA(&ov);
    LOG("AttTFix " ATTFIX_VERSION " loaded; Windows %lu.%lu build %lu", ov.dwMajorVersion, ov.dwMinorVersion, ov.dwBuildNumber);
    // sanity: is this the expected exe?
    BYTE* base = (BYTE*)GetModuleHandleA(nullptr);
    auto nt = (IMAGE_NT_HEADERS*)(base + ((IMAGE_DOS_HEADER*)base)->e_lfanew);
    LOG("exe timestamp %08lX (expected 475EABAF), LAA=%d", nt->FileHeader.TimeDateStamp, (nt->FileHeader.Characteristics & 0x20) != 0);
    // command line + graphic.cfg
    LOG("cmdline: %s", GetCommandLineA());
    snprintf(path, sizeof path, "%sgraphic.cfg", g_dir);
    if (FILE* f = fopen(path, "rb")) { int wh[2] = {0, 0}; BYTE fs[17]; fread(wh, 4, 2, f); fread(fs, 1, 9, f); fclose(f); LOG("graphic.cfg: %dx%d fullscreen=%d", wh[0], wh[1], fs[8]); }
    // DPI awareness (avoid Windows DPI virtualization in windowed mode)
    if (auto u = GetModuleHandleA("user32.dll")) if (auto f = (BOOL (WINAPI*)())GetProcAddress(u, "SetProcessDPIAware")) LOG("SetProcessDPIAware -> %d", f());
    LOG("screen metrics %dx%d", GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN));
    snprintf(path, sizeof path, "%sAttTFix.ini", g_dir);
    if (GetFileAttributesA(path) == INVALID_FILE_ATTRIBUTES)
        WritePrivateProfileStringA("UI", "Widescreen", "1  ; 1 = UI on a centered 4:3 canvas, 0 = original stretched UI", path);
    g_wsEnabled = GetPrivateProfileIntA("UI", "Widescreen", 1, path);
    strcpy(g_iniPath, path);
    char tmp[16];
    if (!GetPrivateProfileStringA("Video", "VSync", "", tmp, sizeof tmp, path)) {
        WritePrivateProfileStringA("Video", "VSync", "1  ; 1 = vertical sync (smooth, no tearing), 0 = off", path);
        WritePrivateProfileStringA("Video", "FpsLimit", "0  ; frame cap when VSync=0 (0 = unlimited)", path);
        WritePrivateProfileStringA("Video", "AllCores", "1  ; 1 = let the game use all CPU cores (original pins it to core 0)", path);
        WritePrivateProfileStringA("Mouse", "CursorSpeed", "1.00", path);
        WritePrivateProfileStringA("Mouse", "CameraSpeed", "1.00", path);
    }
    g_vsync = GetPrivateProfileIntA("Video", "VSync", 1, path);
    g_fpsLimit = GetPrivateProfileIntA("Video", "FpsLimit", 0, path);
    g_allCores = GetPrivateProfileIntA("Video", "AllCores", 1, path);
    if (!GetPrivateProfileStringA("Perf", "Log", "", tmp, sizeof tmp, path)) {
        WritePrivateProfileStringA("Perf", "Log", "0  ; 1 = write AttTFix_perf.log (FPS stats every 5 s, hitches)", path);
        WritePrivateProfileStringA("Perf", "HitchMs", "0  ; frame time that counts as a hitch (0 = auto: 2.5 x median, min 25 ms)", path);
        WritePrivateProfileStringA("Perf", "FpsInTitle", "0  ; show FPS in the window title (windowed mode)", path);
    }
    g_perfOn = GetPrivateProfileIntA("Perf", "Log", 0, path);
    g_hitchMs = (float)GetPrivateProfileIntA("Perf", "HitchMs", 0, path);
    g_fpsTitle = GetPrivateProfileIntA("Perf", "FpsInTitle", 0, path);
    if (!GetPrivateProfileStringA("Perf", "ShowFps", "", tmp, sizeof tmp, path))
        WritePrivateProfileStringA("Perf", "ShowFps", "0  ; on-screen FPS / frame time overlay (F11 toggles in game)", path);
    g_showFps = GetPrivateProfileIntA("Perf", "ShowFps", 0, path);
    if (!GetPrivateProfileStringA("Perf", "Sampler", "", tmp, sizeof tmp, path)) {
        WritePrivateProfileStringA("Perf", "Sampler", "0  ; sampling profiler (top functions in AttTFix_perf.log)", path);
        WritePrivateProfileStringA("Perf", "ProfileEvery", "20  ; seconds between PROFILE dumps", path);
    }
    g_samplerOn = GetPrivateProfileIntA("Perf", "Sampler", 0, path);
    if (!GetPrivateProfileStringA("Video", "Renderer", "", tmp, sizeof tmp, path))
        WritePrivateProfileStringA("Video", "Renderer", "d3d9  ; d3d9 = system Direct3D 9, dxvk = DXVK (Vulkan) from the dxvk folder", path);
    GetPrivateProfileStringA("Video", "Renderer", "d3d9", tmp, sizeof tmp, path);
    g_renderer = !_strnicmp(tmp, "dxvk", 4) ? 1 : 0;
    if (!GetPrivateProfileStringA("Video", "WindowedSync", "", tmp, sizeof tmp, path))
        WritePrivateProfileStringA("Video", "WindowedSync", "dwm  ; VSync in a window: dwm = frames locked to the monitor's vblank, flush = DwmFlush, timer = plain timer", path);
    GetPrivateProfileStringA("Video", "WindowedSync", "dwm", tmp, sizeof tmp, path);
    g_dwmSync = !_strnicmp(tmp, "timer", 5) ? 0 : !_strnicmp(tmp, "flush", 5) ? 2 : 1;
    if (!GetPrivateProfileStringA("Optimize", "ListenerHz", "", tmp, sizeof tmp, path))
        WritePrivateProfileStringA("Optimize", "ListenerHz", "60  ; 3D sound listener updates per second (0 = every frame, original)", path);
    g_listenerHz = GetPrivateProfileIntA("Optimize", "ListenerHz", 60, path);
    if (!GetPrivateProfileStringA("Perf", "TraceSeconds", "", tmp, sizeof tmp, path))
        WritePrivateProfileStringA("Perf", "TraceSeconds", "0  ; per-frame trace (AttTFix_trace.csv) for the first N seconds in the world (0 = off)", path);
    g_traceSec = GetPrivateProfileIntA("Perf", "TraceSeconds", 0, path);
    g_profileEvery = GetPrivateProfileIntA("Perf", "ProfileEvery", 20, path);
    if (!GetPrivateProfileStringA("Video", "SkipIntro", "", tmp, sizeof tmp, path))
        WritePrivateProfileStringA("Video", "SkipIntro", "0", path);
    g_skipIntro = GetPrivateProfileIntA("Video", "SkipIntro", 0, path);
    if (!GetPrivateProfileStringA("Game", "Language", "", tmp, sizeof tmp, path))   // first start: follow the Windows UI language
        WritePrivateProfileStringA("Game", "Language", PRIMARYLANGID(GetUserDefaultUILanguage()) == LANG_RUSSIAN ? "ru" : "en", path);
    GetPrivateProfileStringA("Game", "Language", "ru", tmp, sizeof tmp, path);
    g_langSetting = g_langActive = !_strnicmp(tmp, "en", 2) ? 1 : 0;
    InstallLanguage();
    {   // startup videos (1CLogo, logo, intro): the engine skips them with "-nologo"; "test al,al" -> "xor al,al"
        static const BYTE p[8] = { 0x84, 0xC0, 0x0F, 0x84, 0xE5, 0x00, 0x00, 0x00 };
        if (g_skipIntro) {
            if (!memcmp((void*)0x0044F75E, p, 8)) { static const BYTE x[2] = { 0x32, 0xC0 }; PatchBytes((void*)0x0044F75E, x, 2); LOG("startup videos skipped (SkipIntro=1)"); }
            else LOG("SkipIntro: unexpected bytes");
        }
    }
    if (!GetPrivateProfileStringA("Smooth", "Interpolate", "", tmp, sizeof tmp, path)) {
        WritePrivateProfileStringA("Smooth", "Interpolate", "1  ; 1 = smooth movement of units/hero/camera between 30 Hz logic ticks, 0 = original", path);
        WritePrivateProfileStringA("Smooth", "Classes", g_interpClasses, path);
        WritePrivateProfileStringA("Smooth", "MaxJump", "6  ; movement per tick above this is treated as a teleport (no blending)", path);
    }
    g_interp = GetPrivateProfileIntA("Smooth", "Interpolate", 1, path);
    { char def[512]; strcpy(def, g_interpClasses); GetPrivateProfileStringA("Smooth", "Classes", def, g_interpClasses, sizeof g_interpClasses, path);
      if (!strcmp(g_interpClasses, "CHero,CNpc,CWorldUnit,CTacticCreature,CWorldHeroCreature,LuaTacticCreature") ||
          !strcmp(g_interpClasses, "CHero,CNpc,SAO,CWorldUnit,CTacticCreature,CWorldHeroCreature,LuaTacticCreature")) {   // 0.9.2 default -> current
          strcpy(g_interpClasses, def); WritePrivateProfileStringA("Smooth", "Classes", def, path); } }
    g_maxJump = ReadIniFloat("Smooth", "MaxJump", 6.0f);
    if (!GetPrivateProfileStringA("Smooth", "Animation", "", tmp, sizeof tmp, path))
        WritePrivateProfileStringA("Smooth", "Animation", "1  ; 1 = blend skeletal animation between 30 fps key frames, 0 = original", path);
    g_animBlend = GetPrivateProfileIntA("Smooth", "Animation", 1, path);
    LOG("ini: Smooth Interpolate=%d Animation=%d MaxJump=%.1f Classes=%s", g_interp, g_animBlend, g_maxJump, g_interpClasses);
    g_cursorSpeed = ReadIniFloat("Mouse", "CursorSpeed", 1.0f);
    g_cameraSpeed = ReadIniFloat("Mouse", "CameraSpeed", 1.0f);
    if (g_cursorSpeed < 0.1f || g_cursorSpeed > 10.f) g_cursorSpeed = 1.0f;
    if (g_cameraSpeed < 0.1f || g_cameraSpeed > 10.f) g_cameraSpeed = 1.0f;
    LOG("ini: Widescreen=%d VSync=%d FpsLimit=%d AllCores=%d CursorSpeed=%.2f CameraSpeed=%.2f", g_wsEnabled, g_vsync, g_fpsLimit, g_allCores, g_cursorSpeed, g_cameraSpeed);
    timeBeginPeriod(1);
    QueryPerformanceFrequency(&g_qpf);
    g_waitTimer = CreateWaitableTimerExW(nullptr, nullptr, 0x00000002 /*CREATE_WAITABLE_TIMER_HIGH_RESOLUTION*/, TIMER_ALL_ACCESS);
    if (!g_waitTimer) g_waitTimer = CreateWaitableTimerW(nullptr, FALSE, nullptr);
    o_D3DCreate = (D3DCreate_t)PatchIAT("d3d9.dll", "Direct3DCreate9", (void*)h_D3DCreate);
    o_CxxThrow = (CxxThrow_t)PatchIAT("MSVCR80.dll", "_CxxThrowException", (void*)h_CxxThrow);
    o_SUEF = (SUEF_t)PatchIAT("KERNEL32.dll", "SetUnhandledExceptionFilter", (void*)h_SUEF);
    o_exit = (exit_t)PatchIAT("MSVCR80.dll", "exit", (void*)h_exit);
    o_ExitProcess = (ExitProcess_t)PatchIAT("KERNEL32.dll", "ExitProcess", (void*)h_ExitProcess);
    o_MBA = (MBA_t)PatchIAT("USER32.dll", "MessageBoxA", (void*)h_MBA);
    o_MBW = (MBW_t)PatchIAT("USER32.dll", "MessageBoxW", (void*)h_MBW);
    AddVectoredExceptionHandler(1, VectoredAV);
    o_SPAM = (SPAM_t)PatchIAT("KERNEL32.dll", "SetProcessAffinityMask", (void*)h_SPAM);
    InstallPerfPatches();
    {   // Sound: stopping a 3D sound after the sound manager [0x6CA4B4] is gone (return to main menu) -> null this
        static const BYTE p[7] = { 0x83, 0xEC, 0x0C, 0x8B, 0x54, 0x24, 0x10 };
        GuardNullThis("Sound3D.Stop(0x4C53A0)", (BYTE*)0x004C53A0, p, 7, 0x0C);
    }
    static const BYTE doFileProlog[7] = { 0x6A, 0xFF, 0x68, 0x5A, 0x63, 0x5E, 0x00 };
    o_DoFile = (DoFile_t)Detour((BYTE*)0x00432620, doFileProlog, 7, (void*)h_DoFile);
    {   // replace ChangeSettings (0x44D9D0) entirely: "call 0x42F160 / mov ecx,[eax+70h]"
        static const BYTE expect[8] = { 0xE8, 0x8B, 0x17, 0xFE, 0xFF, 0x8B, 0x48, 0x70 };
        BYTE* t = (BYTE*)0x0044D9D0;
        if (!memcmp(t, expect, 8)) {
            DWORD old; VirtualProtect(t, 5, PAGE_EXECUTE_READWRITE, &old);
            t[0] = 0xE9; *(DWORD*)(t + 1) = (DWORD)(void*)h_ChangeSettings - (DWORD)(t + 5);
            VirtualProtect(t, 5, old, &old); FlushInstructionCache(GetCurrentProcess(), t, 5);
            LOG("ChangeSettings replaced");
        } else LOG("ChangeSettings: unexpected bytes, not replaced");
    }
}
BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) { DisableThreadLibraryCalls(h); Init(); }
    if (reason == DLL_PROCESS_DETACH && g_log) { LogGuardHits(); LOG("process exit, frames=%lu", g_frames); fclose(g_log); g_log = nullptr; }
    return TRUE;
}
