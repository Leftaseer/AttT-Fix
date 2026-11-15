/* 0x00428E00: std::map::_Insert for the ambient sound tree held at +4: when the count at +8 would pass 0x71C71C5
 * it throws std::length_error ("map/set<T> too long", vtable 0x00607B24, throw info 0x00699050); otherwise it
 * builds a node with 0x00428D40, links it as the root or under arg 3 (on its +0 or +8 side per arg 2), red-black
 * rebalances with the rotations 0x00427610 / 0x00427660, blacks the root and returns the iterator written to arg 1
 * (the colour is the byte +0x30, the head's nil flag +0x31). */
/* @conv ECX 16 */
#include "auto_pre.h"
DECOMP_C void *__stdcall sub_00428D40(unsigned int a, unsigned int b, unsigned int c, char *rec,
                                      unsigned char flag);
DECOMP_C void __thiscall sub_00427610(void *self, void *where);
DECOMP_C void __thiscall sub_00427660(void *self, void *where);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char d_0060833C[], d_00607B18[], d_00607B24[], d_00699050[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *)
    __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *)
    __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_006073A4)(void *)
    __asm__("__imp_??0exception@std@@QAE@XZ");

#define COLOR(n) (((char *)(n))[0x30])
#define NIL(n)   (((char *)(n))[0x31])

DECOMP(00428E00)
void *__thiscall f_00428E00(void *this, void *out, unsigned char leftish, char *pos, char *rec)
{
    char *s = (char *)this;
    char *head, *node, *x, *parent, *grand, *uncle;

    if (*(unsigned int *)(s + 8) > 0x71c71c5u) {
        unsigned int msg[7], exc[3 + 7];
        imp_00607324(msg, d_0060833C);
        imp_006073A4(exc);
        *(void **)exc = d_00607B18;
        imp_00607334(exc + 3, msg);
        *(void **)exc = d_00607B24;
        sub_005E3EC0(exc, d_00699050);
        __builtin_unreachable();
    }
    head = *(char **)(s + 4);
    node = (char *)sub_00428D40((unsigned int)head, (unsigned int)pos, (unsigned int)head, rec, 0);
    *(unsigned int *)(s + 8) += 1;
    if (pos == head) {
        *(char **)(head + 4) = node;
        *(char **)head = node;
        *(char **)(head + 8) = node;
    } else if (!leftish) {
        *(char **)(pos + 8) = node;
        if (pos == *(char **)(head + 8))
            *(char **)(head + 8) = node;
    } else {
        *(char **)pos = node;
        if (pos == *(char **)head)
            *(char **)head = node;
    }
    x = node;
    while (COLOR(*(char **)(x + 4)) == 0) {
        parent = *(char **)(x + 4);
        grand = *(char **)(parent + 4);
        if (parent == *(char **)grand) {
            uncle = *(char **)(grand + 8);
            if (COLOR(uncle) == 0) {
                COLOR(parent) = 1;
                COLOR(uncle) = 1;
                COLOR(grand) = 0;
                x = grand;
            } else {
                if (x == *(char **)(parent + 8)) {
                    sub_00427610(s, parent);
                    x = parent;
                }
                COLOR(*(char **)(x + 4)) = 1;
                COLOR(*(char **)(*(char **)(x + 4) + 4)) = 0;
                sub_00427660(s, *(char **)(*(char **)(x + 4) + 4));
            }
        } else {
            uncle = *(char **)grand;
            if (COLOR(uncle) == 0) {
                COLOR(parent) = 1;
                COLOR(uncle) = 1;
                COLOR(grand) = 0;
                x = grand;
            } else {
                if (x == *(char **)parent) {
                    sub_00427660(s, parent);
                    x = parent;
                }
                COLOR(*(char **)(x + 4)) = 1;
                COLOR(*(char **)(*(char **)(x + 4) + 4)) = 0;
                /* inlined rotation of the grandparent's +8 child up */
                grand = *(char **)(*(char **)(x + 4) + 4);
                uncle = *(char **)(grand + 8);
                *(char **)(grand + 8) = *(char **)uncle;
                if (!NIL(*(char **)uncle))
                    *(char **)(*(char **)uncle + 4) = grand;
                *(char **)(uncle + 4) = *(char **)(grand + 4);
                if (grand == *(char **)(*(char **)(s + 4) + 4)) {
                    *(char **)(*(char **)(s + 4) + 4) = uncle;
                } else {
                    parent = *(char **)(grand + 4);
                    if (grand == *(char **)parent)
                        *(char **)parent = uncle;
                    else
                        *(char **)(parent + 8) = uncle;
                }
                *(char **)uncle = grand;
                *(char **)(grand + 4) = uncle;
            }
        }
    }
    COLOR(*(char **)(*(char **)(s + 4) + 4)) = 1;
    *(char **)out = node;
    return out;
}
