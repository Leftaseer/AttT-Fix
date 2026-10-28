/* 0x004CC460: std::list<T>::sort(pred) as inlined by the library: with at least two nodes, takes them one at a
 * time into a scratch list (+0x00 allocator, +0x04 head, +0x08 size; the head from 0x004C2F40) and merges
 * (0x004CC350 with the predicate) through 25 bins (26 lists made and destroyed by the EH vector iterators with
 * 0x004C38E0 / 0x0044D6E0), the last bins merged together and spliced back; the scratch list's nodes and head are
 * freed inline. Nodes: +0x00 next, +0x04 prev */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int alloc; char **head; unsigned int size; } List_4CC460;
DECOMP_C char **__cdecl sub_004C2F40(void);
DECOMP_C void __thiscall sub_004CC350(void *self, void *other, void *pred);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C void __stdcall sub_005E4134(void *p, unsigned int size, int n, void *dtor);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C char d_004C38E0[], d_0044D6E0[];

/* the node moves of _Splice(where, right, first, last), in the library's order */
static void relink_4CC460(char **first, char **last, char **where)
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

static void swap_4CC460(List_4CC460 *a, List_4CC460 *b)
{
    char **h = a->head;
    unsigned int n = a->size;
    a->head = b->head;
    a->size = b->size;
    b->head = h;
    b->size = n;
}

DECOMP(004CC460)
void __thiscall f_004CC460(void *this, void *pred)
{
    List_4CC460 *l = (List_4CC460 *)this, t, bins[26];
    unsigned int maxbin = 0, bin, n;
    char **first, **last, **where, **p, **q;
    if (l->size < 2)
        return;
    t.head = sub_004C2F40();
    t.size = 0;
    sub_005E4197(bins, 0xc, 0x1a, d_004C38E0, d_0044D6E0);
    while (l->size) {
        first = (char **)l->head[0];
        last = (char **)first[0];
        where = (char **)t.head[0];
        if (&t != l) {
            sub_004E0EF0(&t, 1);
            l->size--;
        }
        relink_4CC460(first, last, where);
        for (bin = 0; bin < maxbin && bins[bin].size; bin++) {
            sub_004CC350(&bins[bin], &t, pred);
            swap_4CC460(&bins[bin], &t);
        }
        if (bin == 25)
            sub_004CC350(&bins[24], &t, pred);
        else {
            swap_4CC460(&bins[bin], &t);
            if (bin == maxbin)
                maxbin++;
        }
    }
    for (bin = 1; bin < maxbin; bin++)
        sub_004CC350(&bins[bin], &bins[bin - 1], pred);
    where = (char **)l->head[0];
    if (&bins[maxbin - 1] != l && (n = bins[maxbin - 1].size)) {
        last = bins[maxbin - 1].head;
        first = (char **)last[0];
        sub_004E0EF0(l, n);
        bins[maxbin - 1].size -= n;
        relink_4CC460(first, last, where);
    }
    sub_005E4134(bins, 0xc, 0x1a, d_0044D6E0);
    p = (char **)t.head[0];
    t.head[0] = (char *)t.head;
    t.head[1] = (char *)t.head;
    while (p != t.head) {
        q = (char **)p[0];
        sub_005E3E9C(p);
        p = q;
    }
    sub_005E3E9C(t.head);
}
