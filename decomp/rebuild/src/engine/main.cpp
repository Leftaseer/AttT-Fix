/* Start-up, the error log, the window procedure: Engine.cpp / main.cpp of the original (AttT 0x42E770..0x42FB50). */
#include "game/common.h"
#include "game/globals.h"
#include "game/engine.h"
#include <tlhelp32.h>

/* ---------------------------------------------------------------------------------------------------------------
 * CGameException: the message, then "\n---in file - '<file>'\n---line = <line>" when a file is given. */

ORIG_FN(0042EEC0, int, (char *buf, unsigned size, const char *fmt, ...));       /* snprintf with truncation */

DECOMP(00421220)
CGameException::CGameException(const std::string &msg, const char *file, int line)
    : text(msg)
{
    if (file) {
        char where[512];
        ORIG_CALL(0042EEC0)(where, sizeof(where), "\n---in file - '%s'\n---line = %d", file, line);
        text += where;
    }
#ifdef DECOMP_DEBUG_LOG
    /* every engine error, also the ones caught and handled: WINEDEBUG=+debugstr or DebugView shows them, and
     * decomp_debug.log next to the exe keeps them */
    OutputDebugStringA(text.raw());
    DebugLog(text.raw());
#endif
}

#ifdef DECOMP_DEBUG_LOG
/* decomp_debug.log next to the exe (the game's current folder may be another one) */
void DebugLog(const char *text)
{
    static char path[MAX_PATH];
    if (!path[0]) {
        GetModuleFileNameA(nullptr, path, MAX_PATH - 20);
        char *slash = path;
        for (char *p = path; *p; p++)
            if (*p == '\\' || *p == '/')
                slash = p + 1;
        lstrcpyA(slash, "decomp_debug.log");
    }
    if (FILE *f = fopen(path, "a")) {
        fwrite(text, 1, strlen(text), f);
        fwrite("\n", 1, 1, f);
        fclose(f);
    }
}

/* A crash (access violation, bad instruction, division by zero, stack overflow) is logged with the registers and
 * every stack value that points into code: the return addresses of the calls that led there, most recent first
 * (tools/crashlog.py names them from ATThrone.map).  The game's own handler (WinMain's __except) runs after. */
static LONG CALLBACK CrashLog(EXCEPTION_POINTERS *e)
{
    static int logged;
    DWORD code = e->ExceptionRecord->ExceptionCode;
    bool cxx = code == 0xE06D7363;           /* a C++ throw: logged too, with the type thrown (it may be caught) */
    if (!cxx && code != EXCEPTION_ACCESS_VIOLATION && code != EXCEPTION_ILLEGAL_INSTRUCTION &&
        code != EXCEPTION_PRIV_INSTRUCTION && code != EXCEPTION_INT_DIVIDE_BY_ZERO && code != EXCEPTION_STACK_OVERFLOW)
        return EXCEPTION_CONTINUE_SEARCH;
    if (logged++ >= 6)
        return EXCEPTION_CONTINUE_SEARCH;
    CONTEXT *c = e->ContextRecord;
    char line[256];
    if (cxx && e->ExceptionRecord->NumberParameters >= 3) {
        /* ThrowInfo -> CatchableTypeArray -> first CatchableType -> TypeDescriptor (name at +8) */
        const DWORD *ti = (const DWORD *)e->ExceptionRecord->ExceptionInformation[2];
        const char *name = "?";
        if (ti && !IsBadReadPtr(ti, 16)) {
            const DWORD *cta = (const DWORD *)ti[3];
            if (cta && !IsBadReadPtr(cta, 8) && cta[0]) {
                const DWORD *ct = (const DWORD *)cta[1];
                if (ct && !IsBadReadPtr(ct, 8) && !IsBadReadPtr((void *)(ct[1] + 8), 4))
                    name = (const char *)(ct[1] + 8);
            }
        }
        wsprintfA(line, "C++ exception %.120s", name);
        DebugLog(line);
    }
    wsprintfA(line, "crash %08X at %08X (address %08X)", code, (DWORD)e->ExceptionRecord->ExceptionAddress,
              e->ExceptionRecord->NumberParameters > 1 ? (DWORD)e->ExceptionRecord->ExceptionInformation[1] : 0);
    DebugLog(line);
    wsprintfA(line, "  eax %08X ebx %08X ecx %08X edx %08X esi %08X edi %08X ebp %08X esp %08X", c->Eax, c->Ebx,
              c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    DebugLog(line);
    {   /* the top of the stack as it is: after a call into nowhere the return address is the first */
        DWORD *top = (DWORD *)c->Esp;
        if (!IsBadReadPtr(top - 12, 48)) {
            wsprintfA(line, "  below esp: %08X %08X %08X %08X %08X %08X %08X %08X %08X %08X %08X %08X", top[-12],
                      top[-11], top[-10], top[-9], top[-8], top[-7], top[-6], top[-5], top[-4], top[-3], top[-2], top[-1]);
            DebugLog(line);
        }
        if (!IsBadReadPtr(top, 32)) {
            wsprintfA(line, "  esp: %08X %08X %08X %08X %08X %08X %08X %08X", top[0], top[1], top[2], top[3], top[4],
                      top[5], top[6], top[7]);
            DebugLog(line);
        }
    }
    HMODULE exe = GetModuleHandleA(nullptr);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    DWORD lo = (DWORD)exe + 0x1000, hi = (DWORD)exe + nt->OptionalHeader.SizeOfImage;
    DWORD *sp = (DWORD *)c->Esp;
    int n = 0;
    char *out = line + lstrlenA(lstrcpyA(line, "  stack:"));
    for (int i = 0; i < 2048 && n < 48; i++) {
        DWORD v;
        if (IsBadReadPtr(sp + i, 4))
            break;
        v = sp[i];
        if (v < lo || v >= hi)
            continue;
        /* a return address: the bytes before it are a call (E8 rel32, FF /2) */
        const unsigned char *b = (const unsigned char *)v;
        if (IsBadReadPtr(b - 6, 6) || !(b[-5] == 0xE8 || b[-2] == 0xFF || b[-3] == 0xFF || b[-6] == 0xFF))
            continue;
        out += wsprintfA(out, " %08X", v);
        if (++n % 8 == 0) {
            DebugLog(line);
            out = line + lstrlenA(lstrcpyA(line, "  stack:"));
        }
    }
    if (n % 8)
        DebugLog(line);
    return EXCEPTION_CONTINUE_SEARCH;
}
#endif

ORIG_DATA(0069916C);  /* _ThrowInfo of CGameException */
ORIG_DATA(00607BC8);
ORIG_DATA(00607E98);

void ThrowGameException(const char *msg, const char *file, int line)
{
    CGameException e(std::string(msg), file, line);
    _CxxThrowException(&e, d_0069916C);
    __builtin_unreachable();
}

/* ---------------------------------------------------------------------------------------------------------------
 * Only one copy of the game may run: counts the processes whose main module name contains "ATThrone" and ".exe". */

DECOMP(0042E770)
int IsOnlyInstance()
{
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE)
        return 0;
    PROCESSENTRY32 pe;
    pe.dwSize = sizeof(pe);
    if (!Process32First(snap, &pe)) {
        CloseHandle(snap);
        return 0;
    }
    int count = 0;
    do {
        if (pe.th32ParentProcessID == 0)
            continue;
        HANDLE mods = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pe.th32ProcessID);
        if (mods == INVALID_HANDLE_VALUE)
            continue;
        MODULEENTRY32 me;
        me.dwSize = sizeof(me);
        if (!Module32First(mods, &me)) {
            CloseHandle(mods);
            break;
        }
        CloseHandle(mods);
        char name[MAX_PATH];
        lstrcpyA(name, me.szModule);
        std::string s(name);
        if (s.find("ATThrone", 0) != std::string::npos && s.find(".exe", 0) != std::string::npos)
            ++count;
    } while (Process32Next(snap, &pe));
    CloseHandle(snap);
    return count <= 1;
}

/* ---------------------------------------------------------------------------------------------------------------
 * __ATThrone__ERRORS__<day>_<month>_<year>.log in the game folder: every message is appended to it. */


static void AppendErrorLog(const char *text, size_t len)
{
    SYSTEMTIME t;
    GetLocalTime(&t);
    char name[1024];
    sprintf(name, "__ATThrone__ERRORS__%u_%u_%u.log", t.wDay, t.wMonth, t.wYear);
    /* the original opens a std::ofstream with ios::app (text mode) */
    if (FILE *f = fopen(name, "a")) {
        fwrite(text, 1, len, f);
        fclose(f);
    }
}

DECOMP(0042E930)
void WriteErrorLog(const char *text)
{
    AppendErrorLog(text, strlen(text));
}

/* Shows "Failed with error at address <addr>. Status message: <code>: <text of the NTSTATUS>" and logs it. */
DECOMP(0042EA90)
void ReportException(DWORD code, void *address)
{
    HMODULE ntdll = LoadLibraryA("NTDLL.DLL");
    char *status = nullptr;
    FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_FROM_HMODULE,
                   ntdll, code, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (char *)&status, 0, nullptr);
    char text[1024];
    wsprintfA(text, "Failed with error at address %X. Status message: %d: %s", address, code, status);
    WriteErrorLog(text);
    MessageBoxA(nullptr, text, "Error", MB_OK);
    LocalFree(status);
    FreeLibrary(ntdll);
}

/* ---------------------------------------------------------------------------------------------------------------
 * Singletons created at start-up and destroyed at exit. */

ORIG_THISCALL(0042ED10, void *, (void *self));                                 /* nCfg::GamePath::GamePath */
ORIG_THISCALL(0044A930, CEngine *, (void *self));                              /* CEngine::CEngine */

DECOMP(0042F100)
void CreateGamePath()
{
    void *p = operator new(0x3C);
    g_gamePath = p ? ORIG_CALL(0042ED10)(p) : nullptr;
}

DECOMP(0042F160)
CEngine *CEngine::Instance()
{
    if (!g_engineInstance) {
        void *p = operator new(sizeof(CEngine));
        g_engineInstance = p ? ORIG_CALL(0044A930)(p) : nullptr;
        if (!g_engineInstance)
            ThrowGameException(ORIG_STR(00607BC8), ORIG_STR(00607E98), 16);   /* "Ошибка при создании m_instance
                                                                                  в CSingleton", "e:\\prog\\att1\\singleton.h" */
    }
    return g_engineInstance;
}

struct CDeletable { virtual void Release(int flags); };    /* slot 0 = scalar deleting destructor */

DECOMP(0042EFF0)
void DestroySingletons()
{
    if (g_engineInstance) {
        ((CDeletable *)g_engineInstance)->Release(1);
        g_engineInstance = nullptr;
    }
    g_engine = nullptr;
    if (g_configInstance) {
        ((CDeletable *)g_configInstance)->Release(1);
        g_configInstance = nullptr;
    }
    g_config = nullptr;
    if (g_gamePath) {
        ((CDeletable *)g_gamePath)->Release(1);
        g_gamePath = nullptr;
    }
}

/* ---------------------------------------------------------------------------------------------------------------
 * The window procedure: the engine (current scene) sees the messages first. */

DECOMP(0042EB70)
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (g_wndProcBypass)
        return DefWindowProcW(hwnd, msg, wp, lp);
    if (g_engine && g_engine->HandleMessage(hwnd, msg, wp, lp))
        return 0;
    if (msg == WM_DESTROY) {
        PostQuitMessage(0);
        return 0;
    }
    if (msg == WM_ACTIVATEAPP) {
        g_appActive = wp != 0;
        if (g_appActive) {
            /* keep the cursor inside the window while the game is active */
            SetCursor(nullptr);
            RECT r;
            GetWindowRect(g_hWnd, &r);
            ClipCursor(&r);
        } else {
            ClipCursor(nullptr);
        }
        if (g_engine)
            g_engine->SetActive(g_appActive);
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

/* ---------------------------------------------------------------------------------------------------------------
 * GameMain(lpCmdLine): runs inside WinMain's __try (0x42F9B0).  Creates the window and the engine, then pumps
 * messages; while the window is inactive it waits in GetMessage, otherwise every idle turn runs CEngine::Step. */

#include "game/config.h"

DECOMP(0042F640)
void GameMain(const char *cmdLine)
{
    if (!IsOnlyInstance())
        return;
#ifdef DECOMP_TRACE_ICALLS
    StartICallTrace();      /* icalltrace.cpp: what indirect callees pop, measured */
#endif
#ifdef DECOMP_DEBUG_LOG
    AddVectoredExceptionHandler(1, CrashLog);
    {   /* when, and which build (its compile time; the exe keeps the original's time stamp): the logs of several
         * runs and versions pile up in one file */
        SYSTEMTIME t;
        GetLocalTime(&t);
        char line[96];
        wsprintfA(line, "---- start %04d-%02d-%02d %02d:%02d:%02d, build %s %s", t.wYear, t.wMonth, t.wDay, t.wHour,
                  t.wMinute, t.wSecond, __DATE__, __TIME__);
        DebugLog(line);
    }
#endif
    CreateGamePath();
    std::string dir = ((nCfg::GamePath *)g_gamePath)->exePath;
    dir = dir.substr(0, dir.rfind("\\", std::string::npos));
    dir += "\\";
    std::string saves = dir + "Saves/";
    CreateDirectoryA(saves.c_str(), nullptr);

    g_console = CConsole::Instance();
    ((CConsole *)g_console)->OpenLog(std::string("game.log"));
    g_config = CConfig::Instance();
    g_config->LoadGraphicCfg(std::string("game.cfg"));

    CConfig *cfg = g_config;
    g_hWnd = CreateWindowExW(0, L"ATThrone", L"ATThrone", 0x90000008 /* WS_POPUP | WS_VISIBLE | 8 */,
                             cfg->x, cfg->y, cfg->width, cfg->height, GetDesktopWindow(), nullptr,
                             GetModuleHandleA(nullptr), nullptr);
    g_engine = CEngine::Instance();
    g_engine->Init(std::string(cmdLine));
    g_engine->SetActive(g_appActive);

    HACCEL accel = LoadAcceleratorsA(GetModuleHandleA(nullptr), MAKEINTRESOURCEA(101));
    ShowWindow(g_hWnd, SW_SHOWDEFAULT);
    UpdateWindow(g_hWnd);
    RECT r;
    GetWindowRect(g_hWnd, &r);
    ClipCursor(&r);
    g_engine->ApplyGamma();

    MSG msg;
    for (;;) {
        if (GetKeyState(VK_CONTROL) < 0)
            GetKeyState(VK_HOME);            /* leftover of a debug shortcut, the result is not used */
        if (!g_appActive) {
#ifdef DECOMP_TEST_INPUT
            OutputDebugStringA("main loop: inactive, waiting for messages");
#endif
            if (!GetMessageA(&msg, nullptr, 0, 0))
                break;
        } else if (PeekMessageA(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT)
                break;
        } else {
#ifdef DECOMP_TEST_INPUT
            TestInput(CInput::Instance());
#endif
            if (!g_engine->Step())
                break;
            continue;
        }
        if (!TranslateAcceleratorA(msg.hwnd, accel, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageA(&msg);
        }
    }
    DestroySingletons();
}
