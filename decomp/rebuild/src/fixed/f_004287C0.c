/* 0x004287C0: registers the ambient sound manager userdata as the global named by arg 1 (kept at 0x006C8848):
 * builds the method table (filled by 0x00428740) and its metatable ("__tostring" 0x004273F0, "__eq" 0x00563020,
 * "__index" the method table), refs the metatable in the registry (the ref kept at 0x006BF4E4), makes a 4-byte
 * userdata holding arg 2, gives it the metatable and stores it in the globals. */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004033D0(void *L, int narr, int nrec);       /* lua_createtable */
DECOMP_C int __cdecl sub_00402A60(void *L);                            /* lua_gettop */
DECOMP_C void __cdecl sub_004030E0(void *L, const char *s, int n);     /* lua_pushlstring */
DECOMP_C void __cdecl sub_004031F0(void *L, void *fn, int n);          /* lua_pushcclosure */
DECOMP_C void __cdecl sub_004034C0(void *L, int index);                /* lua_settable */
DECOMP_C void __cdecl sub_00402BF0(void *L, int idx);                  /* lua_pushvalue */
DECOMP_C int __cdecl sub_00402190(void *L, int t);                     /* luaL_ref */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);                  /* lua_settop */
DECOMP_C void __cdecl sub_00403120(void *L, const char *s);            /* lua_pushstring */
DECOMP_C void *__cdecl sub_00403BF0(void *L, int size);                /* lua_newuserdata */
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);           /* lua_rawgeti */
DECOMP_C void __cdecl sub_004036B0(void *L, int idx);                  /* lua_setmetatable */
DECOMP_C void __cdecl sub_00428740(void);
DECOMP_C char d_008D122C[], d_006C8848[], d_006BF4E4[], d_0068A54C[], d_00689840[], d_00689864[],
                d_004273F0[], d_00563020[];

DECOMP(004287C0)
void __cdecl f_004287C0(const char *name, unsigned int value)
{
    void *L = *(void **)d_008D122C;
    int methods, meta;

    *(const char **)d_006C8848 = name;
    sub_004033D0(L, 0, 0);
    methods = sub_00402A60(L);
    sub_004033D0(L, 0, 0);
    meta = sub_00402A60(L);
    sub_004030E0(L, d_0068A54C, 10);
    sub_004031F0(L, d_004273F0, 0);
    sub_004034C0(L, meta);
    sub_004030E0(L, d_00689840, 4);
    sub_004031F0(L, d_00563020, 0);
    sub_004034C0(L, meta);
    sub_004030E0(L, d_00689864, 7);
    sub_00402BF0(L, methods);
    sub_004034C0(L, meta);
    *(int *)d_006BF4E4 = sub_00402190(L, -10000);
    sub_00428740();
    sub_00402A70(L, -2);
    sub_00403120(L, *(const char **)d_006C8848);
    *(unsigned int *)sub_00403BF0(L, 4) = value;
    sub_00403390(L, -10000, *(int *)d_006BF4E4);
    sub_004036B0(L, -2);
    sub_004034C0(L, -10002);
}
