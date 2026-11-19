/* 0x004CA820: the rectangle vertex writer: [this+4] is a vertex buffer whose slot 0x2C locks the vertices (offset 0,
 * all of them, into a pointer this initialises to 0 and passes; the result is not checked) and slot 0x30 unlocks it
 * again.  The vertices are six 0x1C-byte records of two floats of x/y, then 0.01 (0x0060984C) and 1 (0x0068AE40):
 * (x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y) and (x + w, y + h), the two triangles of the rectangle at
 * x, y of the width w and the height h (the sums are x87 single-precision adds).  The other three fields of a record
 * are left alone.  Returns nothing (the unlock's result stays in EAX). */
/* @conv ECX 16 */
#include "auto_pre.h"
DECOMP_C char d_0060984C[], d_0068AE40[];
typedef struct { float x, y, z, w; unsigned int pad[3]; } Vert_4CA820;   /* 0x1c bytes */
typedef int (__stdcall *lock_4CA820)(void *buf, unsigned int offset, unsigned int size, void **data, unsigned int flags);
typedef int (__stdcall *unlock_4CA820)(void *buf);

DECOMP(004CA820)
void __thiscall f_004CA820(void *self, float x, float y, float w, float h)
{
    void *buf = *(void **)((char *)self + 4);
    void **vt = *(void ***)buf;
    void *data = 0;
    Vert_4CA820 *v;
    float right, bottom;

    ((lock_4CA820)vt[0x2c / 4])(buf, 0, 0, &data, 0);
    right = x + w;
    bottom = y + h;
    v = (Vert_4CA820 *)data;
    v[0].x = x;     v[0].y = y;      v[0].z = *(float *)d_0060984C; v[0].w = *(float *)d_0068AE40;
    v[1].x = right; v[1].y = y;      v[1].z = *(float *)d_0060984C; v[1].w = *(float *)d_0068AE40;
    v[2].x = right; v[2].y = bottom; v[2].z = *(float *)d_0060984C; v[2].w = *(float *)d_0068AE40;
    v[3].x = x;     v[3].y = bottom; v[3].z = *(float *)d_0060984C; v[3].w = *(float *)d_0068AE40;
    v[4].x = x;     v[4].y = y;      v[4].z = *(float *)d_0060984C; v[4].w = *(float *)d_0068AE40;
    v[5].x = right; v[5].y = bottom; v[5].z = *(float *)d_0060984C; v[5].w = *(float *)d_0068AE40;
    ((unlock_4CA820)vt[0x30 / 4])(buf);
}
