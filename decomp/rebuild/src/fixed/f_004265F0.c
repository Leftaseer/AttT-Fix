/* 0x004265F0: the virtual at +0x7c gets half of the point arg 1's offset from the size (+0x74/+0x78), negated,
 * then the one at +0x98 gets the original point.  The deltas are rounded to float before scaling; the vtable is
 * reloaded for the second call. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(004265F0)
unsigned int __thiscall f_004265F0(void *self, const float *point)
{
    char *s = (char *)self;
    volatile float dx = point[0] - *(float *)(s + 0x74);
    volatile float dy = point[1] - *(float *)(s + 0x78);
    float scaled[2];
    scaled[0] = (float)(-(double)dx * 0.5);
    scaled[1] = (float)(-(double)dy * 0.5);
    (*(void (__thiscall **)(void *, const float *))(*(char **)self + 0x7c))(self, scaled);
    return (*(unsigned int (__thiscall **)(void *, const float *))(*(char **)self + 0x98))(self, point);
}
