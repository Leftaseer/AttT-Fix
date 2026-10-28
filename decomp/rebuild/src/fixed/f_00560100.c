/* 0x00560100: advances a script table iterator (this: +0x08 valid, +0x0C the value's registry reference, +0x10 the
 * string key, +0x2C the table, +0x30 the key kind: 0 string, 1 number at +0x34) to the next entry whose value is a
 * table: pushes the table (lua_rawgeti from the registry) and the current key, steps with lua_next past non-table
 * values, drops the old reference (luaL_unref); then keeps the new key (lua_tonumber / lua_tolstring, whose EBX input
 * is given L) and a reference to the value (lua_remove of the key, luaL_ref), or marks the iterator invalid; the Lua
 * stack (0x008CF080) is restored to its height on entry */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_00402A60(void *L);                         /* lua_gettop */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C void __cdecl sub_00403120(void *L, const char *s);         /* lua_pushstring */
DECOMP_C int __cdecl sub_00403B00(void *L, int idx);                /* lua_next */
DECOMP_C int __cdecl sub_00402C20(void *L, int idx);                /* lua_type */
DECOMP_C void __cdecl sub_00402270(void *L, int t, int ref);        /* luaL_unref */
DECOMP_C const char *__cdecl sub_00402ED0(void *ebx, void *L, int idx, unsigned int *len);   /* lua_tolstring */
DECOMP_C void __cdecl sub_00402AC0(void *L, int idx);               /* lua_remove */
DECOMP_C int __cdecl sub_00402190(void *L, int t);                  /* luaL_ref */
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);             /* lua_tonumber */
DECOMP_C char d_008CF080[];
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");

#define LS (*(void **)d_008CF080)
#define REG (-10000)

DECOMP(00560100)
void __thiscall f_00560100(void *this)
{
    char *s = (char *)this;
    void *L0 = LS;
    int top = sub_00402A60(L0), found = 0, kind;
    unsigned int key[7];
    float k;
    if (*(void **)(s + 0x2c)) {
        sub_00403390(LS, REG, *(int *)(*(char **)(s + 0x2c) + 0xc));
        kind = *(int *)(s + 0x30);
        if (kind == 0)
            sub_00403120(LS, imp_0060732C(s + 0x10));
        else if (kind == 1)
            sub_004030A0(LS, *(float *)(s + 0x34));
        while (sub_00403B00(LS, -2)) {
            if (sub_00402C20(LS, -1) == 5) {
                found = 1;
                break;
            }
            sub_00402A70(LS, -2);
        }
        if (*(int *)(s + 0xc) >= 0) {
            sub_00402270(LS, REG, *(int *)(s + 0xc));
            *(int *)(s + 0xc) = -1;
        }
        if (!found)
            *(int *)(s + 8) = 0;
        else {
            imp_006071E0(key);
            kind = sub_00402C20(LS, -2);
            if (kind == 4) {
                imp_006072F8(key, sub_00402ED0(LS, LS, -2, 0));
                sub_00402AC0(LS, -2);
                *(int *)(s + 0xc) = sub_00402190(LS, REG);
                imp_0060731C(s + 0x10, key);
                *(int *)(s + 0x30) = 0;
            } else if (kind == 3) {
                k = (float)sub_00402DE0(LS, -2);
                sub_00402AC0(LS, -2);
                *(int *)(s + 0xc) = sub_00402190(LS, REG);
                *(float *)(s + 0x34) = k;
                *(int *)(s + 0x30) = 1;
            } else
                *(int *)(s + 8) = 0;
            imp_00607330(key);
        }
    }
    if (sub_00402A60(L0) > top)
        sub_00402A70(L0, top);
}
