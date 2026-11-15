/* 0x0043E2D0: appends a copy of the 8-byte record arg 1 to the vector (+4 begin, +8 end, +0xC limit): with spare
 * capacity the inline append (0x004BA1F0, whose element-limit argument is this rounded down to 256) is used, else the
 * growing append (0x0050A740).  Neither returns a value. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int d[2]; } Rec_43E2D0;
DECOMP_C void __cdecl sub_004BA1F0(void *eax, void *dst, int n, void *val, unsigned int alloc, void *val2, unsigned int tag);
DECOMP_C void __thiscall sub_0050A740(void *self, void *where, unsigned int n, void *val);

DECOMP(0043E2D0)
void __thiscall f_0043E2D0(void *self, Rec_43E2D0 *val)
{
    char *v = (char *)self;
    char **begin = (char **)(v + 4), **end = (char **)(v + 8), **limit = (char **)(v + 0xc);
    unsigned int tag = (unsigned int)(size_t)self & 0xffffff00;

    if (*begin && (unsigned int)(*end - *begin) / 8 < (unsigned int)(*limit - *begin) / 8) {
        sub_004BA1F0((void *)(size_t)tag, *end, 1, val, (unsigned int)(size_t)self, val, tag);
        *end += 8;
    } else
        sub_0050A740(self, *end, 1, val);
}
