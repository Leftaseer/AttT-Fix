/* 0x00422CE0: copies the 0x64-byte records of [first, last) into dst: each destination gets the MSVCP80 string
 * copy at +0 and the block copy at +0x1C (0x00421150); a null destination skips the copies.  The destination
 * advances with every record, so the return is the end of the output. */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void __thiscall sub_00421150(void *dst, const void *src);

DECOMP(00422CE0)
void *__cdecl f_00422CE0(void *first, void *last, void *dst)
{
    char *f = (char *)first, *l = (char *)last, *d = (char *)dst;
    for (; f != l; f += 0x64) {
        if (d) {
            imp_00607334(d, f);
            sub_00421150(d + 0x1c, f + 0x1c);
        }
        d += 0x64;
    }
    return d;
}
