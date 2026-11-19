/* 0x004CAA00: initialises a textured sprite (this+0 is the FVF 0x144, this+4 the vertex buffer, this+8 the
 * D3D device).  A 0xA8-byte managed write-only vertex buffer of 6 vertices with the 0x144 FVF is created through
 * device slot 0x68 and its HRESULT reported (0x00458940 with ".\Sprite.cpp" and line 0x11).  The buffer is locked
 * (slot 0x2C, everything from offset 0, into a pointer) and every 0x1C-byte vertex gets an opaque colour and the
 * texture coordinates of two triangles ((0,0) (1,0) (1,1), (0,1) (0,0) (1,1)); it is unlocked again (slot 0x30)
 * and the rectangle writer puts the quad at 0, 0 with the width and height from 0x00608B4C (100).  Finally the
 * sprite named "Movie" is looked up in the manager at 0x006C8714 (0x00448F10) and stored at +0x14.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef struct { float x, y, z, w; unsigned int color; float u, v; } Vert_4CAA00;   /* 0x1c bytes */
typedef int (__stdcall *create_vb_4CAA00)(void *device, unsigned int length, unsigned int usage,
                                          unsigned int fvf, unsigned int pool, void **buffer, void *shared);
typedef int (__stdcall *lock_4CAA00)(void *buffer, unsigned int offset, unsigned int size, void **data,
                                     unsigned int flags);
typedef int (__stdcall *unlock_4CAA00)(void *buffer);

DECOMP_C void __cdecl sub_00458940(int hr, const char *file, int line);
DECOMP_C void *__thiscall sub_00448F10(void *self, const void *name);
DECOMP_C void __thiscall sub_004CA820(void *self, float x, float y, float w, float h);
DECOMP_C char d_00611CCC[], d_00611CD4[], d_0068AE40[], d_00608B4C[], d_006C8714[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(004CAA00)
void *__thiscall f_004CAA00(char *this, void *device)
{
    unsigned int name[7];
    Vert_4CAA00 *v;
    void *buffer, **vt;
    void *data = 0;
    float one;
    int hr;

    *(unsigned int *)this = 0x144;
    *(void **)(this + 8) = device;
    this[0x10] = 0;
    vt = *(void ***)device;
    hr = ((create_vb_4CAA00)vt[0x68 / 4])(device, 0xa8, 8, 0x144, 1, (void **)(this + 4), 0);
    sub_00458940(hr, d_00611CD4, 0x11);

    buffer = *(void **)(this + 4);
    vt = *(void ***)buffer;
    ((lock_4CAA00)vt[0x2c / 4])(buffer, 0, 0, &data, 0);
    one = *(float *)d_0068AE40;
    v = (Vert_4CAA00 *)data;
    v[0].u = 0.0f; v[0].v = 0.0f;
    v[1].u = one;  v[1].v = 0.0f;
    v[2].u = one;  v[2].v = one;
    v[3].u = 0.0f; v[3].v = one;
    v[4].u = 0.0f; v[4].v = 0.0f;
    v[5].u = one;  v[5].v = one;
    v[0].color = v[1].color = v[2].color = v[3].color = v[4].color = v[5].color = 0xffffffffu;
    ((unlock_4CAA00)vt[0x30 / 4])(buffer);

    sub_004CA820(this, 0.0f, 0.0f, *(float *)d_00608B4C, *(float *)d_00608B4C);

    imp_00607324(name, d_00611CCC);
    *(void **)(this + 0x14) = sub_00448F10(*(void **)d_006C8714, name);
    imp_00607330(name);
    return this;
}
