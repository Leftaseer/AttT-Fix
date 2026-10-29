/* 0x00551CE0: std::list<Particle>::sort(pred) as inlined by the library, the same code as 0x004CC460 for the
 * particle list: the scratch list's head from 0x0054F7F0, merges by 0x00551920, sizes by 0x0054F8B0, the 26 bins made
 * and destroyed with 0x0054FB40 / 0x00550340, and the scratch list's particles destroyed (0x0054AF20) as freed */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int alloc; char **head; unsigned int size; } List_551CE0;
DECOMP_C char **__cdecl sub_0054F7F0(void);
DECOMP_C void __thiscall sub_00551920(void *self, void *other, void *pred);
DECOMP_C void __thiscall sub_0054F8B0(void *list, unsigned int n);
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C void __stdcall sub_005E4134(void *p, unsigned int size, int n, void *dtor);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C void __cdecl sub_0054AF20(void *self, unsigned int eax);   /* only sets the vtable; EAX passes through */
DECOMP_C char d_0054FB40[], d_00550340[];

/* the node moves of _Splice(where, right, first, last), in the library's order */
static void relink_551CE0(char **first, char **last, char **where)
{
    char **t;
    ((char ***)first[1])[0] = (char *)last;
    ((char ***)last[1])[0] = (char *)where;
    ((char ***)where[1])[0] = (char *)first;
    t = (char **)last[1];
    {
        char **w = (char **)where[1];
        where[1] = (char *)t;
        last[1] = first[1];
        first[1] = (char *)w;
    }
}

static void swap_551CE0(List_551CE0 *a, List_551CE0 *b)
{
    char **h = a->head;
    unsigned int n = a->size;
    a->head = b->head;
    a->size = b->size;
    b->head = h;
    b->size = n;
}

DECOMP(00551CE0)
void __thiscall f_00551CE0(void *this, void *pred)
{
    List_551CE0 *l = (List_551CE0 *)this, t, bins[26];
    unsigned int maxbin = 0, bin, n;
    char **first, **last, **where, **p, **q;
    if (l->size < 2)
        return;
    t.head = sub_0054F7F0();
    t.size = 0;
    sub_005E4197(bins, 0xc, 0x1a, d_0054FB40, d_00550340);
    while (l->size) {
        first = (char **)l->head[0];
        last = (char **)first[0];
        where = (char **)t.head[0];
        if (&t != l) {
            sub_0054F8B0(&t, 1);
            l->size--;
        }
        relink_551CE0(first, last, where);
        for (bin = 0; bin < maxbin && bins[bin].size; bin++) {
            sub_00551920(&bins[bin], &t, pred);
            swap_551CE0(&bins[bin], &t);
        }
        if (bin == 25)
            sub_00551920(&bins[24], &t, pred);
        else {
            swap_551CE0(&bins[bin], &t);
            if (bin == maxbin)
                maxbin++;
        }
    }
    for (bin = 1; bin < maxbin; bin++)
        sub_00551920(&bins[bin], &bins[bin - 1], pred);
    where = (char **)l->head[0];
    if (&bins[maxbin - 1] != l && (n = bins[maxbin - 1].size)) {
        last = bins[maxbin - 1].head;
        first = (char **)last[0];
        sub_0054F8B0(l, n);
        bins[maxbin - 1].size -= n;
        relink_551CE0(first, last, where);
    }
    sub_005E4134(bins, 0xc, 0x1a, d_00550340);
    p = (char **)t.head[0];
    t.head[0] = (char *)t.head;
    t.head[1] = (char *)t.head;
    while (p != t.head) {
        q = (char **)p[0];
        sub_0054AF20(p + 2, 0);
        sub_005E3E9C(p);
        p = q;
    }
    sub_005E3E9C(t.head);
}
