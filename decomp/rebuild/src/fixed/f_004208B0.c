/* 0x004208B0: formats into the buffer arg 1 of size arg 2, leaving room for the terminator: with a zero size it
 * fails with E_INVALIDARG; _vsnprintf (MSVCR80 IAT 0x607398) gets (buffer, size - 1, format arg 3, arguments arg 4),
 * and a negative or oversized result is an error (E_INSUFFICIENT_BUFFER) with a terminator forced into the last byte;
 * a result that exactly fills size - 1 also gets the last byte terminated.  Returns S_OK (0) otherwise. */
#include "auto_pre.h"
DECOMP_C int (__cdecl *imp_00607398)(char *, unsigned int, const char *, void *) __asm__("__imp___vsnprintf");

DECOMP(004208B0)
unsigned int __stdcall f_004208B0(char *buf, unsigned int size, const char *format, void *args)
{
    int n;
    if (size == 0)
        return 0x80070057u;
    n = imp_00607398(buf, size - 1, format, args);
    if (n < 0 || (unsigned int)n > size - 1) {
        buf[size - 1] = 0;
        return 0x8007007au;
    }
    if ((unsigned int)n == size - 1)
        buf[size - 1] = 0;
    return 0;
}
