/* 0x00449290: builds the table/string pair the script-value lookups (0x00464970, 0x00449340) return: the table (by
 * value, 12 bytes) is copied to +0 (0x00435D90), a copy of the string (by value, 28 bytes) built at +0xC, and the
 * by-value arguments are destroyed again (the table by 0x004220A0, the string by its destructor) as the callers'
 * temporaries expect; the pair is returned.  The unwind states cover the two copies. */
/* @conv ECX 40 */
#include "auto_pre.h"
typedef struct { unsigned int d[3]; } Tbl_00449290;               /* nScript::Table */
typedef struct { unsigned int d[7]; } Str_00449290;               /* std::string */
typedef struct { Tbl_00449290 t; Str_00449290 s; } Pair_00449290;
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00449290)
Pair_00449290 *__thiscall f_00449290(Pair_00449290 *this, Tbl_00449290 t, Str_00449290 s)
{
    sub_00435D90(this, &t);
    imp_00607334(&this->s, &s);
    sub_004220A0(&t);
    imp_00607330(&s);
    return this;
}
