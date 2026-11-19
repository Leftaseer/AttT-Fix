/* 0x004888E0: copies the container's 12-byte elements into the geometry locked at +0x1CC.  The element count
 * (0x00427350) must be half the +0x1C8 value plus one, else an assertion string (0x0060F900, file 0x0060F8EC,
 * line 0x5B) is thrown (0x00421220 / 0x005E3EC0 with 0x0069916C).  The mesh is locked through its table slot
 * 0x2C (offset 0, nothing to lock, into a pointer, no flags) and unlocked through slot 0x30.  With more than one
 * element, each iteration writes element i (counted again every step) at the running pointer and element i+1 at
 * pointer + 0x10, then advances the pointer by 0x20. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef void (__stdcall *lock_4888E0)(void *self, int offset, int size, void **data, int flags);
typedef void (__stdcall *unlock_4888E0)(void *self);

DECOMP_C int __thiscall sub_00427350(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *object, void *throw_info);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C char d_0060F900[], d_0060F8EC[], d_0069916C[];

DECOMP(004888E0)
void __thiscall f_004888E0(void *this, void *container)
{
    char *s = (char *)this;
    void *data = 0, **vt, *mesh;
    int count;

    count = sub_00427350(container);
    if (count * 2 - 2 != *(int *)(s + 0x1c8)) {
        unsigned int message[7], thrown[7];
        imp_00607324(message, d_0060F900);
        sub_00421220(thrown, message, d_0060F8EC, 0x5b);
        sub_005E3EC0(thrown, d_0069916C);
    }
    mesh = *(void **)(s + 0x1cc);
    vt = *(void ***)mesh;
    ((lock_4888E0)vt[0x2c / 4])(mesh, 0, 0, &data, 0);
    if (sub_00427350(container) != 1) {
        char *p = (char *)data;
        unsigned int i = 0;
        do {
            char *src = *(char **)((char *)container + 4) + i * 0xc;
            __builtin_memcpy(p, src, 0xc);
            p += 0x10;
            __builtin_memcpy(p, src + 0xc, 0xc);
            p += 0x10;
            i++;
        } while (i < (unsigned int)(sub_00427350(container) - 1));
    }
    ((unlock_4888E0)vt[0x30 / 4])(mesh);
}
