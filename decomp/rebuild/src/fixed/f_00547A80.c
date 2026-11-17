/* 0x00547A80: squared x/z distance between two virtual positions; the deltas are rounded to float,
 * while their squares are summed in x87 precision before the float result is stored. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef float *(__thiscall *position_547A80)(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *object, void *throw_info);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C char d_0061B33C[], d_0061B32C[], d_0069916C[];

DECOMP(00547A80)
float __thiscall f_00547A80(void *this, void *other)
{
    float *a, *b;
    volatile float dx, dz, result;
    if (!other) {
        unsigned int msg[7], thrown[7];
        imp_00607324(msg, d_0061B33C);
        sub_00421220(thrown, msg, d_0061B32C, 0x265);
        sub_005E3EC0(thrown, d_0069916C);
        __builtin_unreachable();
    }
    b = ((position_547A80)(*(void ***)other)[0x68 / 4])(other);
    a = ((position_547A80)(*(void ***)this)[0x68 / 4])(this);
    dx = a[0] - b[0];
    dz = a[2] - b[2];
    result = dx * dx + dz * dz;
    return result;
}
