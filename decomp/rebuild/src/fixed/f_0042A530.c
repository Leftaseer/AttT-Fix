/* CSimpleAnimation's constructor 0x0042A530 (ret 12): the CRenderObject3D base with the given name (0x004AD180),
 * vtable 0x00608424, an empty name string at +0x1E8 and everything before the last ';' of that name cut off.  The
 * driven object (+0x1C4) is marked as not animating and its key count (slot 0xE0) and key vector (slot 0xE4) are
 * taken; the start index comes from the source's +0x1C, the end index from its +0x20 clamped to the last key.  The
 * current index and the driven object's index start there, and the key's height difference (the two keys' z at +8)
 * is negated into +0x1E0.  Returns this. */
/* @conv ECX 12 */
#include "auto_pre.h"

DECOMP_C char d_00608424[];
DECOMP_C unsigned int *imp_006071C4 __asm__("__imp_?npos@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@2IB");
DECOMP_C unsigned int (__thiscall *imp_006071C8)(const void *, char, unsigned int) __asm__("__imp_?rfind@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEIDI@Z");
DECOMP_C void *(__thiscall *imp_006071CC)(void *, void *, unsigned int, unsigned int) __asm__("__imp_?substr@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBE?AV12@II@Z");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
typedef unsigned int (__thiscall *vf_42A530_keys)(void *self);

DECOMP(0042A530)
void *__thiscall f_0042A530(char *this, char *source, char *driven, unsigned int owning)
{
    unsigned int name[7], pos, end;
    char *keys;
    float first, last;

    sub_004AD180(this, source, 0, 0);
    *(void **)this = d_00608424;
    imp_006071E0(this + 0x1e8);
    pos = imp_006071C8(this + 8, ';', *imp_006071C4);
    if (pos != *imp_006071C4) {
        imp_006071CC(this + 8, name, pos + 1, *(unsigned int *)(this + 0x1c));
        imp_0060731C(this + 8, name);
        imp_00607330(name);
    }
    *(char **)(this + 0x1c4) = driven;
    driven[0x1d4] = 0;
    this[0x1e5] = (char)owning;
    *(unsigned int *)(this + 0x1c8) = ((vf_42A530_keys)(*(void ***)driven)[0xe0 / 4])(driven);
    *(unsigned int *)(this + 0x1d8) = ((vf_42A530_keys)(*(void ***)driven)[0xe4 / 4])(driven);
    *(unsigned int *)(this + 0x1d0) = *(unsigned int *)(source + 0x1c);
    end = *(unsigned int *)(source + 0x20);
    *(unsigned int *)(this + 0x1d4) = end;
    if (*(unsigned int *)(this + 0x1c8) <= end)
        *(unsigned int *)(this + 0x1d4) = *(unsigned int *)(this + 0x1c8) - 1;
    *(unsigned int *)(this + 0x1cc) = *(unsigned int *)(this + 0x1d0);
    *(unsigned int *)(driven + 0x1d8) = *(unsigned int *)(this + 0x1d0);
    this[0x1dc] = 0;
    keys = *(char **)(this + 0x1d8);
    first = *(float *)(keys + 8 + *(unsigned int *)(this + 0x1d4) * 0xc);
    last = *(float *)(keys + 8 + *(unsigned int *)(this + 0x1d0) * 0xc);
    this[0x1e4] = 0;
    *(float *)(this + 0x1e0) = -(first - last);
    return this;
}
