/* 0x0042DA70: writes the world matrix of animation frame `frame` of the key list the mesh object (+0x78) picks out of
 * the vector at pose_source+4/+8 into `out` and returns `out`. A list entry holds the records at +0 and their count at
 * +8 / stride count at +0xC (a record is stride*0x18 bytes; an out-of-range frame reads record 0); the record's first
 * vec3 is the rotation (yaw at +4, pitch at +0, roll at +8, 0x005B802C = D3DXMatrixRotationYawPitchRoll), its second
 * vec3 (+0xC..+0x14) the translation (matrix row 3); the result is multiplied by the constant matrix at 0x006C1190
 * (0x005B8020 = D3DXMatrixMultiply). */
/* @conv ECX 12 */
#include "auto_pre.h"

typedef struct {
    float pitch, yaw, roll;                            /* +0x00 */
    float x, y, z;                                      /* +0x0C */
} frame_42DA70;                                         /* 0x18 bytes */

typedef struct {
    char *data;                                         /* +0x00 */
    int unused;                                         /* +0x04 */
    unsigned int count;                                 /* +0x08 */
    int stride;                                         /* +0x0C */
} keylist_42DA70;

DECOMP_C float *__stdcall sub_005B802C(float *m, float yaw, float pitch, float roll); /* D3DXMatrixRotationYawPitchRoll */
DECOMP_C float *__stdcall sub_005B8020(float *out, const float *a, const float *b);   /* D3DXMatrixMultiply */
DECOMP_C char d_006C1190[];

DECOMP(0042DA70)
float *__thiscall f_0042DA70(void *self, float *out, char *pose_source, void *frame_arg)
{
    char *s = (char *)self;
    unsigned int frame = (unsigned int)frame_arg;
    char *begin = *(char **)(pose_source + 4);
    keylist_42DA70 *list = 0;
    frame_42DA70 *rec;
    float m[16];

    if (begin && (unsigned int)((int)(*(char **)(pose_source + 8) - begin) >> 2) > *(unsigned int *)(s + 0x78))
        list = *(keylist_42DA70 **)(begin + 4 * *(unsigned int *)(s + 0x78));
    if (list->count <= frame)
        frame = 0;
    rec = (frame_42DA70 *)(list->data + list->stride * frame * 0x18);
    sub_005B802C(m, rec->yaw, rec->pitch, rec->roll);
    m[12] = rec->x;
    m[13] = rec->y;
    m[14] = rec->z;
    sub_005B8020(out, m, (float *)d_006C1190);
    return out;
}
