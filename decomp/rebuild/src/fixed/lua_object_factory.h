/* Construct a script object from the Lua arguments and return it as userdata with its class metatable. */
#include "auto_pre.h"
typedef void *(__thiscall *lua_object_ctor)(void *self, void *args);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C int __cdecl sub_00402A60(void *L);
DECOMP_C void *__thiscall sub_004277B0(void *self, void *table, int count, unsigned char owns);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void *__cdecl sub_00403BF0(void *L, unsigned int size);
DECOMP_C void __cdecl sub_00403390(void *L, int index, int reference);
DECOMP_C int __cdecl sub_004036B0(void *L, int index);
DECOMP_C char d_008D122C[];

static int lua_object_factory(unsigned int size, void *table_slot, lua_object_ctor ctor, void *metatable_slot)
{
    void *L = *(void **)d_008D122C;
    void *object = sub_005E3EAE(size);
    void **userdata;
    if (object) {
        unsigned int args[6];
        int count = sub_00402A60(L) - 1;
        sub_004277B0(args, *(void **)table_slot, count, 1);
        object = ctor(object, args);
        sub_00427820(args);
    }
    userdata = sub_00403BF0(L, 4);
    *userdata = object;
    sub_00403390(L, -10000, *(int *)metatable_slot);
    sub_004036B0(L, -2);
    return 1;
}
