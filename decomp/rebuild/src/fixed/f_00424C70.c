/* 0x00424C70: CActionKey::~CActionKey (CGameObject's): the vtable of CGameObject; an object still holding its child
 * (+4) throws the exception of 0x00421220 with "Ошибка при удалении CGameObject" (error deleting CGameObject),
 * GameObject.h line 26 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607D14[], d_00607D18[], d_00607D34[], d_0069916C[];
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");

DECOMP(00424C70)
void __thiscall f_00424C70(void *this)
{
    *(void **)this = d_00607D14;
    if (((void **)this)[1]) {
        unsigned int msg[7], thrown[7];
        imp_00607324(msg, d_00607D34);
        sub_00421220(thrown, msg, d_00607D18, 0x1a);
        sub_005E3EC0(thrown, d_0069916C);
    }
}
