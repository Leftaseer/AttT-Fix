/* Shared implementation for the Lua callback registrars: resolve the callback through nScript::TableGet,
 * invoke it with the class object, release the temporary handle and remove the callback arguments. */
#include "auto_pre.h"
typedef unsigned int (__thiscall *lua_callback_fn)(void *self, void *args);
DECOMP_C void *__cdecl sub_00402FD0(void *L, int index);
DECOMP_C int __cdecl sub_00402A60(void *L);
DECOMP_C void __cdecl sub_00402AC0(void *L, int index);
DECOMP_C void *__thiscall sub_004277B0(void *self, void *table, int count, unsigned char owns);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __stdcall sub_005E3EC0(void *object, void *throw_info);
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C char d_008D122C[], d_00608290[], d_0060828C[], d_00608274[], d_0069916C[];

static unsigned int lua_callback_register(void *name_slot)
{
    void *L = *(void **)d_008D122C;
    unsigned int **entry = sub_00402FD0(L, 1);
    unsigned int base, result;
    int count;
    unsigned int **globals;
    unsigned int args[6];
    if (!entry) {
        unsigned int a[7], b[7], c[7], d[7], e[7], thrown[7];
        imp_00607324(a, d_00608290);
        imp_006071DC(b, a, *(char **)name_slot);
        imp_006071DC(c, b, d_0060828C);
        globals = sub_00402FD0(L, -10003);
        imp_006071DC(d, c, (char *)*globals);
        imp_006071DC(e, d, d_00608274);
        imp_00607334(thrown, e);
        sub_005E3EC0(thrown, d_0069916C);
        __builtin_unreachable();
    }
    base = *entry;
    globals = sub_00402FD0(L, -10003);
    count = sub_00402A60(L) - 1;
    sub_004277B0(args, *globals, count, 0);
    result = ((lua_callback_fn)globals[2])((char *)globals[3] + base, args);
    sub_00427820(args);
    while (count > 0) {
        sub_00402AC0(L, 2);
        count--;
    }
    return result;
}
