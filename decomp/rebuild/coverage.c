/* Coverage of the new code (build.py --coverage): every function compiled from rebuild/src and the generated code
 * calls __cyg_profile_func_enter_bare first (clang -finstrument-function-entry-bare); its return address, a point
 * just inside that function, marks the function as run. The marks are written next to the game to
 * decomp_coverage_<first tick>_<process id>.bin (one file per run of the game; one dword per marked point, image
 * addresses) at most every 2 s while new ones appear, so a game that is killed or crashes keeps what it ran up to
 * then. tools/coverage.py maps the points to functions through the
 * build's .map. This file itself is compiled without the hook. */
#include <windows.h>

extern char __ImageBase;
static unsigned char cov[1 << 22];          /* (address - image base) / 4: 16 MB of image */
static unsigned int calls, dirty, last;
static char name[64];

static void dump(void)
{
    static unsigned int buf[4096];
    unsigned int i, n = 0, base = (unsigned int)&__ImageBase;
    DWORD w;
    HANDLE f;
    if (!name[0])
        wsprintfA(name, "decomp_coverage_%08x_%08x.bin", GetTickCount(), GetCurrentProcessId());
    f = CreateFileA(name, GENERIC_WRITE, FILE_SHARE_READ, 0, CREATE_ALWAYS, 0, 0);
    if (f == INVALID_HANDLE_VALUE)
        return;
    for (i = 0; i < sizeof cov; i++) {
        if (!cov[i])
            continue;
        buf[n++] = base + i * 4;
        if (n == sizeof buf / sizeof buf[0]) {
            WriteFile(f, buf, n * 4, &w, 0);
            n = 0;
        }
    }
    if (n)
        WriteFile(f, buf, n * 4, &w, 0);
    CloseHandle(f);
}

void __cdecl __cyg_profile_func_enter_bare(void)
{
    unsigned int o = ((unsigned int)__builtin_return_address(0) - (unsigned int)&__ImageBase) >> 2;
    if (o < sizeof cov && !cov[o]) {
        cov[o] = 1;
        dirty = 1;
    }
    if (!(++calls & 0xffff) && dirty) {
        unsigned int t = GetTickCount();
        if (t - last >= 2000) {
            last = t;
            dirty = 0;
            dump();
        }
    }
}
