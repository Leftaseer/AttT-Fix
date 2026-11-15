/* 0x004284A0: copy-constructs the vector of 12-byte elements at +4 from the one at src+4: the count is
 * (end - begin) / 12, a fresh block of count elements (0x0046A5E0) backs the new vector and 0x00427770 copies the
 * elements into it; the object is returned.  A count past 0x15555555 raises through 0x00493740. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00493740(void);                              /* the vector length error */
DECOMP_C char *__cdecl sub_0046A5E0(unsigned int count, void *hint);   /* _Allocate */
DECOMP_C void *__cdecl sub_00427770(void *first, void *last, void *dest);

DECOMP(004284A0)
void *__thiscall f_004284A0(void *this, char *src)
{
    char *s = (char *)this;
    unsigned int count = *(char **)(src + 4) == 0 ? 0 :
                         (unsigned int)((*(char **)(src + 8) - *(char **)(src + 4)) / 0xc);
    char *base;

    *(void **)(s + 4) = 0;
    *(void **)(s + 8) = 0;
    *(void **)(s + 0xc) = 0;
    if (count != 0) {
        if (count > 0x15555555u)
            sub_00493740();
        base = sub_0046A5E0(count, 0);
        *(char **)(s + 0xc) = base + count * 0xc;
        *(char **)(s + 4) = base;
        *(char **)(s + 8) = base;
        *(char **)(s + 8) = sub_00427770(*(void **)(src + 4), *(void **)(src + 8), base);
    }
    return s;
}
