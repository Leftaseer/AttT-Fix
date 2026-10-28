/* 0x00437720: 0x00437460 with the 19 dwords of *p by value (six vectors and, the 13th, a float the original copies
 * through the x87) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef unsigned int u_437720;
DECOMP_C unsigned int __thiscall sub_00437460(void *self, u_437720, u_437720, u_437720, u_437720, u_437720, u_437720,
                                              u_437720, u_437720, u_437720, u_437720, u_437720, u_437720, float,
                                              u_437720, u_437720, u_437720, u_437720, u_437720, u_437720);

DECOMP(00437720)
unsigned int __thiscall f_00437720(void *this, unsigned int *p)
{
    return sub_00437460(this, p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11],
                        ((float *)p)[12], p[13], p[14], p[15], p[16], p[17], p[18]);
}
