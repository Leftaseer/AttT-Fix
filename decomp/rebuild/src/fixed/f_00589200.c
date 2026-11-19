/* 0x00589200: the TroopIconDragDroper constructor (vtables 0x0061ED2C and, at +0x214, 0x0061ED20): the base at
 * 0x0058A3E0 receives the first two arguments, the object is named "TroopIconDragDroper" (+0x238), the arguments'
 * +0x74 is handed to 0x004AC380 and the third argument (+0x2C0) creates the child object stored at +0x2B8 (0x00587BF0
 * takes it in ECX): its +4 reference count is incremented and the previous child released (deleted through its first
 * vtable slot when the count reaches zero, which the zero stored at +0x2B8 above rules out).  The third argument then
 * updates (vtable +0x50); the child's +0x90 value less this +0x5C is stored at +0x2BC, and the child is told
 * (vtable +0x68) that value plus this +0x5C and half this +0x74 plus this +0x58.  Returns the object. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_0061ED2C[], d_0061ED20[], d_0061ED08[], d_00607CE0[];
DECOMP_C void __thiscall sub_0058A3E0(void *self, void *a, void *b);
DECOMP_C void __thiscall sub_004AC380(void *self, void *a);
DECOMP_C void *__fastcall sub_00587BF0(void *self, unsigned int edx);
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
typedef void (__thiscall *delete_00589200)(void *self, int flags);
typedef void (__thiscall *run_00589200)(void *self);
typedef float (__thiscall *get_00589200)(void *self);
typedef void (__thiscall *set_00589200)(void *self, float a, float b);
#define VT(o) (*(void ***)(o))

DECOMP(00589200)
void *__thiscall f_00589200(void *this, void *arg1, void *arg2, void *arg3)
{
    char *s = this;
    void *child;
    void *old;
    float v;

    sub_0058A3E0(s, arg1, arg2);
    *(void **)s = d_0061ED2C;
    *(void **)(s + 0x214) = d_0061ED20;
    *(unsigned int *)(s + 0x2b8) = 0;
    sub_004AC380(s, (char *)arg1 + 0x74);
    imp_006072F8(s + 0x238, d_0061ED08);
    *(void **)(s + 0x2c0) = arg3;

    child = sub_00587BF0(arg3, 0);
    if (child)
        ++*(unsigned int *)((char *)child + 4);
    old = *(void **)(s + 0x2b8);
    if (old) {
        if (--*(unsigned int *)((char *)old + 4) == 0)
            ((delete_00589200)VT(old)[0])(old, 1);
    }
    *(void **)(s + 0x2b8) = child;

    ((run_00589200)VT(arg3)[0x50 / 4])(arg3);
    v = ((get_00589200)VT(child)[0x90 / 4])(child) - *(float *)(s + 0x5c);
    *(float *)(s + 0x2bc) = v;
    ((set_00589200)VT(child)[0x68 / 4])(child,
        (float)(*(float *)(s + 0x74) * *(double *)d_00607CE0 + *(float *)(s + 0x58)),
        v + *(float *)(s + 0x5c));
    return s;
}
