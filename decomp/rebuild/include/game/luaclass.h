/* The per-class script modules: every registrar builds the module table in _G (its "new" builds the class),
 * the class's metatable in the registry (+ "delete", "__tostring", "__eq", "__gc", "__index" -> the methods
 * table) and then runs the class's fillers (an init of the class's own function table, then the shared
 * {name; data} adders).  0x56FE20 registers them all.
 *
 * The registrars share their whole body; only the data below differs.  Three of them all register under the
 * script name GUISceneClass (the last registration wins in _G). */
#pragma once
#include "game/common.h"

/* one call of the fill phase: the function and its argument (null when it takes none) */
struct LuaModuleFiller {
    const void *function;
    const void *data;
};

/* the one-shot object 0x563C90 builds for 0x56FE20: its +8 byte keeps the registration from running twice */
struct LuaModuleInit {
    void *vftable;  /* +00 */
    int unknown04;  /* +04 */
    bool pending;   /* +08 */
};

/* one registrar's data; fill is a null-function-terminated array */
struct LuaClassModule {
    const char **nameSlot;           /* the global that keeps the module name */
    const void *create;              /* "new" */
    const void *remove;              /* "delete" */
    const void *tostring;            /* "__tostring" */
    int *metatableRef;               /* the registry reference of the metatable */
    const LuaModuleFiller *fill;
};

void RegisterLuaClassModule(const char *name, const LuaClassModule &module);

void __fastcall RegisterLuaModules(LuaModuleInit *init); /* 0x56FE20 registers every module once */
void RunLuaFile(const std::string *fileName);      /* 0x562A50 CLuaWrapper::DoFile(fileName) */

void RegisterLuaParticleSystemModule(const char *name); /* 0x56BC40 */
void RegisterLuaRenderObjectModule(const char *name); /* 0x56BE20 */
void RegisterLuaTacticCreatureModule(const char *name); /* 0x56C000 */
void RegisterLuaUnitSoundManagerModule(const char *name); /* 0x56C1E0 */
void RegisterLuaWorldUnitModule(const char *name); /* 0x56C3C0 */
void RegisterLuaParticleSystemMeshModule(const char *name); /* 0x56C5A0 */
void RegisterLuaGUIElementModule(const char *name); /* 0x56C780 */
void RegisterLuaImageModule(const char *name); /* 0x56C960 */
void RegisterLuaButtonContourModule(const char *name); /* 0x56CB40 */
void RegisterLuaTextModule(const char *name); /* 0x56CD30 */
void RegisterLuaButtonAlphaModule(const char *name); /* 0x56CF10 */
void RegisterLuaViewportModule(const char *name); /* 0x56D110 */
void RegisterLuaRectModule(const char *name); /* 0x56D2F0 */
void RegisterLuaGUISceneClassModule(const char *name); /* 0x56D4E0 */
void RegisterLuaUnitIconModule(const char *name); /* 0x56D6C0 */
void RegisterLuaTroopIconModule(const char *name); /* 0x56D8A0 */
void RegisterLuaButtonModule(const char *name); /* 0x56DA80 */
void RegisterLuaGUISceneClass2Module(const char *name); /* 0x56DC60 */
void RegisterLuaGUISceneClass3Module(const char *name); /* 0x56DE40 */
void RegisterLuaCNpcModule(const char *name); /* 0x56E020 */
void RegisterLuaGUISceneClassWorldModule(const char *name); /* 0x56E200 */
void RegisterLuaMainMenuSceneClassModule(const char *name); /* 0x56E3E0 */
void RegisterLuaItemIconModule(const char *name); /* 0x56E5D0 */
void RegisterLuaAttackSphereModule(const char *name); /* 0x56E9A0 */
void RegisterLuaEditorArmyModule(const char *name); /* 0x56EB80 */
void RegisterLuaToolTipModule(const char *name); /* 0x56ED70 */
void RegisterLuaMessageModule(const char *name); /* 0x56EF60 */
void RegisterLuaMusicManagerModule(const char *name); /* 0x56F150 */
void RegisterLuaEnemyArmyModule(const char *name); /* 0x56F330 */
void RegisterLuaChooseHeroRotatorModule(const char *name); /* 0x56F7D0 */
void RegisterLuaNPCListModule(const char *name); /* 0x56FB20 */
