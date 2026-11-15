/* 0x00426070: the ActionScript object's destructor: the vtables 0x00607F0C and 0x00607F00, then the action at
 * +0x6C and the manager at +0x60 released (each an intrusive count at +4; the drop to zero calls the first vtable
 * slot with 1), the vtable 0x00607ED0 and the CRenderObject base destructor (0x004AB940) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607F0C[], d_00607F00[], d_00607ED0[];
DECOMP_C void __thiscall sub_004AB940(void *self);
typedef void (__thiscall *releaser_426070)(void *self, int flags);

static void release_426070(void *obj)
{
    if (obj && --*(unsigned int *)((char *)obj + 4) == 0)
        ((releaser_426070)(*(void ***)obj)[0])(obj, 1);
}

DECOMP(00426070)
void __thiscall f_00426070(void *this)
{
    char *s = (char *)this;
    *(const void **)s = d_00607F0C;
    *(const void **)(s + 0x58) = d_00607F00;
    release_426070(*(void **)(s + 0x6c));
    release_426070(*(void **)(s + 0x60));
    *(const void **)(s + 0x58) = d_00607ED0;
    sub_004AB940(s);
}
