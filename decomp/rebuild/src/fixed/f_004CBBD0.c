/* 0x004CBBD0: CStandardBorder::Update: the base update (0x004AD110, with EAX as it came), its model (+0x1CC: vf04(dt),
 * and vfD8 when +0x1DC of it is set), visibility (0x00458120 of the camera 0x6CA2C8, which takes the position +0x1DC
 * in EAX too) at +0x1D4 and the level of detail (+0x1D8) by the camera distance (sqrt, as a float) against the limits
 * at 0x607F84, 0x60C0A0, 0x60B360, 0x611DC4, 0x60AB40; beyond 0x608858 it is hidden */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 004CBBD0 custom */
DECOMP_C unsigned int __cdecl sub_004AD110(void *self, unsigned int eax, float dt);
DECOMP_C unsigned int __cdecl sub_00458120(void *self, void *eax, void *pos);
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C char d_006CA2C8[], d_006CA2C4[], d_00607F84[], d_0060C0A0[], d_0060B360[], d_00611DC4[], d_0060AB40[],
              d_00608858[];
typedef void (__thiscall *vf04_4CBBD0)(void *self, float dt);
typedef void (__thiscall *vf_4CBBD0)(void *self);

DECOMP(004CBBD0)
void __cdecl f_004CBBD0(void *this, unsigned int eax, float dt)
{
    char *s = (char *)this;
    char *m;
    float *cam, dx, dy, dz, d2, dist;
    unsigned char vis;
    sub_004AD110(this, eax, dt);
    m = *(char **)(s + 0x1cc);
    ((vf04_4CBBD0)(*(void ***)m)[1])(m, dt);
    m = *(char **)(s + 0x1cc);
    if (m[0x1dc])
        ((vf_4CBBD0)(*(void ***)m)[0xd8 / 4])(m);
    vis = (unsigned char)sub_00458120(*(void **)d_006CA2C8, s + 0x1dc, s + 0x1dc);
    s[0x1d4] = vis;
    if (!vis)
        return;
    cam = (float *)(*(char **)d_006CA2C4 + 0x44);
    dx = cam[0] - *(float *)(s + 0x64);
    dy = cam[1] - *(float *)(s + 0x68);
    dz = cam[2] - *(float *)(s + 0x6c);
    d2 = dx * dx + dy * dy + dz * dz;
    dist = (float)decomp_CIsqrt(d2);
    if (*(float *)d_00607F84 > dist)
        *(int *)(s + 0x1d8) = 0;
    else if (*(float *)d_0060C0A0 > dist)
        *(int *)(s + 0x1d8) = 1;
    else if (*(double *)d_0060B360 > dist)
        *(int *)(s + 0x1d8) = 2;
    else if (*(float *)d_00611DC4 > dist)
        *(int *)(s + 0x1d8) = 3;
    else if (*(double *)d_0060AB40 > dist)
        *(int *)(s + 0x1d8) = 4;
    else if (dist > *(double *)d_00608858)
        s[0x1d4] = 0;
}
