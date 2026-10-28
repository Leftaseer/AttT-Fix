/* 0x004B7E90: ObjectCells<CShadowObject>::~ObjectCells: destroys the cell vector (+0x74: 0x004CE190 on its elements,
 * which takes the first in EAX too, then its memory), the four texture updaters (+0x68, +0x5C, +0x50, +0x44), the
 * list at +0x38 (0x004B6F60, then its head), then the CGameObject base (0x00424E00) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004CE190(void *eax, void *first, void *last, void *alloc, void *tag);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C void __thiscall sub_0044CFE0(void *self);
DECOMP_C void __thiscall sub_004B6F60(void *self);
DECOMP_C void __thiscall sub_00424E00(void *self);
DECOMP_C char d_0061107C[];

DECOMP(004B7E90)
void __thiscall f_004B7E90(void *this)
{
    char *s = (char *)this;
    void **v = (void **)(s + 0x74);
    *(void **)this = d_0061107C;
    if (v[1]) {
        sub_004CE190(v[1], v[1], v[2], v, this);  /* (the last: the dword the original pushed with ECX, unused) */
        sub_005E3E9C(v[1]);
    }
    v[1] = 0;
    v[2] = 0;
    v[3] = 0;
    sub_0044CFE0(s + 0x68);
    sub_0044CFE0(s + 0x5c);
    sub_0044CFE0(s + 0x50);
    sub_0044CFE0(s + 0x44);
    sub_004B6F60(s + 0x38);
    sub_005E3E9C(*(void **)(s + 0x3c));
    *(void **)(s + 0x3c) = 0;
    sub_00424E00(this);
}
