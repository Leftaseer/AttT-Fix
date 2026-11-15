/* 0x0042BB10: the highlight kind for the hero's class (the id at +0x1D8 of 0x00425F60's hero): 4 for class 1, 7 for
 * 2..4, 9 for 5..8 and 10 for 9 (0 otherwise) in the low byte; the class id's upper 24 bits are kept. */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00425F60(void);

DECOMP(0042BB10)
int __stdcall f_0042BB10(void)
{
    int class_id = *(int *)(sub_00425F60() + 0x1d8);
    int kind = 0;

    if (class_id == 1)
        kind = 4;
    else if (class_id >= 2 && class_id <= 4)
        kind = 7;
    else if (class_id >= 5 && class_id <= 8)
        kind = 9;
    else if (class_id == 9)
        kind = 10;
    return (class_id & ~0xff) | kind;
}
