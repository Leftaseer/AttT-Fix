/* 0x004CD190: StaticObjectManager::vf7: clears the renderer (+0xD8, vf18), copies the objects 0x004CD030 collects
 * (+0x38) into a local list and adds each to the renderer (vf0C); returns the renderer's +0x18 (NULL without one) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int alloc; void **head; unsigned int size; } List_4CD190;
DECOMP_C void **__cdecl sub_004C2F40(void);
DECOMP_C List_4CD190 *__thiscall sub_004CD030(void *self, void *out);
DECOMP_C void __thiscall sub_004CCD30(List_4CD190 *self, void *first, void *last, unsigned int tag);
DECOMP_C void __thiscall sub_0044CFE0(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
typedef void (__thiscall *vf_4CD190)(void *self);
typedef void (__thiscall *vf1_4CD190)(void *self, void *o);

DECOMP(004CD190)
void *__thiscall f_004CD190(void *this)
{
    char *s = (char *)this;
    unsigned int tag = 0;                       /* (the dword the original passes unset) */
    List_4CD190 l;
    unsigned int tmp[4];
    List_4CD190 *r;
    void **n, **head;
    void **rd = *(void ***)(s + 0xd8);
    ((vf_4CD190)(*(void ***)rd)[0x18 / 4])(rd);
    l.head = sub_004C2F40();
    l.size = 0;
    r = sub_004CD030(s + 0x38, tmp);
    if (&l != r)
        sub_004CCD30(&l, *r->head, r->head, tag);
    sub_0044CFE0(tmp);
    head = l.head;
    for (n = (void **)*head; n != head; n = (void **)*n) {
        rd = *(void ***)(s + 0xd8);
        ((vf1_4CD190)(*(void ***)rd)[0xc / 4])(rd, n[2]);
    }
    rd = *(void ***)(s + 0xd8);
    n = (void **)*head;
    head[0] = head;
    head[1] = head;
    while (n != head) {
        void **next = (void **)*n;
        sub_005E3E9C(n);
        n = next;
    }
    sub_005E3E9C(head);
    return rd ? (char *)rd + 0x18 : 0;
}
