/* 0x00463F50: CHero::Render: when visible (+0x49): 0x004AC890, then vfC0 of the renderer at +0x1DC with what
 * 0x00463E20 makes of the position (+0x64), the vfEC of the camera (via +0x1EC) and +0x98; otherwise returns EAX
 * as it came */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 00463F50 custom */
DECOMP_C void __thiscall sub_004AC890(void *self);
DECOMP_C unsigned int __cdecl sub_00463E20(void *pos, void *cam, void *extra);
typedef void *(__thiscall *vfEC_463F50)(void *self);
typedef unsigned int (__thiscall *vfC0_463F50)(void *self, unsigned int v);

DECOMP(00463F50)
unsigned int __cdecl f_00463F50(void *this, unsigned int eax)
{
    char *s = (char *)this;
    void **cam, **r;
    vfC0_463F50 f;
    void *c;
    if (!s[0x49])
        return eax;
    sub_004AC890(this);
    cam = **(void ****)(*(char **)(s + 0x1ec) + 0x14);
    r = *(void ***)(s + 0x1dc);
    f = (vfC0_463F50)(*(void ***)r)[0xc0 / 4];
    c = ((vfEC_463F50)(*(void ***)cam)[0xec / 4])(cam);
    return f(*(void **)(s + 0x1dc), sub_00463E20(s + 0x64, c, s + 0x98));
}
