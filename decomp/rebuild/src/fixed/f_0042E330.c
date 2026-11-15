/* 0x0042E330: the projectile's destructor: its own vtable (0x00608B5C), the trail (+0x2C8, deleted through slot 0
 * with 1) and the mesh list (+0x1C8: every mesh's +0x24 marked, the array freed, the vector cleared), then the 3D
 * object base destructor 0x004AD020 */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef void (__thiscall *dtor_42E330)(void *self, int flag);
DECOMP_C char d_00608B5C[];                                            /* vftable */
DECOMP_C void __thiscall sub_004AD020(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(0042E330)
void __thiscall f_0042E330(void *this)
{
    char *s = (char *)this, *list = *(char **)(s + 0x1c8);
    unsigned int i, n;
    void *trail = *(void **)(s + 0x2c8);
    *(const void **)s = d_00608B5C;
    if (trail)
        ((dtor_42E330)(*(void ***)trail)[0])(trail, 1);
    n = list ? (unsigned int)((*(char **)(s + 0x1cc) - list) >> 2) : 0;
    for (i = 0; i < n; i++)
        *(char *)(*(char **)(list + 4 * i) + 0x24) = 1;
    if (list)
        sub_005E3E9C(list);
    *(void **)(s + 0x1c8) = 0;
    *(void **)(s + 0x1cc) = 0;
    *(void **)(s + 0x1d0) = 0;
    sub_004AD020(s);
}
