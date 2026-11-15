/* 0x00429B40: AmbientSoundManager::~AmbientSoundManager: the three vtables 0x006083E0/0x006083D8/0x006083D0, the
 * sound object at +0x40 freed (virtual destructor, arg 1) and cleared, every record of the map at +0x88 destroyed
 * (elements of the vector at node+0x20 and the object at node+0x18 through their virtual destructors), the two lists
 * at +0xA8 and +0x9C freed node by node with their heads, the tree erased (0x00429920) and its head freed (+0x8C/90
 * cleared), the reader at +0x44 closed (0x00458B20), the vtable 0x00607D5C, the child notified (+0x2C, vtable +0x14),
 * the name string at +8 destroyed and the CGameObject base destroyed (0x00424C70). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_006083E0[], d_006083D8[], d_006083D0[], d_00607D5C[], d_00608250[];
DECOMP_C unsigned int __thiscall sub_00427350(void *self);
DECOMP_C void __thiscall sub_00427720(void *self);
DECOMP_C void __thiscall sub_00429920(void *self, char **out, char *first, char *last);
DECOMP_C void __thiscall sub_00458B20(void *self);
DECOMP_C void __thiscall sub_00424C70(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                        /* operator delete */
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00429B40)
void __thiscall f_00429B40(char *this)
{
    char *s = this, *head, *first, *nxt, *obj;

    *(void **)s = d_006083E0;
    *(void **)(s + 0x38) = d_006083D8;
    *(void **)(s + 0x3c) = d_006083D0;
    obj = *(char **)(s + 0x40);
    if (obj != 0)
        (*(void (__thiscall **)(char *, int))*(void **)obj)(obj, 1);
    head = *(char **)(s + 0x8c);
    *(void **)(s + 0x40) = 0;
    first = *(char **)head;
    while (first != head) {
        char *vec = first + 0x20;
        unsigned int i;
        if (sub_00427350(vec) != 0) {
            for (i = 0; i < sub_00427350(vec); i++) {
                obj = *(char **)(*(char **)(vec + 4) + i * 0xc);
                if (obj != 0)
                    (*(void (__thiscall **)(char *, int))*(void **)obj)(obj, 1);
            }
        }
        obj = *(char **)(first + 0x18);
        if (obj != 0)
            (*(void (__thiscall **)(char *, int))*(void **)obj)(obj, 1);
        {
            char *next = first;
            sub_00427720(&next);
            first = next;
        }
    }
    head = *(char **)(s + 0xa8);
    first = *(char **)head;
    *(char **)head = head;
    *(char **)(head + 4) = head;
    *(unsigned int *)(s + 0xac) = 0;
    while (first != head) {
        nxt = *(char **)first;
        sub_005E3E9C(first);
        first = nxt;
    }
    sub_005E3E9C(head);
    *(void **)(s + 0xa8) = 0;
    head = *(char **)(s + 0x9c);
    first = *(char **)head;
    *(char **)head = head;
    *(char **)(head + 4) = head;
    *(unsigned int *)(s + 0xa0) = 0;
    while (first != head) {
        nxt = *(char **)first;
        sub_005E3E9C(first);
        first = nxt;
    }
    sub_005E3E9C(head);
    *(void **)(s + 0x9c) = 0;
    {
        char *out;
        head = *(char **)(s + 0x8c);
        sub_00429920(s + 0x88, &out, *(char **)head, head);
    }
    sub_005E3E9C(*(void **)(s + 0x8c));
    *(void **)(s + 0x8c) = 0;
    *(void **)(s + 0x90) = 0;
    sub_00458B20(s + 0x44);
    *(void **)(s + 0x38) = d_00608250;
    *(void **)s = d_00607D5C;
    obj = *(char **)(s + 0x2c);
    if (obj != 0)
        (*(void (__thiscall **)(char *, char *))(*(void **)obj + 0x14))(obj, s);
    imp_00607330(s + 8);
    sub_00424C70(s);
}
