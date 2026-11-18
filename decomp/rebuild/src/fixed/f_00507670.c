/* 0x00507670: the battle-scene form of 0x00424A90, with the mouse at +0x70 and camera at +0x74.  It returns the
 * origin pointer in EAX as the original does, although its callers use only the two output vectors. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void *__stdcall sub_005B801A(float *out, float *det, const float *m);        /* D3DXMatrixInverse */
DECOMP_C char d_0068AE00[], d_006C8958[], d_006C895C[];
typedef double (__thiscall *vfpos_507670)(void *self);

#define ONE_507670 (*(double *)d_0068AE00)
#define HEIGHT_507670 (*(float *)d_006C8958)
#define WIDTH_507670 (*(float *)d_006C895C)
#define VFPOS_507670(o, off) ((vfpos_507670)(*(void ***)(o))[(off) / 4])(o)

DECOMP(00507670)
float *__thiscall f_00507670(void *this, float *origin, float *dir)
{
    char *s = (char *)this;
    void *mouse = *(void **)(s + 0x70);
    char *camera = *(char **)(s + 0x74);
    float m[16];
    float x = (float)(((VFPOS_507670(mouse, 0x8c) * 2.0) / WIDTH_507670 - ONE_507670) /
                      *(float *)(camera + 0xc8));
    float y = (float)-(((VFPOS_507670(mouse, 0x90) * 2.0) / HEIGHT_507670 - ONE_507670) /
                       *(float *)(camera + 0xdc));
    sub_005B801A(m, 0, (const float *)(camera + 0x88));
    dir[0] = y * m[4] + x * m[0] + m[8];
    dir[1] = m[1] * x + m[5] * y + m[9];
    dir[2] = y * m[6] + m[2] * x + m[10];
    origin[0] = m[12];
    origin[1] = m[13];
    origin[2] = m[14];
    return origin;
}
