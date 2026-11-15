/* 0x00443460: selects the cursor named by arg 1 (a std::string): the name is assigned to the manager's state slot
 * (+0x23C), looked up in the cursor map (+0x258, 0x00422D80) and its cursor (node +0x24) handed to slot 0xE8 of the
 * manager.  A name that is not in the map raises the CGameException (ThrowInfo 0x0069916C) "Неизвестное состояние
 * для курсора - " + name. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int d[7]; } Str_00443460;               /* std::string */
typedef void (__thiscall *vf_443460)(void *self, void *cursor);
DECOMP_C void __thiscall sub_00422D80(void *map, void **node, const void *key);
DECOMP_C char d_0060A318[], d_0069916C[];
DECOMP_C void (__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info); /* _CxxThrowException */

DECOMP(00443460)
void __thiscall f_00443460(void *this, void *name)
{
    char *s = (char *)this;
    void *node;

    imp_0060731C(s + 0x23c, name);
    sub_00422D80(s + 0x258, &node, name);
    if (node == *(void **)(s + 0x260)) {
        Str_00443460 text, msg, error;
        imp_00607324(&text, d_0060A318);
        imp_006071C0(&msg, &text, name);
        imp_00607334(&error, &msg);
        sub_005E3EC0(&error, d_0069916C);
    }
    ((vf_443460)(*(void ***)s)[0xe8 / 4])(s, *(void **)((char *)node + 0x24));
}
