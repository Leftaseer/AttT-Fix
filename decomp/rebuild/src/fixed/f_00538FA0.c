/* 0x00538FA0: a world creature following its target: farther than +0x1F0 (the squared xz distance of its position,
 * vf68, from +0x204) and either farther than +0x1FC or 0x00538980 false, with the target (+0x1CC) moving (+0x1E4
 * == 2, or +0x1EB) and not +0x4E4, it takes the next waypoint (+0x1E0 into +0x1E8, 0x004CAFE0(0), +0x1EC = 1); then
 * it turns to face the target: atan2 of the xz offset (plus the double at 0x6095F0 for a negative x), times the
 * double at 0x609628, by 0x004ACB80(angle, 10) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C double decomp_CIatan2(double y, double x);
DECOMP_C unsigned char __thiscall sub_00538980(void *self);
DECOMP_C void __thiscall sub_004CAFE0(void *self, unsigned int flag);
DECOMP_C void __thiscall sub_004ACB80(void *self, float angle, int speed);
DECOMP_C char d_006095F0[], d_00609628[];
typedef float *(__thiscall *vf68_538FA0)(void *self);

DECOMP(00538FA0)
void __thiscall f_00538FA0(void *this)
{
    char *s = (char *)this;
    float *p = ((vf68_538FA0)(*(void ***)this)[0x68 / 4])(this), *q;
    float dx = *(float *)(s + 0x204) - p[0];
    float dz = *(float *)(s + 0x20c) - p[2];
    float d2 = dx * dx + 0.0f * 0.0f + dz * dz;
    float ax, az, ang;
    if (d2 > *(float *)(s + 0x1f0) && (d2 > *(float *)(s + 0x1fc) || !sub_00538980(this))) {
        char *t = *(char **)(s + 0x1cc);
        if ((*(int *)(t + 0x1e4) == 2 || t[0x1eb]) && !t[0x4e4]) {
            *(void **)(s + 0x1e8) = *(void **)(s + 0x1e0);
            sub_004CAFE0(*(void **)(s + 0x1e0), 0);
            *(int *)(s + 0x1ec) = 1;
        }
    }
    q = ((vf68_538FA0)(*(void ***)*(void **)(s + 0x1cc))[0x68 / 4])(*(void **)(s + 0x1cc));
    p = ((vf68_538FA0)(*(void ***)this)[0x68 / 4])(this);
    ax = p[0] - q[0];
    az = p[2] - q[2];
    if (0.0f > ax) {
        ang = (float)decomp_CIatan2(ax, az);
        ang = (float)(ang + *(double *)d_006095F0);
    } else
        ang = (float)decomp_CIatan2(ax, az);
    sub_004ACB80(this, (float)(ang * *(double *)d_00609628), 10);
}
