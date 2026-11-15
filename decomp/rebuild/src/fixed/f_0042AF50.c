/* 0x0042AF50: CLoopAnimation's constructor.  The descriptor's name string is copied and handed, with the descriptor's
 * +0x1C and +0x28, to the source-object constructor 0x0042A010; that source then builds the CSimpleAnimation base.
 * vtable 0x00608744, the start key from the descriptor's +0x20, the end key from its +0x24 clamped to the last key,
 * a zero byte at +0x20C and the height differences between the start key, the end key and their predecessors
 * negated into +0x210/+0x214/+0x218.  Returns this. */
/* @conv ECX 12 */
#include "auto_pre.h"

typedef struct { unsigned int raw[7]; } Str_42AF50;                       /* std::string, by value */

DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *__thiscall sub_0042A010(void *self, Str_42AF50 name, unsigned int a, unsigned int b);
DECOMP_C void *__thiscall sub_0042A530(void *self, void *source, void *driven, unsigned int owning);
DECOMP_C char d_00608744[];

DECOMP(0042AF50)
void *__thiscall f_0042AF50(char *this, char *desc, char *driven, unsigned int owning)
{
    Str_42AF50 name;
    char source[0x24];
    unsigned int a, b, start, end;
    const float *keys;
    float *f = (float *)this;

    a = *(unsigned int *)(desc + 0x1c);
    b = *(unsigned int *)(desc + 0x28);
    imp_00607334(&name, desc);
    sub_0042A010(source, name, a, b);
    sub_0042A530(this, source, driven, owning);
    *(void **)this = d_00608744;
    start = *(unsigned int *)(desc + 0x20);
    *(unsigned int *)(this + 0x204) = start;
    end = *(unsigned int *)(desc + 0x24);
    if (*(unsigned int *)(this + 0x1d4) < end)
        end = *(unsigned int *)(this + 0x1d4);
    *(unsigned int *)(this + 0x208) = end;
    keys = *(const float **)(this + 0x1d8);
    this[0x20c] = 0;
    f[0x210 / 4] = -(keys[start * 3 - 1] - keys[*(unsigned int *)(this + 0x1d0) * 3 + 2]);
    f[0x214 / 4] = -(keys[*(unsigned int *)(this + 0x1d4) * 3 + 2] - keys[end * 3 + 2]);
    f[0x218 / 4] = -(keys[end * 3 + 2] - keys[start * 3 - 1]);
    return this;
}
