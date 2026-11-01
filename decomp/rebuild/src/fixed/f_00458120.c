/* 0x00458120: tests 8 box corners against each of the 6 frustum planes; a corner is in front when its dot
 * product is ordered and > 0 (fcomi + ja), so an unordered product counts as behind just like <= 0, and the
 * function returns EAX with AL cleared when one plane has every corner behind; AL = 1 when no plane does. */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 00458120 custom */

DECOMP(00458120)
undefined4 __cdecl f_00458120(void *this, undefined4 in_eax, float *param_3)
{
    uint hi = (uint)in_eax & 0xFFFFFF00;
    int i, k;

    for (i = 0; i < 6; i++) {
        float *pl = (float *)((int)this + 4 + i * 16);
        float a = pl[0], b = pl[1], c = pl[2], d = pl[3];
        int all_behind = 1;

        for (k = 0; k < 8; k++) {
            float *p = param_3 + 3 * k;
            float dot = d + a * p[0] + b * p[1] + c * p[2];
            if (dot > 0.0f) {
                all_behind = 0;
                break;
            }
        }
        if (all_behind) return hi;
    }
    return hi | 1;
}
