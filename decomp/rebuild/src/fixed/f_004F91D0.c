/* 0x004F91D0: CWaterCircleManager::Update(dt): the camera position (+0x64 vf68) at +0x44; the clock (+0x38, 64 bits)
 * advances by dt (_ftol); once a period (+0x40) has passed and the camera is just under the water (its y at most 0,
 * above the depth at 0x6130A0) the clock wraps (_allrem) and a circle starts (0x004F9080); the next period comes
 * from 0x004F9020(whether the camera moved), and the position is kept at +0x50 */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C long long __stdcall sub_005E42B0(long long a, long long b);      /* _allrem */
DECOMP_C void __thiscall sub_004F9080(void *self);
DECOMP_C unsigned int __thiscall sub_004F9020(void *self, unsigned int moved);
DECOMP_C char d_006130A0[];
typedef unsigned int *(__thiscall *vf68_4F91D0)(void *self);

DECOMP(004F91D0)
void __thiscall f_004F91D0(void *this, float dt)
{
    char *s = (char *)this;
    void **cam = *(void ***)(s + 0x64);
    unsigned int *p = ((vf68_4F91D0)(*(void ***)cam)[0x68 / 4])(cam);
    float q[3];
    long long t;
    unsigned int per;
    int moved;
    ((unsigned int *)(s + 0x44))[0] = p[0];
    ((unsigned int *)(s + 0x44))[1] = p[1];
    ((unsigned int *)(s + 0x44))[2] = p[2];
    *(long long *)(s + 0x38) += (long long)dt;
    cam = *(void ***)(s + 0x64);
    p = ((vf68_4F91D0)(*(void ***)cam)[0x68 / 4])(cam);
    ((unsigned int *)q)[0] = p[0];
    ((unsigned int *)q)[1] = p[1];
    ((unsigned int *)q)[2] = p[2];
    t = *(long long *)(s + 0x38);
    per = *(unsigned int *)(s + 0x40);
    if (t >= (long long)per && !(0.0f < q[1]) && q[1] > *(float *)d_006130A0) {
        *(long long *)(s + 0x38) = sub_005E42B0(t, per);
        sub_004F9080(this);
    }
    moved = !(*(float *)(s + 0x50) == *(float *)(s + 0x44) && *(float *)(s + 0x54) == *(float *)(s + 0x48) &&
              *(float *)(s + 0x58) == *(float *)(s + 0x4c));
    *(unsigned int *)(s + 0x40) = sub_004F9020(this, moved);
    ((unsigned int *)(s + 0x50))[0] = ((unsigned int *)(s + 0x44))[0];
    ((unsigned int *)(s + 0x50))[1] = ((unsigned int *)(s + 0x44))[1];
    ((unsigned int *)(s + 0x50))[2] = ((unsigned int *)(s + 0x44))[2];
}
