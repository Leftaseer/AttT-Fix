/* 0x00446D50: keeps the object src at +0 and reads its settings (vf30) "fOpaqueDist" into +4 and
 * "fTranspDist" into +8 (vf34), +0xC = their difference */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_0060A6F0[], d_0060A6E4[];
typedef void *(__thiscall *vf30_00446D50)(void *self);
typedef void (__thiscall *vf34_00446D50)(void *self, const char *name, float *out);

DECOMP(00446D50)
void __thiscall f_00446D50(void *this, void **s)
{
    float *f = (float *)this;
    
    void **cfg;
    *(void ***)this = s;
    cfg = ((vf30_00446D50)(*(void ***)s)[0x30 / 4])(s);
    ((vf34_00446D50)(*(void ***)cfg)[0x34 / 4])(cfg, d_0060A6F0, f + 1);
    ((vf34_00446D50)(*(void ***)cfg)[0x34 / 4])(cfg, d_0060A6E4, f + 2);
    f[3] = f[1] - f[2];
}
