#include "auto_pre.h"

/* @func 00456B20 */
DECOMP(00456B20)
void __stdcall f_00456B20(const float *normal, const float *origin, float *point)
{
    // Keep the native negation before division, including the NaN sign.
    volatile float denominator = -normal[1];
    point[1] = ((point[2] - origin[2]) * normal[2] +
                (point[0] - origin[0]) * normal[0]) / denominator + origin[1];
}
