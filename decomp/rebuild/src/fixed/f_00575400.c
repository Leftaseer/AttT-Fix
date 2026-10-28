/* 0x00575400: casts the spell named by the string: its first five characters find the handler in the map at +4
 * (0x00422D80); the handler (the function at +0x24 of the map node) or, without one, the default 0x00574ED0 gets the
 * script table "Spell" (0x00575300, by value: the callee destroys it) and the name */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int d[3]; } Tbl_575400;          /* nScript::Table */
DECOMP_C void __thiscall sub_00422D80(void *map, void *out_it, void *key);
DECOMP_C Tbl_575400 *__stdcall sub_00575300(Tbl_575400 *out);
DECOMP_C void *__cdecl sub_00574ED0(Tbl_575400 t, void *name);
DECOMP_C void *(__thiscall *imp_006071CC)(void *, void *, unsigned int, unsigned int) __asm__("__imp_?substr@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBE?AV12@II@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void *(__cdecl *handler_575400)(Tbl_575400 t, void *name);

DECOMP(00575400)
void *__thiscall f_00575400(void *this, void *name)
{
    char *s = (char *)this;
    unsigned int key[7];                                    /* std::string */
    char *it;
    Tbl_575400 t;
    void *r;
    imp_006071CC(name, key, 0, 5);
    sub_00422D80(s + 4, &it, key);
    if (it != *(char **)(s + 0xc)) {
        sub_00575300(&t);
        r = (*(handler_575400 *)(it + 0x24))(t, name);
    } else {
        sub_00575300(&t);
        r = sub_00574ED0(t, name);
    }
    imp_00607330(key);
    return r;
}
