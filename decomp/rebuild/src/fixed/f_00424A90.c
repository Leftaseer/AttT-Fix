/* 0x00424A90: unprojects the control manager's mouse position.  The mouse's vf8C/vf90 become camera-plane
 * coordinates, the camera matrix is inverted, the inverse translation is the ray origin, and the coordinate vector
 * transformed by the inverse rotation is the ray direction.  Returns the origin pointer. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void *__stdcall sub_005B801A(float *out, float *det, const float *m);        /* D3DXMatrixInverse */
DECOMP_C char d_0068AE00[], d_006C8958[], d_006C895C[];
typedef double (__thiscall *vfpos_424A90)(void *self);

#define ONE_424A90 (*(double *)d_0068AE00)
#define HEIGHT_424A90 (*(float *)d_006C8958)
#define WIDTH_424A90 (*(float *)d_006C895C)
#define VFPOS_424A90(o, off) ((vfpos_424A90)(*(void ***)(o))[(off) / 4])(o)

DECOMP(00424A90)
float *__thiscall f_00424A90(void *this, float *origin, float *dir)
{
    char *s = (char *)this;
    void *mouse = *(void **)(s + 0x4c);
    char *camera = *(char **)(s + 0x50);
    float m[16];
    float x = (float)(((VFPOS_424A90(mouse, 0x8c) * 2.0) / WIDTH_424A90 - ONE_424A90) /
                      *(float *)(camera + 0xc8));
    float y = (float)-(((VFPOS_424A90(mouse, 0x90) * 2.0) / HEIGHT_424A90 - ONE_424A90) /
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
