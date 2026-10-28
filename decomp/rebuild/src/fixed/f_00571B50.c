/* 0x00571B50: Follower::Update(dt): by state (+0x54): 0 follows the target (+0x3C vf68) at the offset +0x40; 1 also
 * rises by the height +0x4C, which falls at the rate 0x6C7850 to 0 (then state 0); 2 waits out +0x50 (then state 1);
 * the object (+0x38) is moved there (the old position kept at +0x58, the moved flag +0x70), with the original's
 * float roundings */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_006C7850[];
typedef float *(__thiscall *vf68_571B50)(void *self);

DECOMP(00571B50)
void __thiscall f_00571B50(void *this, float dt)
{
    char *s = (char *)this;
    float *off = (float *)(s + 0x40), *p, x, y, z;
    void **t;
    char *m;
    switch (*(int *)(s + 0x54)) {
    case 0:
        t = *(void ***)(s + 0x3c);
        p = ((vf68_571B50)(*(void ***)t)[0x68 / 4])(t);
        x = p[0] + off[0];
        y = p[1] + off[1];
        z = p[2] + off[2];
        break;
    case 1: {
        float v = *(float *)(s + 0x4c) - *(float *)d_006C7850 * dt, h, a, b, c;
        *(float *)(s + 0x4c) = v;
        if (!(0.0f < v)) {
            *(float *)(s + 0x4c) = 0.0f;
            *(int *)(s + 0x54) = 0;
        }
        h = *(float *)(s + 0x4c);
        t = *(void ***)(s + 0x3c);
        p = ((vf68_571B50)(*(void ***)t)[0x68 / 4])(t);
        a = p[0] + off[0];
        b = off[1] + p[1];
        c = off[2] + p[2];
        x = a + 0.0f;
        y = b + h;
        z = 0.0f + c;
        break;
    }
    case 2: {
        float w = *(float *)(s + 0x50) - dt;
        *(float *)(s + 0x50) = w;
        if (!(0.0f < w))
            *(int *)(s + 0x54) = 1;
        return;
    }
    default:
        return;
    }
    m = *(char **)(s + 0x38);
    ((unsigned int *)(m + 0x58))[0] = ((unsigned int *)(m + 0x64))[0];
    ((unsigned int *)(m + 0x58))[1] = ((unsigned int *)(m + 0x64))[1];
    ((unsigned int *)(m + 0x58))[2] = ((unsigned int *)(m + 0x64))[2];
    *(float *)(m + 0x64) = x;
    *(float *)(m + 0x68) = y;
    m[0x70] = 1;
    *(float *)(m + 0x6c) = z;
}
