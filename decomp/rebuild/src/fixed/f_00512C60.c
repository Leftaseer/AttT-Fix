/* 0x00512C60: removes from the list of objects (head +0, tail +4; each object's +4 the next) every one whose vf08(a)
 * says so, freeing it */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *p);
typedef char (__thiscall *vf08_512C60)(void *self, unsigned int a);

#define VF08(o) ((vf08_512C60)(*(void ***)(o))[2])((o), a)

DECOMP(00512C60)
void __thiscall f_00512C60(void *this, unsigned int a)
{
    char **l = (char **)this;
    char *prev, *cur;
    if (!l[0])
        return;
    while (VF08(l[0])) {
        char *n = l[0];
        l[0] = *(char **)(n + 4);
        if (n == l[1])
            l[1] = *(char **)(n + 4);
        sub_005E3E9C(n);
        if (!l[0])
            return;
    }
    prev = l[0];
    cur = *(char **)(prev + 4);
    while (cur) {
        if (VF08(cur)) {
            *(char **)(prev + 4) = *(char **)(cur + 4);
            if (cur == l[1])
                l[1] = *(char **)(cur + 4);
            sub_005E3E9C(cur);
            cur = *(char **)(prev + 4);
        } else {
            prev = cur;
            cur = *(char **)(cur + 4);
        }
    }
}
