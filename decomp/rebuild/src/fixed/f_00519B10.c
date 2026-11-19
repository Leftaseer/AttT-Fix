/* 0x00519B10: starts the battle scene (the level state +0x110 becomes 1).  The current unit's data table
 * (0x00508770 copies the +0x3E4 table of the object reached through +0xBC -> +0x64 -> +0x58) supplies the
 * values: its "Magic" subtable (0x0057B4E0) goes into a fresh table (0x00435E00) under "Magic" (0x0057BF50,
 * 0x00614054), the string "Tactic" (0x0061404C) as "Scene" (0x0057BDF0, 0x00613FD8), its "Intelligence"
 * float (0x0057AD40, 0x00613960) as "CurIntelligence" (0x0057BC80, 0x0061403C) and the unit's name (the
 * string at +8 of the object) as "UnitName" (0x00614030).  A 0x194-byte scene (0x005E3EAE / 0x00582FA0 with
 * 1) gets its reference count +8 raised by one, the previous scene at +0x114 is released (its +4 object is
 * destroyed through vtable slot 0 with 1 when the count reaches zero) and replaced, the scene's vf3C is given
 * a "SpellBook" string (0x00611AA0, import ctor / dtor 0x00607324 / 0x00607330) and that table with flag 1,
 * and the game (+0x38) has the object at +0x80 reset (0x0046CF30) and +0xAC set to 5.  The table copies die
 * in reverse order (0x004220A0). */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_519B10;                 /* nScript::Table */
DECOMP_C void __thiscall sub_00508770(void *self, void *out);     /* copies the table at self+0x3E4 */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);            /* operator new */
DECOMP_C void *__thiscall sub_00582FA0(void *self, int one);       /* GUIScene::GUIScene */
DECOMP_C void __thiscall sub_00435E00(void *self, int allocator);  /* nScript::Table::Table */
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, const void *value);
DECOMP_C void __thiscall sub_0057BDF0(void *self, const char *key, const char *value);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_0057BC80(void *self, const char *key, float value);
DECOMP_C int __thiscall sub_004220A0(void *self);                  /* nScript::Table::~Table */
DECOMP_C void __thiscall sub_0046CF30(void *self);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C char d_00614054[], d_00613FD8[], d_0061404C[], d_00613960[], d_0061403C[], d_00614030[], d_00611AA0[];
typedef void (__thiscall *configure_519B10)(void *self, void *name, void *value, int one);
typedef void (__thiscall *del_519B10)(void *self, int del);

DECOMP(00519B10)
void __thiscall f_00519B10(char *this)
{
    Tbl_519B10 t, scan, part;
    unsigned int text[7];
    char *level, *holder, *unit, *game, *old;
    void *scene;
    float value;

    *(unsigned int *)(this + 0x110) = 1;
    level = *(char **)(this + 0xbc);
    holder = *(char **)(level + 0x64);
    unit = *(char **)*(void **)(holder + 0x58);
    sub_00508770(unit, &scan);
    scene = sub_005E3EAE(0x194);
    scene = scene ? sub_00582FA0(scene, 1) : 0;
    if (scene)
        *(int *)((char *)scene + 8) += 1;
    old = *(char **)(this + 0x114);
    if (old && !(*(int *)(old + 8) -= 1))
        ((del_519B10)(*(void ***)(old + 4))[0])(old + 4, 1);
    *(void **)(this + 0x114) = scene;
    sub_00435E00(&t, 0);
    sub_0057BF50(&t, d_00614054, sub_0057B4E0(&scan, &part, d_00614054));   /* "Magic" */
    sub_004220A0(&part);
    sub_0057BDF0(&t, d_00613FD8, d_0061404C);                               /* "Scene" = "Tactic" */
    value = sub_0057AD40(&scan, d_00613960);                                /* "Intelligence" */
    sub_0057BC80(&t, d_0061403C, value);                                    /* "CurIntelligence" */
    sub_0057BDF0(&t, d_00614030, imp_0060732C(unit + 8));                   /* "UnitName" */
    imp_00607324(text, d_00611AA0);                                         /* "SpellBook" */
    ((configure_519B10)(*(void ***)scene)[0x3c / 4])(scene, text, &t, 1);
    imp_00607330(text);
    game = *(char **)(this + 0x38);
    sub_0046CF30(*(void **)(game + 0x80));
    *(unsigned int *)(game + 0xac) = 5;
    sub_004220A0(&t);
    sub_004220A0(&scan);
}
