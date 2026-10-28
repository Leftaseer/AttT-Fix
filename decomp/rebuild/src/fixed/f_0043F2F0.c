/* 0x0043F2F0: PointInPolygon: the sum of the angles (0x0043F260) the polygon's edges subtend from the point
 * (*b + (ox, oy)), the polygon placed at *a; inside when its magnitude reaches the double at 0x60A228 */
/* @conv - 0 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_43F2F0;
DECOMP_C V2_43F2F0 *__thiscall sub_004205A0(V2_43F2F0 *self, float x, float y);
DECOMP_C int __thiscall sub_004D3E80(void *poly);
DECOMP_C float *__thiscall sub_0047F6E0(void *poly);
DECOMP_C void *__thiscall sub_0047F730(void *poly, int which);
DECOMP_C double __cdecl sub_0043F260(float ux, float uy, float vx, float vy);
DECOMP_C char d_0060A228[];

DECOMP(0043F2F0)
int __cdecl f_0043F2F0(float *a, float *b, void *poly, float ox, float oy)
{
    float sum = 0.0f, m;
    V2_43F2F0 u, v;
    int n, r;
    sub_004205A0(&u, 0.0f, 0.0f);
    sub_004205A0(&v, 0.0f, 0.0f);
    r = sub_004D3E80(poly);
    for (n = r - 1; n > 0; n--) {
        u.x = (a[0] + sub_0047F6E0(poly)[0]) - (b[0] + ox);
        u.y = (sub_0047F6E0(poly)[1] + a[1]) - (oy + b[1]);
        sub_0047F730(poly, 0);
        v.x = (sub_0047F6E0(poly)[0] + a[0]) - (b[0] + ox);
        v.y = (sub_0047F6E0(poly)[1] + a[1]) - (oy + b[1]);
        sum = (float)(sub_0043F260(u.x, u.y, v.x, v.y) + sum);
    }
    m = __builtin_fabsf(sum);
    if (*(double *)d_0060A228 > m)
        return 0;
    if (m >= *(double *)d_0060A228)
        return 1;
    return r;                                       /* (a NaN sum: EAX as the original leaves it) */
}
