/* 0x00444BD0: types a character into the console line (the string at +0x94): runs of spaces and of newlines
 * collapse (the flags at 0x6C8974, after a space, and 0x6C0036, after a newline): a newline right after a space
 * replaces it; returns what the string's += returned (the character when nothing was added) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_006C8974[], d_006C0028[];
DECOMP_C void *(__thiscall *imp_00607204)(void *, unsigned int) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@D@Z");
DECOMP_C void *(__thiscall *imp_00607200)(void *, unsigned int, unsigned int) __asm__("__imp_?erase@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV12@II@Z");

#define AFTER_SPACE d_006C8974[0]
#define AFTER_NEWLINE d_006C0028[0xe]

DECOMP(00444BD0)
unsigned int __thiscall f_00444BD0(void *this, unsigned int c)
{
    char *line = (char *)this + 0x94;
    if ((char)c == ' ') {
        if (AFTER_SPACE || AFTER_NEWLINE)
            return c;
        AFTER_SPACE = 1;
        AFTER_NEWLINE = 0;
        return (unsigned int)imp_00607204(line, ' ');
    }
    if ((char)c != '\n') {
        AFTER_NEWLINE = 0;
        AFTER_SPACE = 0;
        return (unsigned int)imp_00607204(line, c);
    }
    if (AFTER_SPACE == 1) {
        AFTER_SPACE = 0;
        AFTER_NEWLINE = 1;
        imp_00607200(line, *(unsigned int *)((char *)this + 0xa8) - 1, 1);
        return (unsigned int)imp_00607204(line, '\n');
    }
    if (AFTER_NEWLINE)
        return 1;
    AFTER_NEWLINE = 1;
    return (unsigned int)imp_00607204(line, '\n');
}
