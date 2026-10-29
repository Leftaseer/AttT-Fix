/* 0x004E0750: CTextureNode::Create: the texture (+0x60) of size +0x68 x +0x6C, +0x70 levels, format +0x74 and pool
 * +0x7C. A render target (usage +0x78 is 1) logs, for the node "uniqueTexture4", its name and "CTextureNode::Create"
 * (0x0042F050 / 0x0054B510, an empty stub in this build) and, when that fails, retries as a plain texture,
 * throwing the std::string made by 0x00421220 from "Невозможно создать RenderTarget текстуру" (cannot create a
 * render target texture) if that fails too; other usages are created as given. Failures are reported to 0x00458940
 * with ".\TextureNode.cpp" */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__cdecl sub_0042F050(void);
DECOMP_C void __cdecl sub_0054B510(void *eax, void *msg, int a);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char d_006C8C10[], d_006125BC[], d_00612634[], d_00612630[], d_00612618[], d_006125EC[], d_0069916C[];
DECOMP_C int (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
typedef long (__stdcall *tex_4E0750)(void *dev, unsigned int w, unsigned int h, unsigned int levels,
                                     unsigned int usage, unsigned int fmt, unsigned int pool, void *out, void *h2);

#define U(o) (*(unsigned int *)(s + (o)))
#define DEV (*(void ***)d_006C8C10)
#define CREATE(usage) ((tex_4E0750)(*(void ***)DEV)[0x5c / 4])(DEV, U(0x68), U(0x6c), U(0x70), usage, U(0x74), \
                                                                U(0x7c), s + 0x60, 0)

DECOMP(004E0750)
void __thiscall f_004E0750(void *this)
{
    char *s = (char *)this;
    long hr;
    if (U(0x78) != 1) {
        sub_00458940(CREATE(U(0x78)), d_006125BC, 0x155);
        return;
    }
    hr = CREATE(1);
    sub_00458940(hr, d_006125BC, 0x139);
    if ((char)imp_006071E4(s + 0x30, d_00612634)) {
        unsigned int msg[7], a[7], b[7], c[7], m2[7];
        void *e;
        sub_0042F050();
        imp_006071E0(msg);
        imp_006071DC(c, imp_006071DC(b, imp_006071C0(a, msg, s + 0x30), d_00612630), d_00612618);
        imp_0060731C(msg, c);
        imp_00607330(c);
        imp_00607330(b);
        imp_00607330(a);
        e = imp_00607324(m2, imp_0060732C(msg));
        sub_0054B510(e, m2, 1);
        imp_00607330(m2);
        imp_00607330(msg);
    }
    if (hr >= 0)
        return;
    hr = CREATE(0);
    sub_00458940(hr, d_006125BC, 0x147);
    if (hr < 0) {
        unsigned int text[7], thrown[7];
        imp_00607324(text, d_006125EC);
        sub_00421220(thrown, text, d_006125BC, 0x14c);
        sub_005E3EC0(thrown, d_0069916C);
    }
}
