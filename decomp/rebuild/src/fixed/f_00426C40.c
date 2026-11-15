/* 0x00426C40: stores the argument's low byte in the +0x49 flag and reports the full argument to every control in
 * the +0x5C list through the +0x54 virtual of each one; returns the last virtual's result. */
/* @func 00426C40 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP(00426C40)
unsigned int __cdecl f_00426C40(void *this, unsigned int eax, unsigned int enable)
{
    char *s = (char *)this;
    char *head = *(char **)(s + 0x5c);
    char *node = *(char **)head;
    unsigned int result = eax;

    s[0x49] = (char)enable;
    while (node != head) {
        char *control = *(char **)(node + 8) + 0x54;
        result = (*(unsigned int (__thiscall **)(char *, unsigned int))(*(char **)control + 0x54))(control, enable);
        node = *(char **)node;
    }
    return result;
}
