/* 0x004302F0: while the render surface at +8 is missing, creates it with D3DXCreateRenderToSurface (0x005B8050):
 * the device 0x006C8C10, half of the screen (0x006C8964 x 0x006C8960), format 0x15, depth-stencil on, the
 * depth-stencil format from the data root (+0x5C), into +8; then the virtual at +0x2C of the object at +4 yields a
 * surface a0, whose routine at [a0]+0x48 is called with (a0, 0, this+0xC). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C int __stdcall sub_005B8050(void *dev, unsigned int w, unsigned int h, unsigned int fmt, int depth,
                                    unsigned int dfmt, void **out);      /* D3DXCreateRenderToSurface */
DECOMP_C char d_006C8960[], d_006C8964[], d_006C8C10[];

DECOMP(004302F0)
void __thiscall f_004302F0(void *self)
{
    char *s = (char *)self;
    char *root = sub_00427990();
    void *ctx, *a0;
    if (*(void **)(s + 8))
        return;
    sub_005B8050(*(void **)d_006C8C10, *(unsigned int *)d_006C8964 >> 1, *(unsigned int *)d_006C8960 >> 1,
                 0x15, 1, *(unsigned int *)(root + 0x5c), (void **)(s + 8));
    ctx = *(void **)(s + 4);
    a0 = (*(void *(__thiscall **)(void *))(*(char **)ctx + 0x2c))(ctx);
    (*(void (__stdcall **)(void *, int, void *))(*(char **)a0 + 0x48))(a0, 0, s + 0xc);
}
