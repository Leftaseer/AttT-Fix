/* 0x0042B290: the other CSimpleAnimation subclass's constructor: the descriptor's name string (its +0x1C and +0x24)
 * builds the source object 0x0042A010, that source builds the base animation, and the constructor ends with vtable
 * 0x0060863C and the descriptor's +0x20 in +0x204.  The by-value string temporary dies with the source constructor.
 * Returns this. */
/* @conv ECX 12 */
#include "auto_pre.h"

typedef struct { unsigned int raw[7]; } Str_42B290;                       /* std::string, by value */

DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *__thiscall sub_0042A010(void *self, Str_42B290 name, unsigned int a, unsigned int b);
DECOMP_C void *__thiscall sub_0042A530(void *self, void *source, void *driven, unsigned int owning);
DECOMP_C char d_0060863C[];

DECOMP(0042B290)
void *__thiscall f_0042B290(char *this, char *desc, char *driven, unsigned int owning)
{
    Str_42B290 name;
    char source[0x24];
    unsigned int a, b;

    a = *(unsigned int *)(desc + 0x1c);
    b = *(unsigned int *)(desc + 0x24);
    imp_00607334(&name, desc);
    sub_0042A010(source, name, a, b);
    sub_0042A530(this, source, driven, owning);
    *(void **)this = d_0060863C;
    *(unsigned int *)(this + 0x204) = *(unsigned int *)(desc + 0x20);
    return this;
}
