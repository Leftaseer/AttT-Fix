/* 0x004BA7F0: the vertex buffer at +0xEC (0x004BA550) gets a record built by slot 0x2C of its vtable (the record
 * slot's address in ECX and as the fifth argument, a 0x2000-byte limit) and asks slot 0x30 to finish it; the span at
 * +0xD8 (+0xDC..+0xE0, 32-byte vertices) is then appended to the record as far as whole vertices go, and the finish
 * slot's result is returned.  Called by the skeleton mesh draws (0x004BA850, 0x004BAB70). */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void **__thiscall sub_004BA550(void *self);
DECOMP_C void __cdecl sub_00576360(void *dst, const void *src, unsigned int count);
typedef int (__thiscall *vf_4BA7F0_begin)(void **self, void *object, int zero, int zero2, void **out, int limit);
typedef int (__stdcall *vf_4BA7F0_end)(void *object);

DECOMP(004BA7F0)
int __thiscall f_004BA7F0(void *this, char *span)
{
    void *object = *sub_004BA550((char *)this + 0xec);
    void *vtable = *(void **)object;
    void *out = this;

    ((vf_4BA7F0_begin)(((void **)vtable)[0x2c / 4]))(&out, object, 0, 0, &out, 0x2000);
    unsigned int begin = *(unsigned int *)(span + 4);
    sub_00576360(out, (void *)begin, begin ? ((*(unsigned int *)(span + 8) - begin) >> 5) << 5 : 0);
    vtable = *(void **)object;
    return ((vf_4BA7F0_end)(((void **)vtable)[0x30 / 4]))(object);
}
