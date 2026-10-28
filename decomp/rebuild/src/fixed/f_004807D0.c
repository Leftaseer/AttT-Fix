/* 0x004807D0: whether the point p is inside the triangle (a, b, c): on the same side of the three edges (0x00480020,
 * a method of the point taking the edge's ends) */
/* @conv - 0 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_4807D0;
DECOMP_C int __thiscall sub_00480020(V2_4807D0 *p, V2_4807D0 *e0, V2_4807D0 *e1);

DECOMP(004807D0)
int __cdecl f_004807D0(V2_4807D0 p, V2_4807D0 a, V2_4807D0 b, V2_4807D0 c)
{
    if (sub_00480020(&p, &a, &b) && sub_00480020(&p, &b, &c) && sub_00480020(&p, &c, &a))
        return 1;
    return 0;
}
