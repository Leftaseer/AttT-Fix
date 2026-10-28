/* 0x004F7C60: a CViewerMesh tick: with no frame (+0x1D8 of the model +0x58) the model's position (+0x64) becomes its
 * old one (+0x58) and is zeroed; when the frame changed and there is a track (+0x5C, 12 bytes a frame) the model
 * moves by the track's step along its heading (+0x78, times the double at 0x608528): x += cos * step,
 * z -= sin * step, with the original's float roundings; either way it is marked moved (+0x70); the frame is kept at
 * +0x60 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C char d_00608528[];

DECOMP(004F7C60)
void __thiscall f_004F7C60(void *this)
{
    char *s = (char *)this;
    char *m = *(char **)(s + 0x58);
    int f = *(int *)(m + 0x1d8);
    float *t;
    if (!f) {
        ((unsigned int *)(m + 0x58))[0] = ((unsigned int *)(m + 0x64))[0];
        ((unsigned int *)(m + 0x58))[1] = ((unsigned int *)(m + 0x64))[1];
        ((unsigned int *)(m + 0x58))[2] = ((unsigned int *)(m + 0x64))[2];
        *(float *)(m + 0x64) = 0.0f;
        *(float *)(m + 0x68) = 0.0f;
        *(float *)(m + 0x6c) = 0.0f;
    } else {
        float heading, step, x, a, c;
        double z;
        t = *(float **)(s + 0x5c);
        if (f == *(int *)(s + 0x60) || !t)
            goto done;
        heading = *(float *)(m + 0x78);
        step = t[f * 3] - t[f * 3 - 3];
        x = *(float *)(m + 0x64);
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
        c = c * step;
        *(float *)(m + 0x6c) = (float)(z - c);
    }
    m[0x70] = 1;
done:
    *(int *)(s + 0x60) = *(int *)(*(char **)(s + 0x58) + 0x1d8);
}
