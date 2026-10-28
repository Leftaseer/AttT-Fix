/* 0x00440990: whether the point is accepted: the offset (x, z) from the centre (+0x3FC, +0x404) must be shorter than
 * the radius (+0x414) when that is checked (+0x21); then, if wanted (+0x20), 0x00440490 with the offset; a bool in
 * AL */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_440990;
DECOMP_C V2_440990 *__thiscall sub_004205A0(V2_440990 *self, float x, float y);
DECOMP_C float __thiscall sub_0047F4F0(V2_440990 *self);
DECOMP_C void __thiscall sub_00440490(void *self, V2_440990 *d);

DECOMP(00440990)
unsigned char __thiscall f_00440990(void *this, float *pos)
{
    char *s = (char *)this;
    V2_440990 tmp;
    float dx = pos[0] - *(float *)(s + 0x3fc);
    float dz = pos[2] - *(float *)(s + 0x404);
    if (s[0x21] && !(*(float *)(s + 0x414) > sub_0047F4F0(sub_004205A0(&tmp, dx, dz))))
        return 0;
    if (s[0x20])
        sub_00440490(this, sub_004205A0(&tmp, dx, dz));
    return 1;
}
