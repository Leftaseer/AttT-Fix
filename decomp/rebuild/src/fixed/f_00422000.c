/* 0x00422000: Object::~Object: the vtable of Object; an object still holding its child (+4) throws the
 * std::string "Ошибка при удалении Object" (error deleting Object) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607C88[], d_00607C98[], d_0069916C[];
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");

DECOMP(00422000)
void __thiscall f_00422000(void *this)
{
    *(void **)this = d_00607C88;
    if (((void **)this)[1]) {
        unsigned int msg[7], thrown[7];         /* two std::string */
        imp_00607324(msg, d_00607C98);
        imp_00607334(thrown, msg);
        sub_005E3EC0(thrown, d_0069916C);
    }
}
