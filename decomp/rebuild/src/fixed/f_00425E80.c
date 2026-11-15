/* 0x00425E80 (one string argument, ret 4): parses a "r:g:b" text - the string is copied to a 256-byte buffer, split
 * by ':' (strtok) and each field converted (atoi); the result is b * 0x00607EC0 + g * 0x0068AE10 +
 * r * 0x00607EB8 * 0x0068AE10, returned as a float. */
/* @conv - 4 */
#include "auto_pre.h"
DECOMP_C char d_00607EC8[];
DECOMP_C double d_00607EB8, d_00607EC0, d_0068AE10;
DECOMP_C char *(__cdecl *imp_006073CC)(char *, const char *) __asm__("__imp__strtok");
DECOMP_C int (__cdecl *imp_006073C8)(const char *) __asm__("__imp__atoi");

DECOMP(00425E80)
float __cdecl f_00425E80(const char *text)
{
    char buf[256], *q = buf, c;
    double v;
    int r, g, b;

    do {
        c = *text++;
        *q++ = c;
    } while (c);
    r = imp_006073C8(imp_006073CC(buf, d_00607EC8));
    g = imp_006073C8(imp_006073CC(0, d_00607EC8));
    b = imp_006073C8(imp_006073CC(0, d_00607EC8));
    v = (double)b * d_00607EC0 + (double)g * d_0068AE10 + (double)r * d_00607EB8 * d_0068AE10;
    return (float)v;
}
