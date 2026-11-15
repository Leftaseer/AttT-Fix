/* 0x004270C0: the grid cell under a point: the column is w * (x + 0.5 * cell width) / cell width and the row is
 * -(h * (z - 0.5 * cell height) / cell height), both truncated (w, h at +0x5C/+0x60, the cell size at +0x78/+0x7C),
 * clamped to the grid; the two ints go through the output argument, which is returned. */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(004270C0)
int *__thiscall f_004270C0(void *this, int *out, float *point)
{
    char *s = (char *)this;
    int w = *(int *)(s + 0x5c), h = *(int *)(s + 0x60);
    double cw = *(float *)(s + 0x78), ch = *(float *)(s + 0x7c);
    int cx = (int)((double)(unsigned int)w * ((double)point[0] + 0.5 * cw) / cw);
    int cy = (int)-((double)(unsigned int)h * ((double)point[2] - 0.5 * ch) / ch);
    out[0] = cx;
    if (cx < w) {
        if (cx < 0)
            out[0] = 0;
    }
    else
        out[0] = w - 1;
    out[1] = cy;
    if (cy < h) {
        if (cy < 0)
            out[1] = 0;
    }
    else
        out[1] = h - 1;
    return out;
}
