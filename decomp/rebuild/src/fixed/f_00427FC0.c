/* 0x00427FC0: constructs the map at +4 the same way 0x00427EC0 resets it (a fresh 0x00427C00 head becomes its own
 * empty nil-marked circle, count +8 cleared) and returns the object.  EDX is not read. */
/* @func 00427FC0 custom */
/* @conv ECX,EDX 8 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_00427C00(void);

DECOMP(00427FC0)
void *__cdecl f_00427FC0(void *this, unsigned int reg_edx, unsigned int unused1, unsigned int unused2)
{
    char *s = (char *)this;
    char *head = (char *)sub_00427C00();

    *(char **)(s + 4) = head;
    head[0x31] = 1;
    *(char **)(head + 4) = head;
    *(char **)head = head;
    *(char **)(head + 8) = head;
    *(unsigned int *)(s + 8) = 0;
    return s;
}
