/* 0x00455640: packs four 0..1 floats into 0xAARRGGBB as (int)(f * 255 + 0.5); the compares are comiss + jb,
 * so an unordered value takes the conversion path (which yields 0) instead of the >= 1 path the C form picks */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP_C char d_00607CE0[], d_00609620[], d_0068AE40[];

static uint f_00455640_byte(float f)
{
    if (f >= *(float *)d_0068AE40) return 0xff;
    if (!(0.0f >= f))
        return (uint)(long long)TRUNC((double)f * *(double *)d_00609620 + *(double *)d_00607CE0);
    return 0;
}

DECOMP(00455640)
uint __fastcall f_00455640(float *param_1)
{
    uint a = f_00455640_byte(param_1[3]);
    uint r = f_00455640_byte(param_1[0]);
    uint g = f_00455640_byte(param_1[1]);
    uint b = f_00455640_byte(param_1[2]);

    return ((a << 8 | r) << 8 | g) << 8 | b;
}
