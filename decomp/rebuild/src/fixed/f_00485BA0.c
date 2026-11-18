/* 0x00485BA0: opens the resource named by the by-value string through the reader at +0xC8.
 * When +0xF4 is set, processes the object and closes the reader; otherwise returns false. */
/* @conv ECX 28 */
#include "auto_pre.h"

typedef struct {
    unsigned int words[7];
} String_00485BA0;

DECOMP_C unsigned char __thiscall sub_00459050(void *self, const void *name, int mode);
DECOMP_C void __thiscall sub_004857E0(void *self);
DECOMP_C void __thiscall sub_00459010(void *self);
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00485BA0)
unsigned char __thiscall f_00485BA0(char *this, String_00485BA0 name)
{
    sub_00459050(this + 0xc8, &name, 1);
    if (!this[0xf4]) {
        imp_00607330(&name);
        return 0;
    }
    sub_004857E0(this);
    sub_00459010(this + 0xc8);
    imp_00607330(&name);
    return 1;
}
