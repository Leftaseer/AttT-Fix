/* 0x00555690: NForest::Forest::Forest: the CRenderObject3D base (0x004AB9C0 with an empty name), its updater at +0x58
 * (0x004B8640(1)), the vtables, empty vectors (+0x68, +0x78, +0xD8, +0xE8) and maps (+0x84, +0xAC: 0x004BE3C0; +0xF4:
 * 0x005549F0), flags (+0x11C, +0x11D) and the scale +0x12C (0x60A2A4); then a 0x4260-byte loader on the stack
 * (0x0055A4A0, 0x0055B850, ~0x0055A500) around 0x004B8630, 0x00554740 and 0x005552D0 (the original's unwinding on
 * an exception is not reproduced) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AB9C0(void *self, void *name, int a);
DECOMP_C void __thiscall sub_004B8640(void *self, int a);
DECOMP_C void __thiscall sub_004BE3C0(void *self, void *cmp, void *alloc);
DECOMP_C void __thiscall sub_005549F0(void *self, void *cmp, void *alloc);
DECOMP_C void __thiscall sub_0055A4A0(void *self);
DECOMP_C void __thiscall sub_0055B850(void *self);
DECOMP_C void __thiscall sub_0055A500(void *self);
DECOMP_C void __stdcall sub_004B8630(void *a);
DECOMP_C void __thiscall sub_00554740(void *self);
DECOMP_C void __thiscall sub_005552D0(void *self);
DECOMP_C char d_0060FA8B[], d_0060B900[], d_0061BCBC[], d_0061BCB0[], d_0061BCA4[], d_0060A2A4[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00555690)
void *__thiscall f_00555690(void *this)
{
    char *s = (char *)this;
    unsigned int name[7];
    unsigned char dummy;
    unsigned int loader[0x4260 / 4];
    imp_00607324(name, d_0060FA8B);
    sub_004AB9C0(this, name, 0);
    imp_00607330(name);
    sub_004B8640(s + 0x58, 1);
    *(void **)(s + 0x60) = d_0060B900;
    *(void **)s = d_0061BCBC;
    *(void **)(s + 0x58) = d_0061BCB0;
    *(void **)(s + 0x60) = d_0061BCA4;
    *(unsigned int *)(s + 0x68) = 0;
    *(unsigned int *)(s + 0x6c) = 0;
    *(unsigned int *)(s + 0x70) = 0;
    *(unsigned int *)(s + 0x78) = 0;
    *(unsigned int *)(s + 0x7c) = 0;
    *(unsigned int *)(s + 0x80) = 0;
    sub_004BE3C0(s + 0x84, &dummy, &dummy);
    sub_004BE3C0(s + 0xac, &dummy, &dummy);
    *(unsigned int *)(s + 0xd8) = 0;
    *(unsigned int *)(s + 0xdc) = 0;
    *(unsigned int *)(s + 0xe0) = 0;
    *(unsigned int *)(s + 0xe8) = 0;
    *(unsigned int *)(s + 0xec) = 0;
    *(unsigned int *)(s + 0xf0) = 0;
    sub_005549F0(s + 0xf4, &dummy, &dummy);
    s[0x11c] = 0;
    s[0x11d] = 0;
    *(unsigned int *)(s + 0x12c) = *(unsigned int *)d_0060A2A4;
    sub_0055A4A0(loader);
    sub_0055B850(loader);
    sub_004B8630(s + 0x58);
    sub_00554740(this);
    sub_005552D0(this);
    sub_0055A500(loader);
    return this;
}
