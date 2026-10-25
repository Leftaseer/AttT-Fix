/* A sampling profiler for builds made with -D DECOMP_PROFILE -D DECOMP_DEBUG_LOG: a thread stops the main thread
 * every millisecond and counts where it was, in the exe: the instruction itself, or, inside a DLL, the first
 * return address into the exe on its stack.  Every 10 seconds the 40 most frequent addresses of that period go to
 * decomp_debug.log ("profile" lines; tools/crashlog.py names them from ATThrone.map). */
#include "game/common.h"
#include "game/engine.h"

#ifdef DECOMP_PROFILE
static const int SLOTS = 1 << 16;
static DWORD g_addr[SLOTS], g_count[SLOTS];

static void Count(DWORD a)
{
    for (DWORD h = (a * 2654435761u) >> 16;; h = (h + 1) & (SLOTS - 1)) {
        if (g_addr[h] == a || !g_addr[h]) {
            g_addr[h] = a;
            g_count[h]++;
            return;
        }
    }
}

static void Report(int samples)
{
    char line[1024];
    wsprintfA(line, "profile: %d samples", samples);
    DebugLog(line);
    for (int k = 0; k < 40; k++) {
        int best = -1;
        for (int i = 0; i < SLOTS; i++)
            if (g_count[i] && (best < 0 || g_count[i] > g_count[best]))
                best = i;
        if (best < 0)
            break;
        wsprintfA(line, "profile %08X %d", g_addr[best], g_count[best]);
        DebugLog(line);
        g_count[best] = 0;
    }
    memset(g_addr, 0, sizeof(g_addr));
    memset(g_count, 0, sizeof(g_count));
}

static DWORD WINAPI Sampler(void *mainThread)
{
    HMODULE exe = GetModuleHandleA(nullptr);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    DWORD lo = (DWORD)exe + 0x1000, hi = (DWORD)exe + nt->OptionalHeader.SizeOfImage;
    DWORD next = GetTickCount() + 10000;
    int samples = 0;
    for (;;) {
        Sleep(1);
        if (SuspendThread(mainThread) == (DWORD)-1)
            return 0;
        CONTEXT c;
        c.ContextFlags = CONTEXT_CONTROL;
        if (GetThreadContext(mainThread, &c)) {
            DWORD a = c.Eip;
            if (a < lo || a >= hi) {
                a = 0;
                const DWORD *sp = (const DWORD *)c.Esp;
                for (int i = 0; i < 1024 && !IsBadReadPtr(sp + i, 4); i++)
                    if (sp[i] >= lo && sp[i] < hi) {
                        a = sp[i];
                        break;
                    }
            }
            Count(a);
            samples++;
        }
        ResumeThread(mainThread);
        if ((int)(GetTickCount() - next) >= 0) {
            Report(samples);
            samples = 0;
            next = GetTickCount() + 10000;
        }
    }
}

void StartProfiler()
{
    HANDLE self;
    DuplicateHandle(GetCurrentProcess(), GetCurrentThread(), GetCurrentProcess(), &self, 0, FALSE,
                    DUPLICATE_SAME_ACCESS);
    CloseHandle(CreateThread(nullptr, 0, Sampler, self, 0, nullptr));
}
#endif
