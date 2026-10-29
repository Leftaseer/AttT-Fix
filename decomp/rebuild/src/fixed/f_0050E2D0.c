/* 0x0050E2D0: shows a unit's (arg 2) reach in battle (args 1 and 3 unused): with arg 4 it is marked on its owner's
 * board (+0x2C8, 0x0051F5F0) and the view refreshed (+0x1C0 vf8C); otherwise its moves (+0xD8's +0x150 list,
 * 0x00503BC0 / 0x00502D10; copied by value, 0x005019E0) go to the battle's search (0x004E46D0, 0x004FB800 with 0)
 * and each unit in the resulting set gets its count in +0x1E4. The original's attack branch (+0x15C, flag 1) is
 * unreachable (it tests arg 4 again) and left out. The sets are std::sets built and freed inline */
/* @conv ECX 16 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Obj12_50E2D0;
typedef struct { unsigned int alloc; char *head; unsigned int size; } Set_50E2D0;
DECOMP_C void __thiscall sub_0051F5F0(void *self, void *unit);
DECOMP_C char *__cdecl sub_004FA480(void);
DECOMP_C void *__thiscall sub_00503BC0(void *self, void *out);
DECOMP_C void *__thiscall sub_00502D10(void *self, void *key);
DECOMP_C void __thiscall sub_005019E0(void *self, void *src);
DECOMP_C void *__cdecl sub_004E46D0(void);
DECOMP_C Set_50E2D0 *__thiscall sub_004FB800(void *self, void *out, Obj12_50E2D0 reach, int attack);
DECOMP_C void __thiscall sub_004FAF90(void *self, void *out, void *first, void *last);
DECOMP_C void __thiscall sub_004FAE50(void *self, void *src);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
typedef void (__thiscall *vf_50E2D0)(void *self);

#define NIL(n) ((n)[0x15])

DECOMP(0050E2D0)
void __thiscall f_0050E2D0(void *this, void *a1, char *unit, void *a3, unsigned char board)
{
    char *s = (char *)this, *n, *p, *dummy;
    Set_50E2D0 set, *res, r;
    unsigned int tmp;
    Obj12_50E2D0 reach;
    void **v;
    if (board) {
        sub_0051F5F0(*(void **)(unit + 0x2c8), unit);
        v = *(void ***)(s + 0x1c0);
        ((vf_50E2D0)(*(void ***)v)[0x8c / 4])(v);
        return;
    }
    set.head = sub_004FA480();
    set.head[0x15] = 1;
    ((char **)set.head)[1] = set.head;
    ((char **)set.head)[0] = set.head;
    ((char **)set.head)[2] = set.head;
    set.size = 0;
    sub_005019E0(&reach, sub_00502D10(sub_00503BC0(*(char **)(s + 0xd8) + 0x150, &tmp), &unit));
    res = sub_004FB800(sub_004E46D0(), &r, reach, 0);
    if (&set != res) {
        sub_004FAF90(&set, &dummy, *(char **)set.head, set.head);
        sub_004FAE50(&set, res);
    }
    sub_004FAF90(&r, &dummy, *(char **)r.head, r.head);
    sub_005E3E9C(r.head);
    for (n = *(char **)set.head; n != set.head;) {
        *(int *)(*(char **)(n + 0xc) + 0x1e4) = *(int *)(n + 0x10);
        if (NIL(n))
            continue;
        p = ((char **)n)[2];
        if (!NIL(p)) {
            n = p;
            while (!NIL(((char **)n)[0]))
                n = ((char **)n)[0];
        } else {
            p = ((char **)n)[1];
            while (!NIL(p) && n == ((char **)p)[2]) {
                n = p;
                p = ((char **)p)[1];
            }
            n = p;
        }
    }
    sub_004FAF90(&set, &dummy, *(char **)set.head, set.head);
    sub_005E3E9C(set.head);
}
