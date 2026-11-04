#include "auto_pre.h"

DECOMP_C unsigned int __cdecl sub_004F6470(float *degrees);
DECOMP_C char d_00608974[], d_00609308[], d_0060984C[], d_0060A178[], d_0068AE08[];

/* @func 004ACB80 */
DECOMP(004ACB80)
unsigned int __thiscall f_004ACB80(char *object, unsigned int angle_bits, int ticks)
{
    float angle = BITCAST(float, angle_bits);
    float delta = GH_FROUND(*(float *)(object + 0x84) - angle);
    unsigned int unchanged = sub_004F6470(&delta);
    double circle = *(double *)d_00609308;
    if (*(float *)d_0060984C > delta || *(double *)d_0060A178 > circle - delta)
        return unchanged;

    delta = GH_FROUND(angle - *(float *)(object + 0x78));
    __builtin_memcpy(object + 0x84, &angle_bits, sizeof(angle_bits));
    sub_004F6470(&delta);
    double duration = ticks;
    if (ticks < 0)
        duration += *(float *)d_0068AE08;
    double step;
    if (*(float *)d_00608974 > delta) {
        step = delta / duration;
    } else {
        step = (circle - delta) / duration;
        __asm__("fchs" : "=t"(step) : "0"(step));
    }
    *(float *)(object + 0x88) = step;
    object[0x8c] = 1;
    *(unsigned int *)(object + 0x90) = 0;
    *(int *)(object + 0x94) = ticks;
    return ticks;
}
