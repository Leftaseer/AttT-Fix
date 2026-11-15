/* 0x00427F10: the Lua setter of the same value: number argument args->+0x10 (plus one, as the stack counts from 1)
 * read through the global state, clamped to [0, the maximum at 0x0068AE40], then pushed like 0x00427D70 does with
 * an empty register argument; no results. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00427CE0(void *self, unsigned int eax, float value);
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);             /* lua_tonumber */
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C char d_008D122C[], d_0068AE40[];

DECOMP(00427F10)
int __thiscall f_00427F10(void *this, char *args)
{
    char *s = (char *)this;
    float value = (float)sub_00402DE0(*(void **)d_008D122C, *(int *)(args + 0x10) + 1);

    if (0.0f > value)
        value = 0.0f;
    else if (value > *(float *)d_0068AE40)
        value = *(float *)d_0068AE40;
    sub_00427CE0(s + 0x98, 0, value);
    *(float *)(s + 0x94) = value;
    *(float *)(sub_00427990() + 0x90) = value;
    return 0;
}
