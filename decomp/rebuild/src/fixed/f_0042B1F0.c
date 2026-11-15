/* 0x0042B1F0: resizes the int buffer at +4: the old block is freed, `count` ints are allocated (an overflowing size
 * becomes a saturated value, as the original's multiply does), and the used count at +8 is reset. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                  /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *block);                         /* operator delete[] */

DECOMP(0042B1F0)
void __thiscall f_0042B1F0(char *this, unsigned int count)
{
    if (*(void **)(this + 4)) {
        sub_005E3EBA(*(void **)(this + 4));
        *(void **)(this + 4) = 0;
    }
    if (count)
        *(void **)(this + 4) = sub_005E3B10((unsigned long long)count * 4 > 0xffffffffu
                                            ? 0xffffffffu : count * 4);
    *(unsigned int *)(this + 8) = 0;
}
