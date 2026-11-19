/* 0x00519990: starts the end-battle screen (the level's +0x110 state becomes 2).  The script table "TacticLevel"
 * (0x004323E0, 0x0060AB58) is queried for "EndBattle" (0x0057B770, 0x00614024) and the value is called with no
 * arguments (0x0057A180, 0), the result and the value die through 0x00427820 / 0x004378D0 and the table through
 * 0x004220A0.  The status byte +0x118 is cleared, a 0x194-byte GUIScene is allocated (0x005E3EAE) and constructed
 * with the flag 1 (0x00582FA0); it is stored at +0x21C.  A fresh table (0x00435E00) gets the name argument's string
 * (the caller passes an std::string, its c_str through 0x0060732C) under "bgnd" (0x0057BDF0, 0x0061401C) and the
 * scene's vf3C is told to build it from a "Defeat" string (0x00614014, import ctor / dtor 0x00607324 / 0x00607330)
 * and that table (flag 1).  Then the game (+0x38) has the object at +0x80 reset (0x0046CF30) and its state +0xAC set
 * to 5, and the table dies last. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_519990;                 /* nScript::Table */
typedef struct { unsigned int w[6]; } Val_519990;                 /* nScript::Value (table at +8, Lua ref at +0x14) */
typedef struct { unsigned int w[6]; } Get_519990;                 /* nScript::TableGet */
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);   /* Table from a named global table */
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int flag);
DECOMP_C void __thiscall sub_00427820(void *self);                 /* nScript::TableGet::~TableGet */
DECOMP_C void __thiscall sub_004378D0(void *self);                 /* nScript::Value::~Value */
DECOMP_C int __thiscall sub_004220A0(void *self);                  /* nScript::Table::~Table */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);            /* operator new */
DECOMP_C void *__thiscall sub_00582FA0(void *self, int one);       /* GUIScene::GUIScene */
DECOMP_C void __thiscall sub_00435E00(void *self, int allocator);  /* nScript::Table::Table */
DECOMP_C void __thiscall sub_0057BDF0(void *self, const char *key, const char *value);
DECOMP_C void __thiscall sub_0046CF30(void *self);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C char d_0060AB58[], d_00614024[], d_0061401C[], d_00614014[];
typedef void (__thiscall *configure_519990)(void *self, void *name, void *value, int one);

DECOMP(00519990)
void __thiscall f_00519990(char *this, void *name)
{
    Tbl_519990 t1, t2;
    Val_519990 fn;
    Get_519990 res;
    unsigned int text[7];
    void *scene, *game;

    sub_004323E0(&t1, d_0060AB58);                                            /* "TacticLevel" */
    sub_0057A180(sub_0057B770(&t1, &fn, d_00614024), &res, 0);                /* "EndBattle"() */
    sub_00427820(&res);
    sub_004378D0(&fn);
    sub_004220A0(&t1);
    this[0x118] = 0;
    scene = sub_005E3EAE(0x194);
    scene = scene ? sub_00582FA0(scene, 1) : 0;
    *(void **)(this + 0x21c) = scene;
    sub_00435E00(&t2, 0);
    sub_0057BDF0(&t2, d_0061401C, imp_0060732C(name));                        /* "bgnd" */
    imp_00607324(text, d_00614014);                                           /* "Defeat" */
    ((configure_519990)(*(void ***)scene)[0x3c / 4])(scene, text, &t2, 1);
    imp_00607330(text);
    *(unsigned int *)(this + 0x110) = 2;
    game = *(void **)(this + 0x38);
    sub_0046CF30(*(void **)((char *)game + 0x80));
    *(unsigned int *)((char *)game + 0xac) = 5;
    sub_004220A0(&t2);
}
