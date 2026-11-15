/* 0x004299E0: AmbientSoundManager::Load: releases the sound object at +0x40 (virtual destructor with arg 1) and
 * clears it, destroys every map record at +0x88 (each freed element of the vector at node+0x20 through its virtual
 * destructor, then the object at node+0x18), frees the tree and resets the head (+0x8C, count +0x90 = 0), clears the
 * cell containers at +0x98 (0x00427C70), zeroes +0x74, stores the given position at +0x78/+0x7C, loads the named
 * sound (0x00429440) and clears +0x40 again. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C unsigned int __thiscall sub_00427350(void *self);
DECOMP_C void __thiscall sub_00427720(void *self);
DECOMP_C void __thiscall sub_004293F0(void *self, char *node);
DECOMP_C void __thiscall sub_00427C70(void *self);
DECOMP_C void __thiscall sub_00429440(void *self, void *name);

DECOMP(004299E0)
void __thiscall f_004299E0(char *this, const float *pos, void *name)
{
    char *head, *it, *vec, *obj;
    unsigned int i;

    obj = *(char **)(this + 0x40);
    if (obj != 0)
        (*(void (__thiscall **)(char *, int))*(void **)obj)(obj, 1);
    head = *(char **)(this + 0x8c);
    *(void **)(this + 0x40) = 0;
    it = *(char **)head;
    while (it != head) {
        vec = it + 0x20;
        if (sub_00427350(vec) != 0) {
            for (i = 0; i < sub_00427350(vec); i++) {
                obj = *(char **)(*(char **)(vec + 4) + i * 0xc);
                if (obj != 0)
                    (*(void (__thiscall **)(char *, int))*(void **)obj)(obj, 1);
            }
        }
        obj = *(char **)(it + 0x18);
        if (obj != 0)
            (*(void (__thiscall **)(char *, int))*(void **)obj)(obj, 1);
        {
            char *next = it;
            sub_00427720(&next);
            it = next;
        }
    }
    sub_004293F0(this + 0x88, *(char **)(*(char **)(this + 0x8c) + 4));
    *(char **)(*(char **)(this + 0x8c) + 4) = *(char **)(this + 0x8c);
    *(unsigned int *)(this + 0x90) = 0;
    *(char **)*(char **)(this + 0x8c) = *(char **)(this + 0x8c);
    *(char **)(*(char **)(this + 0x8c) + 8) = *(char **)(this + 0x8c);
    sub_00427C70(this + 0x98);
    *(unsigned int *)(this + 0x74) = 0;
    *(float *)(this + 0x78) = pos[0];
    *(float *)(this + 0x7c) = pos[1];
    sub_00429440(this, name);
    *(void **)(this + 0x40) = 0;
}
