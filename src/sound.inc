// ---------------------------------------------------------------- 8) 3D sound on a worker thread (1.1.1)
// Included into attfix.cpp after cpuopt.inc.
//
// DirectSound is emulated in software on modern Windows: IDirectSound3DListener::CommitDeferredSettings
// (0x4C18F0, even at ListenerHz=60) and IDirectSound3DBuffer::SetPosition with DS3D_IMMEDIATE (0x4C2E10, every
// sound source on its update) recalculate the 3D mix and wait for the mixer's lock: ~13% of the game thread in a
// battle (profile "system time from"). These calls return nothing the game uses, so they are queued here and
// executed by a worker thread, normally within a millisecond (immediate positions wake it right away, the
// commit is coalesced). Each queued interface holds a reference until the worker is done with it.
static int g_asyncSnd = 1;                      // [Perf] AsyncSound; Ctrl+4 with the other optimizations
static DWORD g_sndPos = 0, g_sndCoalesced = 0, g_sndCommits = 0, g_sndSync = 0, g_sndWake = 0;
struct SndCmd { void* buf; float v[3]; DWORD apply; };
enum { SND_Q = 512 };
static SndCmd g_sndQ[SND_Q]; static int g_sndN = 0;
static void* g_sndListener = nullptr;           // referenced listener for pending listener commands / commit
static bool g_sndLPos = false, g_sndLOri = false, g_sndCommit = false;
static float g_sndLp[3], g_sndLo[6]; static DWORD g_sndLpA = 1, g_sndLoA = 1;
static CRITICAL_SECTION g_sndCs; static HANDLE g_sndEv = nullptr; static volatile LONG g_sndRun = 0; static HANDLE g_sndThread = nullptr;
typedef ULONG (__stdcall *SndRef_t)(void*);
typedef HRESULT (__stdcall *SndPos_t)(void*, float, float, float, DWORD);
typedef HRESULT (__stdcall *SndOri_t)(void*, float, float, float, float, float, float, DWORD);
typedef HRESULT (__stdcall *SndCommit_t)(void*);
static inline void SndAddRef(void* p) { ((SndRef_t)(*(void***)p)[1])(p); }
static inline void* SndListenerRef(void* l) {   // keep one reference to the listener while commands for it are pending
    if (g_sndListener != l) { if (g_sndListener) ComRelease(g_sndListener); g_sndListener = l; if (l) SndAddRef(l); }
    return l;
}
static DWORD WINAPI SndThread(void*) {
    static SndCmd q[SND_Q];
    while (g_sndRun) {
        WaitForSingleObject(g_sndEv, 50);
        EnterCriticalSection(&g_sndCs);
        int n = g_sndN; memcpy(q, g_sndQ, n * sizeof(SndCmd)); g_sndN = 0;
        void* l = g_sndListener; g_sndListener = nullptr;
        bool lp = g_sndLPos, lo = g_sndLOri, cm = g_sndCommit; g_sndLPos = g_sndLOri = g_sndCommit = false;
        float p[3], o[6]; memcpy(p, g_sndLp, sizeof p); memcpy(o, g_sndLo, sizeof o); DWORD pa = g_sndLpA, oa = g_sndLoA;
        LeaveCriticalSection(&g_sndCs);
        for (int i = 0; i < n; ++i) {
            void* b = q[i].buf;
            ((SndPos_t)(*(void***)b)[19])(b, q[i].v[0], q[i].v[1], q[i].v[2], q[i].apply);   // IDirectSound3DBuffer::SetPosition
            ComRelease(b);
        }
        if (l) {
            if (lp) ((SndPos_t)(*(void***)l)[14])(l, p[0], p[1], p[2], pa);                     // listener SetPosition
            if (lo) ((SndOri_t)(*(void***)l)[13])(l, o[0], o[1], o[2], o[3], o[4], o[5], oa);   // listener SetOrientation
            if (cm) ((SndCommit_t)(*(void***)l)[17])(l);                                         // CommitDeferredSettings
            ComRelease(l);
        }
    }
    return 0;
}
static bool SndAsync() { return g_asyncSnd && g_sndRun; }
// 0x4C2E10 CSound::SetPosition(const float* pos, bool deferred)  (thiscall, ret 8)
static void __fastcall h_SndSetPos(BYTE* s, void*, const float* pos, char deferred) {
    if (!s[8]) return;                              // not loaded: the original does nothing either
    void* b = *(void**)(s + 0x60);
    DWORD apply = deferred ? 1 : 0;                 // DS3D_DEFERRED : DS3D_IMMEDIATE
    if (!b) return;
    if (!SndAsync()) { ((SndPos_t)(*(void***)b)[19])(b, pos[0], pos[1], pos[2], apply); return; }
    bool wake = false;
    EnterCriticalSection(&g_sndCs);
    int i = 0; for (; i < g_sndN; ++i) if (g_sndQ[i].buf == b) break;
    if (i < g_sndN) { memcpy(g_sndQ[i].v, pos, 12); g_sndQ[i].apply &= apply; ++g_sndCoalesced; }
    else if (g_sndN < SND_Q) { SndCmd& c = g_sndQ[g_sndN++]; c.buf = b; SndAddRef(b); memcpy(c.v, pos, 12); c.apply = apply; }
    else i = -1;
    if (i >= 0) { ++g_sndPos; wake = !apply; }
    LeaveCriticalSection(&g_sndCs);
    if (i < 0) { ++g_sndSync; ((SndPos_t)(*(void***)b)[19])(b, pos[0], pos[1], pos[2], apply); return; }
    if (wake) { ++g_sndWake; SetEvent(g_sndEv); }
}
// 0x4C19A0 listener SetPosition(const float* pos, bool deferred)  (cdecl)
static void __cdecl h_SndListenerPos(const float* pos, char deferred) {
    void* l = *(void**)0x006CA4AC; if (!l) return;
    if (!SndAsync()) { ((SndPos_t)(*(void***)l)[14])(l, pos[0], pos[1], pos[2], deferred ? 1 : 0); return; }
    EnterCriticalSection(&g_sndCs);
    SndListenerRef(l); memcpy(g_sndLp, pos, 12); g_sndLpA = deferred ? 1 : 0; g_sndLPos = true;
    LeaveCriticalSection(&g_sndCs);
    if (!deferred) SetEvent(g_sndEv);
}
// 0x4C1AA0 listener SetOrientation(const float* front, const float* top, bool deferred)  (cdecl)
static void __cdecl h_SndListenerOri(const float* f, const float* t, char deferred) {
    void* l = *(void**)0x006CA4AC; if (!l) return;
    if (!SndAsync()) { ((SndOri_t)(*(void***)l)[13])(l, f[0], f[1], f[2], t[0], t[1], t[2], deferred ? 1 : 0); return; }
    EnterCriticalSection(&g_sndCs);
    SndListenerRef(l); memcpy(g_sndLo, f, 12); memcpy(g_sndLo + 3, t, 12); g_sndLoA = deferred ? 1 : 0; g_sndLOri = true;
    LeaveCriticalSection(&g_sndCs);
    if (!deferred) SetEvent(g_sndEv);
}
// 0x4C18F0 listener CommitDeferredSettings (+ a once-per-second GetCaps on an uninitialized struct, dropped)
static void __cdecl h_SndCommit() {
    void* l = *(void**)0x006CA4AC; if (!l) return;
    if (!SndAsync()) { ((SndCommit_t)(*(void***)l)[17])(l); return; }
    EnterCriticalSection(&g_sndCs);
    SndListenerRef(l); g_sndCommit = true;
    LeaveCriticalSection(&g_sndCs);
    ++g_sndCommits; SetEvent(g_sndEv);
}
static void SndStop() {                         // process exit: let the worker finish what is queued, then stop it
    if (!g_sndRun) return;
    g_asyncSnd = 0; SetEvent(g_sndEv); Sleep(5);
    g_sndRun = 0; SetEvent(g_sndEv);
    if (g_sndThread) WaitForSingleObject(g_sndThread, 300);
}
static void InstallAsyncSound() {
    struct { DWORD at; const char* b; int n; void* fn; } p[4] = {
        { 0x004C18F0, "\xA1\xAC\xA4\x6C\x00\x83\xEC\x60", 8, (void*)h_SndCommit },
        { 0x004C19A0, "\x8B\x0D\xAC\xA4\x6C\x00\x85\xC9", 8, (void*)h_SndListenerPos },
        { 0x004C1AA0, "\x8B\x0D\xAC\xA4\x6C\x00\x85\xC9", 8, (void*)h_SndListenerOri },
        { 0x004C2E10, "\x56\x8B\xF1\x80\x7E\x08\x00\x74\x34\xE8", 10, (void*)h_SndSetPos },
    };
    for (auto& e : p) if (memcmp((void*)e.at, e.b, e.n)) { g_asyncSnd = 0; LOG("async sound: unexpected code at %08lX, not installed", e.at); return; }
    if (memcmp((void*)0x004C2E1E, "\x8B\x46\x60\x8B\x10\x8B\x52\x4C", 8) || memcmp((void*)0x004C18FC, "\x8B\x08\x8B\x51\x44", 5)) {
        g_asyncSnd = 0; LOG("async sound: unexpected vtable use, not installed"); return;
    }
    InitializeCriticalSection(&g_sndCs);
    g_sndEv = CreateEventA(nullptr, FALSE, FALSE, nullptr);
    g_sndRun = 1;
    g_sndThread = CreateThread(nullptr, 0, SndThread, nullptr, 0, nullptr);
    if (!g_sndThread) { g_sndRun = 0; g_asyncSnd = 0; LOG("async sound: thread creation failed"); return; }
    SetThreadPriority(g_sndThread, THREAD_PRIORITY_ABOVE_NORMAL);
    for (auto& e : p) { BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)e.fn - (e.at + 5); PatchBytes((void*)e.at, j, 5); }
    LOG("async sound: 3D positions and commits on a worker thread (AsyncSound=%d)", g_asyncSnd);
}
static void SoundStats() {
    if (!g_sndRun) return;
    PLOG("SOUND async=%d: positions queued=%lu (coalesced %lu, immediate wakes %lu, sync %lu) commits=%lu", g_asyncSnd, g_sndPos, g_sndCoalesced, g_sndWake, g_sndSync, g_sndCommits);
    g_sndPos = g_sndCoalesced = g_sndWake = g_sndSync = g_sndCommits = 0;
}
