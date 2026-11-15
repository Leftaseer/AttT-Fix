/* 0x005AD210: gives the sound manager (called on the global 0x006C88D8) the sound object arg 1: the stream it holds
 * (+0x68) is released (0x00591B80 with 1, then the global 0x006C8E70's manager 0x005A2410 with 1, 0) and the object's
 * +0x1A8 stream takes its place, started (0x00591AF0 with 1).  Without an object the stream is dropped and the item
 * 4 of kind 0x13F in the global's manager (0x00594600) plays its entry 0 (0x00595030).  Its result is returned. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_006C8E70[];
DECOMP_C void __thiscall sub_00591B80(void *self, int resume);
DECOMP_C void __thiscall sub_005A2410(void *self, int a, int b);
DECOMP_C void *__thiscall sub_00591AF0(void *self, int start);
DECOMP_C void *__thiscall sub_00594600(void *self, int kind, int index);
DECOMP_C void *__thiscall sub_00595030(void *self, int entry);

DECOMP(005AD210)
void *__thiscall f_005AD210(void *self, void *obj)
{
    char *c = (char *)self;

    if (*(void **)(c + 0x68)) {
        sub_00591B80(*(void **)(c + 0x68), 1);
        sub_005A2410(*(void **)d_006C8E70, 1, 0);
    }
    if (obj) {
        *(void **)(c + 0x68) = *(void **)((char *)obj + 0x1a8);
        return sub_00591AF0(*(void **)(c + 0x68), 1);
    }
    *(void **)(c + 0x68) = 0;
    return sub_00595030(sub_00594600(*(void **)d_006C8E70, 0x13f, 4), 0);
}
