/* 0x00426750: feeds the point arg 1 to the object's virtuals: the one at +0x7c gets the point negated and halved
 * (the double at 0x00607CE0 is 0.5), then the one at +0xa8 gets the original point.  The vtable is reloaded for the
 * second call. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607CE0[];

DECOMP(00426750)
void __thiscall f_00426750(void *self, const float *point)
{
    double scale = *(double *)d_00607CE0;
    float scaled[2];
    scaled[0] = (float)(-(double)point[0] * scale);
    scaled[1] = (float)(-(double)point[1] * scale);
    (*(void (__thiscall **)(void *, const float *))(*(char **)self + 0x7c))(self, scaled);
    (*(void (__thiscall **)(void *, const float *))(*(char **)self + 0xa8))(self, point);
}
