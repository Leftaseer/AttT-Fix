/* Replacements switched at start-up (build.py --toggle), for finding a bad replaced function by bisection without
 * a new build each time.  The entry of every replaced function jumps through a slot (data, tools/exe2obj.py
 * --toggle) holding the new function; for one that decomp_toggle.txt next to the exe turns off, the slot gets the
 * old entry's first instructions copied out with a jump back, before the game's own start-up code runs.  No code
 * is written.  The pointers to replaced functions (vtables, tables) keep pointing at the old entries, so they
 * follow the switch.
 *
 * decomp_toggle.txt: one rule per line, applied in order to every replaced function, all on before the first:
 *     - 00500000-00607000      off: the replaced functions whose original address is in the range
 *     + 0051BB20               on:  one function (a single address)
 * anything else (comments) is ignored.  decomp_toggle.log next to it says how many are on.
 * Runs before the C runtime is set up: only kernel32. */
#include <windows.h>

/* [0] count, then (original address, copy of its first instructions or 0 when it cannot be switched off) pairs,
 * then the slots: made by tools/exe2obj.py --toggle */
#define TOGGLE_MAX 16384
extern unsigned decomp_toggle_table[];
static unsigned char on[TOGGLE_MAX];

static int hexval(const char **p, unsigned *v)
{
    int n = 0;
    *v = 0;
    for (;; (*p)++, n++) {
        char c = **p;
        unsigned d = c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 :
                     c >= 'A' && c <= 'F' ? c - 'A' + 10 : 16;
        if (d == 16)
            return n;
        *v = *v * 16 + d;
    }
}

static void path_next_to_exe(char *path, const char *name)
{
    GetModuleFileNameA(0, path, MAX_PATH - 32);
    char *slash = path;
    for (char *p = path; *p; p++)
        if (*p == '\\' || *p == '/')
            slash = p + 1;
    lstrcpyA(slash, name);
}

void decomp_apply_toggles(void)
{
    unsigned count = decomp_toggle_table[0];
    unsigned *e = decomp_toggle_table + 1;
    if (count > TOGGLE_MAX)
        return;
    for (unsigned i = 0; i < count; i++)
        on[i] = 1;
    static char buf[262144];
    char path[MAX_PATH];
    DWORD got = 0;
    path_next_to_exe(path, "decomp_toggle.txt");
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, 0, 0);
    if (f != INVALID_HANDLE_VALUE) {
        ReadFile(f, buf, sizeof(buf) - 1, &got, 0);
        CloseHandle(f);
    }
    buf[got] = 0;
    for (const char *p = buf; *p;) {
        while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')
            p++;
        char sign = *p;
        if (sign == '+' || sign == '-') {
            p++;
            while (*p == ' ' || *p == '\t')
                p++;
            unsigned lo, hi;
            if (hexval(&p, &lo)) {
                hi = lo;
                if (*p == '-') {
                    p++;
                    hexval(&p, &hi);
                }
                for (unsigned i = 0; i < count; i++)
                    if (e[2 * i] >= lo && e[2 * i] <= hi)
                        on[i] = sign == '+';
            }
        }
        while (*p && *p != '\n')
            p++;
    }
    unsigned n = 0, *slot = e + 2 * count;
    for (unsigned i = 0; i < count; i++) {
        if (!on[i] && e[2 * i + 1])
            slot[i] = e[2 * i + 1];
        else
            n++;
    }
    char line[96];
    wsprintfA(line, "%u of %u replaced functions on\r\n", n, count);
    path_next_to_exe(path, "decomp_toggle.log");
    f = CreateFileA(path, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (f != INVALID_HANDLE_VALUE) {
        WriteFile(f, line, lstrlenA(line), &got, 0);
        CloseHandle(f);
    }
}

/* the entry point of a --toggle build: switch the replacements on, then the game's own start-up (the stack as the
 * loader left it) */
__asm__(".globl _decomp_entry\n_decomp_entry:\n\tcall _decomp_apply_toggles\n\tjmp _orig_entry\n");
