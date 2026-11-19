/* 0x0053D840: the argument-less twin of 0x0053D600 (identical body, plain ret instead of ret 4): starts a
 * scripted battle scene.  A 0x194-byte scene (0x005E3EAE / 0x00582FA0 with 1) replaces the state's +0x110,
 * the old scene is not released and no reference count is raised.  The global "Unit" table's
 * "Hero" -> "BattleParams" -> "Magic" value (0x004323E0, 0x0057B4E0; 0x0060C088, 0x0060C080, 0x00613978,
 * 0x00614054) is copied into a fresh table (0x00435E00 / 0x0057BF50) as "Magic", "Scene" gets the
 * 0x0061ADFC function table (0x0057BDF0, 0x00613FD8), the same path's "Intelligence" float (0x0057AD40,
 * 0x00613960) becomes "CurIntelligence" (0x0057BC80, 0x0061403C) and "UnitName" is "Hero" (0x00614030).
 * The scene's vf3C gets a "SpellBook" string (0x00611AA0, imports 0x00607324 / 0x00607330) and that table
 * with flag 1; +0x118 becomes 2, then the game (+0x38) has the object at +0x80 reset (0x0046CF30) and
 * +0xAC set to 5.  The stacked table copies die in reverse order (0x004220A0). */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_53D840;                  /* nScript::Table */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void *__thiscall sub_00582FA0(void *self, int one);        /* GUIScene::GUIScene */
DECOMP_C void __thiscall sub_00435E00(void *self, int allocator);   /* nScript::Table::Table */
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, const void *value);
DECOMP_C void __thiscall sub_0057BDF0(void *self, const char *key, const char *value);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_0057BC80(void *self, const char *key, float value);
DECOMP_C int __thiscall sub_004220A0(void *self);                   /* nScript::Table::~Table */
DECOMP_C void __thiscall sub_0046CF30(void *self);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_0060C080[], d_0060C088[], d_00613978[], d_00614054[], d_00613FD8[];
DECOMP_C char d_00613960[], d_0061403C[], d_00614030[], d_00611AA0[], d_0061ADFC[];
typedef void (__thiscall *configure_53D840)(void *self, void *name, void *value, int one);

DECOMP(0053D840)
void __thiscall f_0053D840(char *this)
{
    Tbl_53D840 t, unit, hero, params, magic;
    unsigned int text[7];
    char *game;
    void *scene, *value;
    float number;

    scene = sub_005E3EAE(0x194);
    scene = scene ? sub_00582FA0(scene, 1) : 0;
    *(void **)(this + 0x110) = scene;
    sub_00435E00(&t, 0);
    value = sub_0057B4E0(sub_004323E0(&unit, d_0060C088), &hero, d_0060C080);     /* "Unit"/"Hero" */
    value = sub_0057B4E0(value, &params, d_00613978);                              /* "BattleParams" */
    value = sub_0057B4E0(value, &magic, d_00614054);                               /* "Magic" */
    sub_0057BF50(&t, d_00614054, value);                                           /* "Magic" */
    sub_004220A0(&magic);
    sub_004220A0(&params);
    sub_004220A0(&hero);
    sub_004220A0(&unit);
    sub_0057BDF0(&t, d_00613FD8, d_0061ADFC);                                      /* "Scene" */
    value = sub_0057B4E0(sub_004323E0(&unit, d_0060C088), &hero, d_0060C080);     /* "Unit"/"Hero" */
    value = sub_0057B4E0(value, &params, d_00613978);                              /* "BattleParams" */
    number = sub_0057AD40(value, d_00613960);                                      /* "Intelligence" */
    sub_0057BC80(&t, d_0061403C, number);                                          /* "CurIntelligence" */
    sub_004220A0(&params);
    sub_004220A0(&hero);
    sub_004220A0(&unit);
    sub_0057BDF0(&t, d_00614030, d_0060C080);                                      /* "UnitName" = "Hero" */
    imp_00607324(text, d_00611AA0);                                                /* "SpellBook" */
    ((configure_53D840)(*(void ***)scene)[0x3c / 4])(scene, text, &t, 1);
    imp_00607330(text);
    *(unsigned int *)(this + 0x118) = 2;
    game = *(char **)(this + 0x38);
    sub_0046CF30(*(void **)(game + 0x80));
    *(unsigned int *)(game + 0xac) = 5;
    sub_004220A0(&t);
}
