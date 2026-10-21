/* Measuring what indirect callees pop, in a running game (build.py -D DECOMP_TRACE_ICALLS, for the tests): the
 * machine code alone does not tell for many virtual calls (a frame pointer restores ESP, so its balance says
 * nothing).  decomp_trace_sites.txt next to the exe lists 'ADDRESS LENGTH' of such call instructions
 * (tools/icalls.py's unsolved ones); each gets an int3.  At the call: ESP is noted, the call instruction put back
 * for one step (the trap flag re-arms it), and its return address gets an int3; there ESP minus the noted ESP is
 * the bytes the callee popped.  A site seen three times alike is written to decomp_trace_out.txt and left alone.
 * Only for test machines: the code is patched at run time. */
#include "game/common.h"

#ifdef DECOMP_TRACE_ICALLS

namespace {
const int SITES = 8192, PENDING = 512;
struct Site { DWORD addr, len; unsigned char orig, ret_orig; int seen, pop; bool done, ret_armed; };
Site g_sites[SITES];
int g_count;
struct Pending { int site; DWORD esp; };
Pending g_pending[PENDING];
int g_npending;
DWORD g_rearm;              /* an int3 to put back after the step over its instruction */
char g_out[MAX_PATH];

int FindSite(DWORD a)
{
    int lo = 0, hi = g_count;           /* sorted by address */
    while (lo < hi) {
        int m = (lo + hi) / 2;
        if (g_sites[m].addr < a) lo = m + 1; else hi = m;
    }
    return lo < g_count && g_sites[lo].addr == a ? lo : -1;
}

int FindReturn(DWORD a)
{
    /* the latest pending call whose return address this is (recursion: LIFO) */
    for (int k = g_npending - 1; k >= 0; k--) {
        const Site &s = g_sites[g_pending[k].site];
        if (s.addr + s.len == a)
            return k;
    }
    return -1;
}

void Poke(DWORD a, unsigned char b) { *(volatile unsigned char *)a = b; }

LONG CALLBACK Trace(EXCEPTION_POINTERS *e)
{
    CONTEXT *c = e->ContextRecord;
    DWORD code = e->ExceptionRecord->ExceptionCode, at = (DWORD)e->ExceptionRecord->ExceptionAddress;
    if (code == EXCEPTION_SINGLE_STEP) {
        if (!g_rearm)
            return EXCEPTION_CONTINUE_SEARCH;
        Poke(g_rearm, 0xCC);
        g_rearm = 0;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (code != EXCEPTION_BREAKPOINT)
        return EXCEPTION_CONTINUE_SEARCH;
    int s = FindSite(at);
    if (s >= 0 && !g_sites[s].done && *(unsigned char *)at == 0xCC) {
        Site &x = g_sites[s];
        if (g_npending < PENDING)
            g_pending[g_npending++] = { s, c->Esp };
        Poke(at, x.orig);
        DWORD r = x.addr + x.len;
        if (!x.ret_armed) {
            x.ret_orig = *(unsigned char *)r;
            x.ret_armed = true;
        }
        Poke(r, 0xCC);
        c->Eip = at;
        c->EFlags |= 0x100;
        g_rearm = at;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    int k = FindReturn(at);
    if (k >= 0) {
        Site &x = g_sites[g_pending[k].site];
        int pop = (int)(c->Esp - g_pending[k].esp);
        g_npending = k;                      /* this one and any left by an exception thrown through */
        Poke(at, x.ret_orig);
        c->Eip = at;
        if (x.seen == 0 || x.pop == pop) x.seen++; else x.seen = -1000;   /* disagreeing: never written */
        x.pop = pop;
        if (x.seen >= 3 && !x.done) {
            x.done = true;
            Poke(x.addr, x.orig);
            if (FILE *f = fopen(g_out, "a")) {
                char line[32];
                fwrite(line, 1, sprintf(line, "%08X\t%d\n", (unsigned)x.addr, pop), f);
                fclose(f);
            }
        } else if (!x.done) {
            c->EFlags |= 0x100;              /* keep the return address armed for the next call */
            g_rearm = at;
        }
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    /* an armed return address reached some other way (a jump to it): step over it and arm it again */
    for (int i = 0; i < g_count; i++) {
        Site &x = g_sites[i];
        if (x.ret_armed && x.addr + x.len == at && *(unsigned char *)at == 0xCC) {
            Poke(at, x.ret_orig);
            c->Eip = at;
            if (!x.done) {
                c->EFlags |= 0x100;
                g_rearm = at;
            }
            return EXCEPTION_CONTINUE_EXECUTION;
        }
    }
    return EXCEPTION_CONTINUE_SEARCH;
}
}

void StartICallTrace()
{
    char path[MAX_PATH];
    GetModuleFileNameA(nullptr, path, MAX_PATH - 32);
    char *slash = path;
    for (char *p = path; *p; p++)
        if (*p == '\\' || *p == '/') slash = p + 1;
    lstrcpyA(slash, "decomp_trace_out.txt");
    lstrcpyA(g_out, path);
    lstrcpyA(slash, "decomp_trace_sites.txt");
    FILE *f = fopen(path, "r");
    if (!f)
        return;
    unsigned a, n;
    char line[64];
    while (g_count < SITES && fgets(line, sizeof(line), f))
        if (sscanf(line, "%x %u", &a, &n) == 2)
            g_sites[g_count++] = { a, n, 0, 0, 0, 0, false, false };
    fclose(f);
    HMODULE exe = GetModuleHandleA(nullptr);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    DWORD old;
    VirtualProtect((char *)exe + 0x1000, nt->OptionalHeader.SizeOfImage - 0x1000, PAGE_EXECUTE_READWRITE, &old);
    AddVectoredExceptionHandler(1, Trace);
    for (int k = 0; k < g_count; k++) {
        g_sites[k].orig = *(unsigned char *)g_sites[k].addr;
        Poke(g_sites[k].addr, 0xCC);
    }
}
#endif
