#include "auto_pre.h"

DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C char d_00608528[];

/* @func 0042AC80 */
DECOMP(0042AC80)
float *__thiscall f_0042AC80(char *track, float *out, float degrees, int index)
{
    // The last dword is a record index. The native guard is an integer comparison.
    float delta = 0.0f;
    if (index != *(int *)(track + 0x1d0)) {
        const float *records = *(const float **)(track + 0x1d8);
        delta = GH_FROUND(records[index * 3] - records[index * 3 - 3]);
    }
    float angle = GH_FROUND(degrees * *(double *)d_00608528);
    float cosine = GH_FROUND(decomp_CIcos(angle));
    out[0] = cosine * delta;
    float sine = GH_FROUND(decomp_CIsin(angle));
    out[1] = sine * -delta;
    return out;
}
