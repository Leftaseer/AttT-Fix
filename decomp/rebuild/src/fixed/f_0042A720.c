/* CSimpleAnimation's destructor 0x0042A720: the vtable goes back to 0x00608424, an owned driven object (+0x1C4,
 * when the owning flag +0x1E5 is set) is released through slot 0, the name string (+0x1E8) and the CRenderObject3D
 * base (0x004AD020) are destroyed. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP_C char d_00608424[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void __thiscall sub_004AD020(void *self);
typedef void (__thiscall *vf_42A720_release)(void *self, int deleting);

DECOMP(0042A720)
void __thiscall f_0042A720(char *this)
{
    char *driven;

    *(void **)this = d_00608424;
    if (this[0x1e5] && (driven = *(char **)(this + 0x1c4)) != 0) {
        ((vf_42A720_release)(*(void ***)driven)[0])(driven, 1);
        *(void **)(this + 0x1c4) = 0;
    }
    imp_00607330(this + 0x1e8);
    sub_004AD020(this);
}
