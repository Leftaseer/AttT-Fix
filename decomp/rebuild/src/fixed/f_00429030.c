/* 0x00429030: std::map::erase(iterator) for the ambient sound tree held at +4: arg 2 is the node to erase (the
 * head, +0x31 set, throws std::out_of_range "invalid map/set<T> iterator", vtable 0x00608208, throw info
 * 0x00699C38).  arg 1 receives the iterator that follows.  The successor (0x00427720) is computed first; a node
 * with two children is replaced by its successor (links relinked, colours swapped), otherwise the only child takes
 * its place; a black node is then fixed up (rotations 0x00427610 / 0x00427660, head extremes via 0x004274B0 /
 * 0x00427490), its item vector (+0x24) and the node are freed and the count at +8 drops.  Colour byte +0x30,
 * nil flag +0x31. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00427720(void *slot);
DECOMP_C void __thiscall sub_00427610(void *self, void *where);
DECOMP_C void __thiscall sub_00427660(void *self, void *where);
DECOMP_C void *__cdecl sub_004274B0(void *node);
DECOMP_C void *__cdecl sub_00427490(void *node);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                        /* operator delete */
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char d_00608350[], d_00607B18[], d_00608208[], d_00699C38[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *)
    __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *)
    __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_006073A4)(void *)
    __asm__("__imp_??0exception@std@@QAE@XZ");

#define COLOR(n) (((char *)(n))[0x30])
#define NIL(n)   (((char *)(n))[0x31])

DECOMP(00429030)
void __thiscall f_00429030(void *this, char **out, char *pos)
{
    char *s = (char *)this;
    char *head = *(char **)(s + 4);
    char **posslot = (char **)((char *)__builtin_frame_address(0) + 0xc);  /* arg 2's own slot */
    char *next, *fix, *fixp, *xp, *x, *sib;
    unsigned int oldcolor;

    pos = *posslot;

    if (NIL(pos)) {
        unsigned int msg[7], exc[3 + 7];
        imp_00607324(msg, d_00608350);
        imp_006073A4(exc);
        *(void **)exc = d_00607B18;
        imp_00607334(exc + 3, msg);
        *(void **)exc = d_00608208;
        sub_005E3EC0(exc, d_00699C38);
        __builtin_unreachable();
    }
    next = pos;
    sub_00427720(posslot);
    next = *posslot;

    x = *(char **)pos;
    if (!NIL(x)) {
        fix = x;
        if (!NIL(*(char **)(pos + 8)) && next != pos) {
            /* two children: the successor takes the erased node's place */
            fix = *(char **)(next + 8);
            *(char **)(x + 4) = next;
            *(char **)next = *(char **)pos;
            fixp = next;
            if (next != *(char **)(pos + 8)) {
                fixp = *(char **)(next + 4);
                if (!NIL(fix))
                    *(char **)(fix + 4) = fixp;
                *(char **)fixp = fix;
                *(char **)(next + 8) = *(char **)(pos + 8);
                *(char **)(*(char **)(pos + 8) + 4) = next;
            }
            if (*(char **)(head + 4) == pos) {
                *(char **)(head + 4) = next;
            } else {
                char *parent = *(char **)(pos + 4);
                if (*(char **)parent == pos)
                    *(char **)parent = next;
                else
                    *(char **)(parent + 8) = next;
            }
            *(char **)(next + 4) = *(char **)(pos + 4);
            oldcolor = COLOR(next);
            COLOR(next) = COLOR(pos);
            COLOR(pos) = (char)oldcolor;
            goto fixup;
        }
    } else {
        fix = *(char **)(pos + 8);
    }

    fixp = *(char **)(pos + 4);
    if (!NIL(fix))
        *(char **)(fix + 4) = fixp;
    if (*(char **)(head + 4) == pos)
        *(char **)(head + 4) = fix;
    else if (*(char **)fixp == pos)
        *(char **)fixp = fix;
    else
        *(char **)(fixp + 8) = fix;
    if (*(char **)head == pos)
        *(char **)head = NIL(fix) ? fixp : (char *)sub_004274B0(fix);
    if (*(char **)(head + 8) == pos)
        *(char **)(head + 8) = NIL(fix) ? fixp : (char *)sub_00427490(fix);

fixup:
    if (COLOR(pos) == 1) {
        if (fix != *(char **)(head + 4)) {
            do {
                char *node = fixp;
                if (COLOR(fix) != 1)
                    break;
                sib = *(char **)node;
                if (fix == sib) {
                    sib = *(char **)(node + 8);
                    if (COLOR(sib) == 0) {
                        COLOR(sib) = 1;
                        COLOR(node) = 0;
                        sub_00427610(s, node);
                        sib = *(char **)(node + 8);
                    }
                    if (!NIL(sib)) {
                        if (COLOR(*(char **)sib) != 1 || COLOR(*(char **)(sib + 8)) != 1) {
                            if (COLOR(*(char **)(sib + 8)) == 1) {
                                COLOR(*(char **)sib) = 1;
                                COLOR(sib) = 0;
                                sub_00427660(s, sib);
                                sib = *(char **)(node + 8);
                            }
                            COLOR(sib) = COLOR(node);
                            COLOR(node) = 1;
                            COLOR(*(char **)(sib + 8)) = 1;
                            sub_00427610(s, node);
                            break;
                        }
                        COLOR(sib) = 0;
                    }
                } else {
                    if (COLOR(sib) == 0) {
                        COLOR(sib) = 1;
                        COLOR(node) = 0;
                        sub_00427660(s, node);
                        sib = *(char **)node;
                    }
                    if (!NIL(sib)) {
                        if (COLOR(*(char **)(sib + 8)) == 1 && COLOR(*(char **)sib) == 1) {
                            COLOR(sib) = 0;
                        } else {
                            if (COLOR(*(char **)sib) == 1) {
                                COLOR(*(char **)(sib + 8)) = 1;
                                COLOR(sib) = 0;
                                sub_00427610(s, sib);
                                sib = *(char **)node;
                            }
                            COLOR(sib) = COLOR(node);
                            COLOR(node) = 1;
                            COLOR(*(char **)sib) = 1;
                            sub_00427660(s, node);
                            break;
                        }
                    }
                }
                fixp = *(char **)(node + 4);
                fix = node;
            } while (fix != *(char **)(head + 4));
        }
        COLOR(fix) = 1;
    }

    if (*(void **)(pos + 0x24) != 0)
        sub_005E3E9C(*(void **)(pos + 0x24));
    *(void **)(pos + 0x24) = 0;
    *(void **)(pos + 0x28) = 0;
    *(void **)(pos + 0x2c) = 0;
    sub_005E3E9C(pos);
    if (*(unsigned int *)(s + 8) > 0)
        *(unsigned int *)(s + 8) -= 1;
    *out = next;
}
