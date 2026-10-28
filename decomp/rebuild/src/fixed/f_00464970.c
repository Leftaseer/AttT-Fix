/* 0x00464970: gets a value of a script table: the table (0x0057B4E0 of this, by the key at +0xc) and a copy of the string
 * make the pair 0x00449290 builds, which 0x00449230 stores in *out; returns out (the string came by value: this
 * function destroys it) */
/* @conv ECX 32 */
#include "auto_pre.h"
typedef struct { unsigned int d[3]; } Tbl_00464970;               /* nScript::Table */
typedef struct { unsigned int d[7]; } Str_00464970;               /* std::string */
typedef struct { Tbl_00464970 t; Str_00464970 s; } Pair_00464970;
DECOMP_C Tbl_00464970 *__thiscall sub_0057B4E0(void *self, Tbl_00464970 *out, void *key);
DECOMP_C void *__thiscall sub_00449290(Pair_00464970 *self, Tbl_00464970 t, Str_00464970 s);
DECOMP_C void *__thiscall sub_00449230(void *self, void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00464970)
void *__thiscall f_00464970(void *this, void *out, unsigned int s0, unsigned int s1, unsigned int s2, unsigned int s3,
                       unsigned int s4, unsigned int s5, unsigned int s6)
{
    Str_00464970 *str = (Str_00464970 *)((char *)__builtin_frame_address(0) + 12);     /* the string by value */
    Str_00464970 copy;
    Tbl_00464970 t;
    Pair_00464970 pair;
    imp_00607334(&copy, str);
    sub_0057B4E0(this, &t, *(void **)((char *)this + 0xc));
    sub_00449230(out, sub_00449290(&pair, t, copy));
    imp_00607330(&pair.s);
    sub_004220A0(&pair.t);
    imp_00607330(str);
    return out;
}
