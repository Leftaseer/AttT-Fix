/* 0x004301F0: the back buffer texture's init: a second initialisation throws "Нельзя дважды инициализировать
 * CBackBufferTexture" (the string at 0x00608FE8 copied through 0x00607324 / 0x00607334 and 0x005E3EC0 with the
 * throw info at 0x0069916C).  Otherwise the 0x54-byte render texture is allocated (0x005E3EAE) and built by
 * 0x004DF860 from half of the screen (0x006C8964 x 0x006C8960), one level, format 0x15 and no pool, then stored at
 * +4; its virtual +0x2C yields a surface a0 whose routine [a0]+0x48 is called with (a0, 0, this+0xC).  Finally
 * D3DXCreateRenderToSurface (0x005B8050) creates the render surface at +8 on the device 0x006C8C10 with the same
 * size, format 0x15, depth-stencil on and the depth-stencil format from the data root (+0x5C, 0x00427990); its
 * result is returned. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void *__thiscall sub_004DF860(void *self, unsigned int w, unsigned int h, unsigned int levels,
                                       unsigned int a, unsigned int usage, unsigned int pool);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C int __stdcall sub_005B8050(void *dev, unsigned int w, unsigned int h, unsigned int fmt, int depth,
                                    unsigned int dfmt, void **out);      /* D3DXCreateRenderToSurface */
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C char d_00608FE8[], d_0069916C[], d_006C8960[], d_006C8964[], d_006C8C10[];

DECOMP(004301F0)
int __thiscall f_004301F0(void *self)
{
    char *s = (char *)self;
    void *tex, *a0;
    if (*(void **)(s + 4)) {
        unsigned int msg[7], thrown[7];
        imp_00607324(msg, d_00608FE8);
        imp_00607334(thrown, msg);
        sub_005E3EC0(thrown, d_0069916C);
    }
    tex = sub_005E3EAE(0x54);
    tex = tex ? sub_004DF860(tex, *(unsigned int *)d_006C8964 >> 1, *(unsigned int *)d_006C8960 >> 1,
                             1, 1, 0x15, 0) : 0;
    *(void **)(s + 4) = tex;
    a0 = (*(void *(__thiscall **)(void *))(*(char **)tex + 0x2c))(tex);
    (*(void (__stdcall **)(void *, int, void *))(*(char **)a0 + 0x48))(a0, 0, s + 0xc);
    return sub_005B8050(*(void **)d_006C8C10,
                        *(unsigned int *)d_006C8964 >> 1, *(unsigned int *)d_006C8960 >> 1,
                        0x15, 1, *(unsigned int *)(sub_00427990() + 0x5c), (void **)(s + 8));
}
