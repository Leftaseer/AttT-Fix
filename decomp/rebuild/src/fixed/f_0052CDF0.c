#include "auto_pre.h"

DECOMP_C float __thiscall sub_00473110(void *terrain, float x, float z);
DECOMP_C double decomp_CIatan2(double, double);
DECOMP_C void *__stdcall sub_005B80C2(void *matrix, float angle);
DECOMP_C void *__stdcall sub_005B8038(void *matrix, float angle);
DECOMP_C void *__stdcall sub_005B8020(void *matrix, void *left, void *right);
DECOMP_C char d_006095F0[], d_0060F708[];

/* @func 0052CDF0 */
DECOMP(0052CDF0)
void *__thiscall f_0052CDF0(char *object, char *item, const float *delta)
{
    *(float *)(item + 0x58) += delta[0];
    *(float *)(item + 0x5c) += delta[1];
    *(float *)(item + 0xac) += delta[0];
    *(float *)(item + 0xb4) += delta[1];

    void *terrain = *(void **)(object + 0x1c8);
    float x = *(float *)(item + 0x58);
    float z = *(float *)(item + 0x5c);
    float radius = *(float *)(item + 0x60);
    *(float *)(item + 0xb0) = sub_00473110(terrain, x, z);

    float near_z = GH_FROUND(z - radius);
    float near_height = GH_FROUND(sub_00473110(terrain, x, near_z));
    float far_z = GH_FROUND(radius + z);
    float span_z = GH_FROUND(far_z - near_z);
    float rise_z = GH_FROUND(sub_00473110(terrain, x, far_z) - near_height);
    float pitch = GH_FROUND(decomp_CIatan2(span_z, rise_z));
    if (0.0f > span_z)
        pitch = GH_FROUND(pitch + *(double *)d_006095F0);
    float first_rotation = GH_FROUND(-(*(double *)d_0060F708 - pitch));

    float near_x = GH_FROUND(x - radius);
    near_height = GH_FROUND(sub_00473110(terrain, near_x, z));
    float far_x = GH_FROUND(x + radius);
    float rise_x = GH_FROUND(sub_00473110(terrain, far_x, z) - near_height);
    float span_x = GH_FROUND(far_x - near_x);
    float second_rotation = GH_FROUND(decomp_CIatan2(rise_x, span_x));
    if (0.0f > rise_x)
        second_rotation = GH_FROUND(second_rotation + *(double *)d_006095F0);

    unsigned int first[16], second[16], combined[16];
    sub_005B80C2(first, first_rotation);
    sub_005B8038(second, second_rotation);
    void *result = sub_005B8020(combined, first, second);
    __builtin_memcpy(second, combined, sizeof(second));
    // The translation is the final matrix row, within the same 16-dword object.
    __builtin_memcpy(second + 12, item + 0xac, 3 * sizeof(*second));
    __builtin_memcpy(item + 0x7c, second, sizeof(second));
    return result;
}
