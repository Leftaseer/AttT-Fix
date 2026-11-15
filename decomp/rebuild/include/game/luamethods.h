/* The per-class script method tables: the classes' method inits fill a table of 16-byte entries
 * {name; 0; function; 0} (the last entry all zero) and then walk it, pushing every named function as a
 * closure whose upvalue is the entry.  Each init runs once behind a flag at 0x8D0FCC..; the derived classes
 * run their base class's init first.  Some modules add the shared table at 0x8D0FE8 or 0x8D1000 (empty in the
 * exe), and a few walk a shared table directly (0x8D1018, 0x8D1048, 0x8D1068, 0x8D1078, 0x8D1088, 0x6C76E0).
 * The registrars of luaclass.cpp run these (0x56FE20 runs the registrars). */
#pragma once
#include "game/common.h"

/* one entry of a class's method table */
struct LuaNamedMethod {
    const char *name;     /* +00, null ends the table */
    unsigned reserved04;  /* +04 */
    const void *function; /* +08 */
    unsigned reserved0C;  /* +0C */
};
static_assert(sizeof(LuaNamedMethod) == 16, "LuaNamedMethod is 16 bytes");

/* one entry of the 8-byte tables ({name; data}: the closure gets the data) */
struct LuaNamedFunction {
    const char *name; /* +00, null ends the table */
    const void *data; /* +04 */
};
static_assert(sizeof(LuaNamedFunction) == 8, "LuaNamedFunction is 8 bytes");

void FillLuaParticleSystemMethods(const void *methods); /* 0x569670 */
void FillLuaRenderObjectMethods(const void *methods); /* 0x5696D0 */
void FillLuaTacticCreatureMethods(const void *methods); /* 0x569730 */
void FillLuaWorldUnitMethods(const void *methods); /* 0x569790 */
void FillLuaParticleSystemMeshMethods(const void *methods); /* 0x5697F0 */
void FillLuaGuiElementMethods(const void *methods); /* 0x569850 */
void FillLuaImageMethods(const void *methods); /* 0x5698B0 */
void FillLuaSharedMethods(const void *methods); /* 0x569910 */
void FillLuaTextMethods(const void *methods); /* 0x569970 */
void FillLuaSharedMethods2(const void *methods); /* 0x5699D0 */
void FillLuaViewportMethods(const void *methods); /* 0x569A30 */
void FillLuaRectMethods(const void *methods); /* 0x569A90 */
void FillLuaChooseHeroRotatorMethods(const void *methods); /* 0x569AF0 */
void FillLuaGuiSceneClassMethods(const void *methods); /* 0x569B50 */
void FillLuaUnitIconMethods(const void *methods); /* 0x569BB0 */
void FillLuaTroopIconMethods(const void *methods); /* 0x569C10 */
void FillLuaButtonMethods(const void *methods); /* 0x569C70 */
void FillLuaGuiSceneClass2Methods(const void *methods); /* 0x569CD0 */
void FillLuaGuiSceneClass3Methods(const void *methods); /* 0x569D30 */
void FillLuaNpcMethods(const void *methods); /* 0x569D90 */
void FillLuaGuiSceneClassWorldMethods(const void *methods); /* 0x569DF0 */
void FillLuaMainMenuSceneMethods(const void *methods); /* 0x569E50 */
void FillLuaItemIconMethods(const void *methods); /* 0x569EB0 */
void FillLuaAttackSphereMethods(const void *methods); /* 0x569F70 */
void FillLuaEditorArmyMethods(const void *methods); /* 0x569FD0 */
void FillLuaToolTipMethods(const void *methods); /* 0x56A030 */
void FillLuaMessageMethods(const void *methods); /* 0x56A090 */
void FillLuaNpcListMethods(const void *methods); /* 0x56A0F0 */
void FillLuaEnemyArmyMethods(const void *methods); /* 0x56A150 */
void FillLuaUnitSoundManagerMethods(const void *methods); /* 0x4EDEF0 */
void FillLuaMusicManagerMethods(const void *methods); /* 0x47D470 */

void InitLuaParticleSystemMethods(); /* 0x56A1B0 */
void InitLuaRenderObjectMethods(); /* 0x56A300 */
void InitLuaTacticCreatureMethods(); /* 0x56A380 */
void InitLuaWorldUnitMethods(); /* 0x56A540 */
void InitLuaParticleSystemMeshMethods(); /* 0x56A880 */
void InitLuaGuiElementMethods(); /* 0x56AAA0 */
void InitLuaImageMethods(); /* 0x56AC10 */
void InitLuaTextMethods(); /* 0x56AD00 */
void InitLuaViewportMethods(); /* 0x56AEC0 */
void InitLuaGuiSceneClassMethods(); /* 0x56AFF0 */
void InitLuaUnitIconMethods(); /* 0x56B0C0 */
void InitLuaTroopIconMethods(); /* 0x56B1E0 */
void InitLuaButtonMethods(); /* 0x56B350 */
void InitLuaGuiSceneClass2Methods(); /* 0x56B3F0 */
void InitLuaGuiSceneClass3Methods(); /* 0x56B590 */
void InitLuaNpcMethods(); /* 0x56B6B0 */
void InitLuaGuiSceneClassWorldMethods(); /* 0x56B7F0 */
void InitLuaItemIconMethods(); /* 0x56B8C0 */
void InitLuaAttackSphereMethods(); /* 0x56B9A0 */
void InitLuaEnemyArmyMethods(); /* 0x56BB50 */
void InitLuaChooseHeroRotatorMethods(); /* 0x56F5E0 */
void InitLuaUnitSoundManagerMethods(); /* 0x4EE1C0 */
void InitLuaMusicManagerMethods(); /* 0x47DB60 */
