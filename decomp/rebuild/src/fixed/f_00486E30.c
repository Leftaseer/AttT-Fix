/* 0x00486E30: Lua Started(): true when the flag +0x1FC is set or one of the objects (vector +0x1D0..+0x1D4) says so
 * through its delegate (+0x24C: function +0x250, context +0x258); pushed as a boolean under a stack guard object (an
 * Object with the vtable 0x60826C, then 0x607CB8, destroyed by Object::~Object); one result */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00403280(void *L, int b);                    /* lua_pushboolean */
DECOMP_C void __thiscall sub_00422000(void *self);                    /* Object::~Object */
DECOMP_C char d_008D122C[], d_0060826C[], d_00607CB8[];
typedef char (__thiscall *dlg_486E30)(void *ctx, void *d);

DECOMP(00486E30)
int __thiscall f_00486E30(void *this, void *args)
{
    char *s = (char *)this;
    int r = 1;
    unsigned int guard[3];
    if (!s[0x1fc]) {
        unsigned int i;
        r = 0;
        for (i = 0; *(char ***)(s + 0x1d0) &&
                    i < (unsigned int)((*(char **)(s + 0x1d4) - *(char **)(s + 0x1d0)) >> 2); i++) {
            char *e = (*(char ***)(s + 0x1d0))[i];
            if ((*(dlg_486E30 *)(e + 0x250))(*(void **)(e + 0x258), e + 0x24c)) {
                r = 1;
                break;
            }
        }
    }
    guard[1] = 0;
    guard[0] = (unsigned int)d_0060826C;
    guard[2] = 0;
    sub_00403280(*(void **)d_008D122C, r);
    guard[2] = 1;
    guard[0] = (unsigned int)d_00607CB8;
    sub_00422000(guard);
    return 1;
}
