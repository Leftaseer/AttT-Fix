/* 0x004F7B60: CViewerMesh::Tick: when the model's (+0x58) frame (+0x1D8) changed and there is a track (+0x5C, 12
 * bytes a frame) the model moves by the track's step along its heading (+0x78, times the double at 0x608528):
 * x += cos * step, z -= sin * step (the old x at +0x58, z at +0x60, moved flag +0x70), with the original's float
 * roundings; the frame is kept at +0x60 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C char d_00608528[];

DECOMP(004F7B60)
void __thiscall f_004F7B60(void *this)
{
    char *s = (char *)this;
    char *m = *(char **)(s + 0x58);
    int f = *(int *)(m + 0x1d8);
    float *t = *(float **)(s + 0x5c);
    if (f && f != *(int *)(s + 0x60) && t) {
        float heading = *(float *)(m + 0x78);
        float step = t[f * 3] - t[f * 3 - 3];
        float x = *(float *)(m + 0x64), a, c;
        double z;
        *(float *)(m + 0x58) = x;
        a = (float)(heading * *(double *)d_00608528);
        c = (float)decomp_CIcos(a);
        m[0x70] = 1;
        c = c * step;
        *(float *)(m + 0x64) = c + x;
        m = *(char **)(s + 0x58);
        z = *(float *)(m + 0x6c);
        *(float *)(m + 0x60) = *(float *)(m + 0x6c);
        a = (float)(heading * *(double *)d_00608528);
        c = (float)decomp_CIsin(a);
        m[0x70] = 1;
        c = c * step;
        *(float *)(m + 0x6c) = (float)(z - c);
    }
    *(int *)(s + 0x60) = *(int *)(*(char **)(s + 0x58) + 0x1d8);
}
