/* 0x00559D20: whether a formation group (groups arg 1, 0x1C0 bytes each, index arg 2) can be placed: each of its
 * positions (0x0055BB60, count 0x0055BBF0) must pass 0x00559880 (with arg 3) and stay clear of every position of the
 * groups before it: the horizontal distance (x and z squared through the inlined integer pow) not below the sum of
 * the two radii (0x0055BC20; the original looks the radii up with the indices swapped between the two groups, kept
 * here) */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int v[3]; } V3_559D20;
DECOMP_C int __thiscall sub_0055BBF0(void *self);
DECOMP_C float *__thiscall sub_0055BB60(void *self, void *out, int i);
DECOMP_C char __stdcall sub_00559880(V3_559D20 p, void *a);
DECOMP_C double __thiscall sub_0055BC20(void *self, int i);
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C char d_0068AE40[];

/* std::pow(float, 2) as inlined: 1 * (d * d), each step rounded to float */
static float sq_559D20(float d)
{
    float r = *(float *)d_0068AE40;
    return r * (d * d);
}

DECOMP(00559D20)
unsigned char __thiscall f_00559D20(void *this, char *groups, int idx, void *a3)
{
    char *g = groups + idx * 0x1c0, *h;
    float t1[3], t2[3], *p, dx2, dz2, dist;
    double x, ra;
    int i, j, k, m;
    for (k = 0; k < sub_0055BBF0(g); k++) {
        p = sub_0055BB60(g, t1, k);
        if (!sub_00559880(*(V3_559D20 *)p, a3))
            return 0;
    }
    for (i = idx - 1; i >= 0; i--) {
        h = groups + i * 0x1c0;
        for (j = 0; j < sub_0055BBF0(g); j++)
            for (m = 0; m < sub_0055BBF0(h); m++) {
                x = sub_0055BB60(g, t1, j)[0];
                dx2 = sq_559D20((float)(x - sub_0055BB60(h, t2, m)[0]));
                x = sub_0055BB60(g, t1, j)[2];
                dz2 = sq_559D20((float)(x - sub_0055BB60(h, t2, m)[2]));
                ra = sub_0055BC20(h, j);
                dist = (float)decomp_CIsqrt((float)(dz2 + dx2));
                if (sub_0055BC20(g, m) + ra > dist)
                    return 0;
            }
    }
    return 1;
}
