/* 0x00427EC0: resets the map held at +4: a fresh head node (0x00427C00) becomes its own empty circle (the nil
 * flag +0x31, both links and the parent at +4 pointing back at it) and the count at +8 is cleared. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_00427C00(void);

DECOMP(00427EC0)
void __thiscall f_00427EC0(void *this)
{
    char *s = (char *)this;
    char *head = (char *)sub_00427C00();

    *(char **)(s + 4) = head;
    head[0x31] = 1;
    *(char **)(head + 4) = head;
    *(char **)head = head;
    *(char **)(head + 8) = head;
    *(unsigned int *)(s + 8) = 0;
}
