/* 0x0042EEC0: the vararg form of 0x004208B0 (a StringCchPrintfA-style formatting into dst of size `size`): the
 * size above 0x7FFFFFFF is E_INVALIDARG, everything else is 0x004208B0's */
/* @func 0042EEC0 */
#include "auto_pre.h"
#include <stdarg.h>
DECOMP_C unsigned int __stdcall sub_004208B0(char *buf, unsigned int size, const char *format, void *args);

DECOMP(0042EEC0)
unsigned int __cdecl f_0042EEC0(char *dst, unsigned int size, const char *format, ...)
{
    va_list args;
    if (size > 0x7fffffffu)
        return 0x80070057u;
    va_start(args, format);
    return sub_004208B0(dst, size, format, args);
}
