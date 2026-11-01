/* 0x00456B50: constructor: stores the vtable, copies 12 floats from param_1 to +0x1c4, then fills +0x200 and
 * +0x204 with the lengths of two vectors built from +0x1d0/+0x1e8 against +0x1c4; the original rounds each
 * difference and each squared sum to float (stored to stack slots) before the CRT square root, so an
 * overflowing sum becomes +inf instead of a huge finite value */
/* @conv ECX 20 */
#include "auto_pre.h"

DECOMP_C char d_005E8611[], d_0060B4F4[], d_0060FA8B[];
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C undefined4 *__thiscall sub_004AD180(void *, void *, undefined4, undefined4);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00456B50)
void *__thiscall f_00456B50(void *this, float *param_1, undefined4 param_2, undefined4 param_3, undefined4 param_4, undefined4 param_5)
{
    unsigned char sbuf[32] __attribute__((aligned(16)));
    float *m = (float *)((int)this + 0x1c4);
    volatile float ax, ay, az, bx, by, bz, l2;
    int i;

    imp_00607324(sbuf, d_0060FA8B);
    sub_004AD180(this, sbuf, 0, 0);
    imp_00607330(sbuf);

    *(undefined4 *)((int)this + 0x208) = param_5;
    *(undefined4 **)this = (undefined4 *)d_0060B4F4;
    for (i = 0; i < 12; i++)
        m[i] = param_1[i];

    ax = *(float *)((int)this + 0x1e8) - m[0];
    ay = *(float *)((int)this + 0x1ec) - m[1];
    az = *(float *)((int)this + 0x1f0) - m[2];
    bx = *(float *)((int)this + 0x1d0) - m[0];
    by = *(float *)((int)this + 0x1d4) - m[1];
    bz = *(float *)((int)this + 0x1d8) - m[2];

    l2 = (bx * bx + by * by) + bz * bz;
    *(float *)((int)this + 0x200) = (float)decomp_CIsqrt(l2);
    l2 = (ax * ax + ay * ay) + az * az;
    *(float *)((int)this + 0x204) = (float)decomp_CIsqrt(l2);

    *(undefined4 *)((int)this + 0x1f4) = param_2;
    *(undefined4 *)((int)this + 0x1f8) = param_3;
    *(undefined4 *)((int)this + 0x1fc) = param_4;
    return this;
}
