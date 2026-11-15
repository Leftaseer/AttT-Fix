/* LuaGlobal_FindSaveFiles 0x0057EDE0: the saves the scripts can load: <data root>/Saves/game*.sav (0x00427990 + 0x20)
 * is enumerated, every game*.sav whose <stem>.bmp screenshot exists becomes a {stem, last-write time} entry, the
 * entries are sorted most recent first and their stems are pushed as a 1-based table.  A true top-of-stack value
 * asks for the newest save only: the auto-save slots "game0"/"game00" are left out and an empty name heads the
 * table (slot 1) so the entries start at 2. */
/* @conv - 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_57EDE0;                        /* std::string */
typedef struct {
    Str_57EDE0 name;              /* the stem */
    unsigned int unused;          /* the 8-byte write time is aligned */
    unsigned int timeLow, timeHigh;
} Save_57EDE0;                    /* 0x28 */
typedef struct { void *allocator; Save_57EDE0 *begin, *end, *capacity; } Vec_57EDE0;
typedef struct { unsigned int w[3]; } Tbl_57EDE0;                        /* nScript::Table */
typedef struct {
    unsigned int attributes, createdLow, createdHigh, accessedLow, accessedHigh;
    unsigned int writtenLow, writtenHigh, sizeHigh, sizeLow, reserved0, reserved1;
    char name[260], alternate[14];
} Find_57EDE0;                                                           /* WIN32_FIND_DATAA */

DECOMP_C int __cdecl sub_00402EA0(void *lua, int index);                 /* lua_toboolean */
DECOMP_C char *__cdecl sub_00427990(void);                               /* the data root object */
DECOMP_C void *__thiscall sub_00435E00(void *self, int allocator);       /* nScript::Table::Table */
DECOMP_C void __thiscall sub_004220A0(void *self);                       /* nScript::Table::~Table */
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);             /* lua_rawgeti */
DECOMP_C void __thiscall sub_0057E760(void *vec, int n);                 /* vector reserve */
DECOMP_C void __thiscall sub_0057ED20(void *vec, const void *element);   /* vector push_back */
DECOMP_C void __cdecl sub_0057EBF0(void *begin, void *end, int count);   /* vector sort */
DECOMP_C void __thiscall sub_0057BD40(void *table, int index, const char *value); /* Table::SetString(index) */
DECOMP_C void __cdecl sub_005E3E9C(void *p);                             /* operator delete */
DECOMP_C char d_008D122C[], d_00608F20[], d_0061DAB4[], d_00689D84[], d_0061AF9C[], d_0061AFC0[], d_00610FC8[], d_0060FA8B[];
DECOMP_C unsigned int *imp_006071C4 __asm__("__imp_?npos@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@2IB");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C unsigned int (__thiscall *imp_006071A4)(void *, const char *, unsigned int) __asm__("__imp_?rfind@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEIPBDI@Z");
DECOMP_C void *(__thiscall *imp_006071CC)(void *, void *, unsigned int, unsigned int) __asm__("__imp_?substr@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBE?AV12@II@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void *(__stdcall *imp_00607080)(const char *, Find_57EDE0 *) __asm__("__imp__FindFirstFileA@8");
DECOMP_C int (__stdcall *imp_00607084)(void *, Find_57EDE0 *) __asm__("__imp__FindNextFileA@8");
DECOMP_C int (__stdcall *imp_00607088)(void *) __asm__("__imp__FindClose@4");
DECOMP_C int (__stdcall *imp_006075F4)(const char *) __asm__("__imp__PathFileExistsA@4");

DECOMP(0057EDE0)
int __cdecl f_0057EDE0(void *lua)
{
    int savesOnly = sub_00402EA0(lua, -1) != 0;
    Str_57EDE0 folder, pattern;
    Vec_57EDE0 vec;
    Find_57EDE0 found;
    Tbl_57EDE0 table;
    void *handle;
    unsigned int i, count;
    imp_006071DC(&folder, sub_00427990() + 0x20, d_00608F20);            /* <root> + "Saves/" */
    imp_006071DC(&pattern, &folder, d_0061DAB4);                        /* + "game*.sav" */
    handle = imp_00607080(imp_0060732C(&pattern), &found);
    imp_00607330(&pattern);
    vec.allocator = 0;
    vec.begin = vec.end = vec.capacity = 0;
    sub_0057E760(&vec, 0x20);
    if (handle != (void *)-1) {
        for (;;) {
            Str_57EDE0 name, stem, dir, screenshot;
            unsigned int exists;
            imp_00607324(&name, found.name);
            imp_006071CC(&name, &stem, 0, imp_006071A4(&name, d_00689D84, *imp_006071C4)); /* stem = name before the last '.' */
            imp_0060731C(&name, &stem);
            imp_00607330(&stem);
            if (savesOnly && (imp_006071E4(&name, d_0061AF9C) || imp_006071E4(&name, d_0061AFC0)))
                goto skip;                                              /* "game0", "game00" */
            imp_006071C0(&dir, &folder, &name);
            imp_006071DC(&screenshot, &dir, d_00610FC8);                /* + ".bmp" */
            exists = imp_006075F4(imp_0060732C(&screenshot));
            imp_00607330(&screenshot);
            imp_00607330(&dir);
            if (!exists)
                goto skip;
            {
                Save_57EDE0 element;
                imp_006071E0(&element.name);
                imp_0060731C(&element.name, &name);
                element.timeLow = found.writtenLow;
                element.timeHigh = found.writtenHigh;
                sub_0057ED20(&vec, &element);
                imp_00607330(&element.name);
            }
        skip:
            imp_00607330(&name);
            if (!imp_00607084(handle, &found))
                break;
        }
        count = (unsigned int)((char *)vec.end - (char *)vec.begin) / 0x28;
        sub_0057EBF0(vec.begin, vec.end, count);
        imp_00607088(handle);
    }
    sub_00435E00(&table, 0);
    i = 1;
    if (savesOnly) {
        sub_0057BD40(&table, 1, d_0060FA8B);
        i = 2;
    }
    count = vec.begin ? (unsigned int)((char *)vec.end - (char *)vec.begin) / 0x28 : 0;
    for (unsigned int e = 0; e < count; e++, i++)
        sub_0057BD40(&table, (int)i, imp_0060732C(&vec.begin[e].name));
    sub_00403390(*(void **)d_008D122C, -10000, (int)table.w[2]);
    sub_004220A0(&table);
    if (vec.begin) {
        for (unsigned int e = 0; e < count; e++)
            imp_00607330(&vec.begin[e].name);
        sub_005E3E9C(vec.begin);
    }
    imp_00607330(&folder);
    return 1;
}
