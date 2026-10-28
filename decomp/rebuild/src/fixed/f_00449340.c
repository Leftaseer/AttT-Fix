/* 0x00449340: gets a value of a script table: the table (0x0057B4E0 of the object at +0, by the key at +4) and a copy of the string
 * make the pair 0x00449290 builds, which 0x00449230 stores in *out; returns out (the string came by value: this
 * function destroys it) */
/* @conv ECX 32 */
#include "auto_pre.h"
typedef struct { unsigned int d[3]; } Tbl_00449340;               /* nScript::Table */
typedef struct { unsigned int d[7]; } Str_00449340;               /* std::string */
typedef struct { Tbl_00449340 t; Str_00449340 s; } Pair_00449340;
DECOMP_C Tbl_00449340 *__thiscall sub_0057B4E0(void *self, Tbl_00449340 *out, void *key);
DECOMP_C void *__thiscall sub_00449290(Pair_00449340 *self, Tbl_00449340 t, Str_00449340 s);
DECOMP_C void *__thiscall sub_00449230(void *self, void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00449340)
void *__thiscall f_00449340(void *this, void *out, unsigned int s0, unsigned int s1, unsigned int s2, unsigned int s3,
                       unsigned int s4, unsigned int s5, unsigned int s6)
{
    Str_00449340 *str = (Str_00449340 *)((char *)__builtin_frame_address(0) + 12);     /* the string by value */
    Str_00449340 copy;
    Tbl_00449340 t;
    Pair_00449340 pair;
    imp_00607334(&copy, str);
    sub_0057B4E0(*(void **)this, &t, *(void **)((char *)this + 4));
    sub_00449230(out, sub_00449290(&pair, t, copy));
    imp_00607330(&pair.s);
    sub_004220A0(&pair.t);
    imp_00607330(str);
    return out;
}
