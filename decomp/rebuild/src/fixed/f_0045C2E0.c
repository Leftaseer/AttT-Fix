/* 0x0045C2E0: GizmoContourObject::vf1_248 (ECX is the base at +0x248): 0x00435640 on the global at 0x6CA2C4, sets the
 * world transform (D3DTS_WORLD) to the object's matrix (0x004ACD60), then vf94(1, 0) of the object at +0x10, if any;
 * returns what the last call returned */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int m[16]; } M44_45C2E0;
DECOMP_C void __thiscall sub_00435640(void *self);
DECOMP_C void __thiscall sub_004ACD60(void *self, M44_45C2E0 *out);
DECOMP_C char d_006CA2C4[], d_006C8C10[];
typedef unsigned int (__stdcall *SetTransform_45C2E0)(void *dev, unsigned int state, const M44_45C2E0 *m);
typedef unsigned int (__thiscall *vf94_45C2E0)(void *self, int a, int b);

DECOMP(0045C2E0)
unsigned int __thiscall f_0045C2E0(void *this)
{
    char *s = (char *)this;
    M44_45C2E0 m;
    void **dev, **o;
    unsigned int r;
    sub_00435640(*(void **)d_006CA2C4);
    sub_004ACD60(s - 0x248, &m);
    dev = *(void ***)d_006C8C10;
    r = ((SetTransform_45C2E0)(*(void ***)dev)[0xb0 / 4])(dev, 0x100, &m);
    o = *(void ***)(s + 0x10);
    if (o)
        r = ((vf94_45C2E0)(*(void ***)o)[0x94 / 4])(o, 1, 0);
    return r;
}
