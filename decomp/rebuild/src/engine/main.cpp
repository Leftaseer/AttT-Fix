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
}

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
