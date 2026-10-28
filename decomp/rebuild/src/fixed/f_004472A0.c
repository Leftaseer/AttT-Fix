/* 0x004472A0: CDistanceTransparency::Update: the base update (0x00424D90, which takes EAX as it came), then for
 * every child in the list at +0x3C sets the "dwTFactor" of its settings (vf30, then vf44) to the alpha of 0x00446F60
 * in the top byte; returns what the last vf44 returned (the list head when the list is empty) */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 004472A0 custom */
DECOMP_C unsigned int __cdecl sub_00424D90(void *self, unsigned int eax, float dt);
DECOMP_C unsigned char __thiscall sub_00446F60(void *child);
DECOMP_C char d_0060A708[];
typedef void *(__thiscall *vf30_4472A0)(void *self);
typedef unsigned int (__thiscall *vf44_4472A0)(void *self, const char *name, unsigned int v);

DECOMP(004472A0)
unsigned int __cdecl f_004472A0(void *this, unsigned int eax, float dt)
{
    char **head, **node;
    unsigned int r;
    sub_00424D90(this, eax, dt);
    head = *(char ***)((char *)this + 0x3c);
    r = (unsigned int)head;
    for (node = (char **)*head; node != head; node = (char **)*node) {
        void **child = (void **)node[2];
        void **cfg = ((vf30_4472A0)(*(void ***)child)[0x30 / 4])(child);
        vf44_4472A0 set = (vf44_4472A0)(*(void ***)cfg)[0x44 / 4];
        r = set(cfg, d_0060A708, (unsigned int)sub_00446F60(node + 2) << 24);
    }
    return r;
}
