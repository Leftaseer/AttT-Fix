/* 0x00580450: builds the button's alpha mask (+0x2B0, a byte vector: 0x005803C0) from its texture (+0x44):
 * saves the current frame (vf28) as a DDS in memory (D3DXSaveTextureToFileInMemory), loads that back as a
 * system-memory A8R8G8B8 texture of the frame's size (vf10 x vf14, D3DXCreateTextureFromFileInMemoryEx), locks its
 * top level and copies each pixel's alpha byte, one per pixel (the vector holds height * pitch / 4); failed D3DX
 * calls are reported to 0x00458940 with ".\Button.cpp" and the line */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C long __stdcall sub_005B80E6(void **buf, int fmt, void *tex, void *pal);
DECOMP_C long __stdcall sub_005B80AA(void *dev, void *data, unsigned int size, unsigned int w, unsigned int h,
                                     unsigned int mips, unsigned int usage, unsigned int fmt, unsigned int pool,
                                     unsigned int filter, unsigned int mipfilter, unsigned int key, void *info,
                                     void *pal, void **tex);
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void __thiscall sub_005803C0(void *vec, unsigned int n, int a);
DECOMP_C char d_0061DE54[];
DECOMP_C char d_006C8C10[];
typedef void *(__thiscall *vf_580450)(void *self);
typedef unsigned int (__thiscall *dim_580450)(void *self);
typedef unsigned int (__stdcall *com_580450)(void *self);
typedef long (__stdcall *lvl_580450)(void *self, unsigned int level, void **surf);
typedef long (__stdcall *lock_580450)(void *self, void *rect, void *area, unsigned int flags);

#define FRAME(v) (*(void ***)(*(char **)((v) + 0x38) + *(int *)((v) + 0x40) * 4))
#define FRAMEDIM(s, o) ((dim_580450)(*(void ***)FRAME(*(char **)((s) + 0x44)))[(o) / 4])(FRAME(*(char **)((s) + 0x44)))

DECOMP(00580450)
void __thiscall f_00580450(void *this)
{
    char *s = (char *)this;
    void **tex = 0, **buf = 0, **surf;
    struct { unsigned int pitch; unsigned char *bits; } lr;
    void **t = *(void ***)(s + 0x44);
    unsigned int w, h, x, y, sz;
    void *data;
    sub_00458940(sub_005B80E6((void **)&buf, 4, ((vf_580450)(*(void ***)t)[0x28 / 4])(t), 0), d_0061DE54, 0x164);
    h = FRAMEDIM(s, 0x14);
    w = FRAMEDIM(s, 0x10);
    sz = ((com_580450)(*(void ***)buf)[0x10 / 4])(buf);
    data = (void *)(size_t)((com_580450)(*(void ***)buf)[0xc / 4])(buf);
    sub_00458940(sub_005B80AA(*(void **)d_006C8C10, data, sz, w, h, 1, 0, 0x15, 2, 1, 1, 0, 0, 0, (void **)&tex), d_0061DE54,
                 0x16a);
    if (buf) {
        ((com_580450)(*(void ***)buf)[2])(buf);
        buf = 0;
    }
    ((lvl_580450)(*(void ***)tex)[0x48 / 4])(tex, 0, (void **)&surf);
    ((lock_580450)(*(void ***)surf)[0x34 / 4])(surf, &lr, 0, 0);
    sub_005803C0(s + 0x2b0, FRAMEDIM(s, 0x14) * lr.pitch >> 2, 0);
    for (x = 0; x < lr.pitch >> 2; x++)
        if (FRAMEDIM(s, 0x14)) {
            y = 0;
            do {
                (*(unsigned char **)(s + 0x2b4))[(y * lr.pitch >> 2) + x] = lr.bits[y * lr.pitch + x * 4 + 3];
                y++;
            } while (y < FRAMEDIM(s, 0x14));
        }
    ((com_580450)(*(void ***)surf)[0x38 / 4])(surf);
    if (surf)
        ((com_580450)(*(void ***)surf)[2])(surf);
    if (tex)
        ((com_580450)(*(void ***)tex)[2])(tex);
}
