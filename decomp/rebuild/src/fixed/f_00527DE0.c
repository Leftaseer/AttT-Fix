/* 0x00527DE0: reads the settings (the config at +0x3C): "sName" into the string at +8 (vf38), "dwLevel" (+0x264),
 * "fCloudsSpeed" (+0x260, vf34), "dwShadowTexSize" (+0x2D4), "dwVertexBufferSize" (+0x2D8), "dwIndexBufferSize"
 * (+0x2DC) (vf30) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00614F68[], d_00614F60[], d_00614D94[], d_00614F50[], d_00614F3C[], d_00614F28[];
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
typedef void (__thiscall *get_527DE0)(void *cfg, const char *key, void *out);

#define GET(slot, key, out) do { void **c_ = *(void ***)(s + 0x3c); \
    ((get_527DE0)(*(void ***)c_)[(slot) / 4])(c_, key, out); } while (0)

DECOMP(00527DE0)
void __thiscall f_00527DE0(void *this)
{
    char *s = (char *)this;
    const char *name = (const char *)this;        /* (the slot as the original leaves it until vf38 sets it) */
    GET(0x38, d_00614F68, &name);
    imp_006072F8(s + 8, name);
    GET(0x30, d_00614F60, s + 0x264);
    GET(0x34, d_00614D94, s + 0x260);
    GET(0x30, d_00614F50, s + 0x2d4);
    GET(0x30, d_00614F3C, s + 0x2d8);
    GET(0x30, d_00614F28, s + 0x2dc);
}
