/* The script modules of the game classes: the shared registrar (the body of 0x56BC40 .. 0x56FB20; the LuaTrigger
 * one is 0x56E7B0 in luatrigger.cpp) and its per-class data.  The module name string is what 0x56FE20 passes and
 * what scripts see in _G. */
#include "game/common.h"
#include "game/lua.h"
#include "game/luaclass.h"
#include "game/trigger.h"

ORIG_FN(004030E0, void, (void *lua, const char *text, unsigned len)); /* lua_pushlstring */
ORIG_FN(004034F0, void, (void *lua, int index, const char *key));     /* lua_setfield */
ORIG_FN(0044E5A0, void *, ());                                        /* the usual collector singleton */
ORIG_THISCALL(00432620, void, (void *self, const char *fileName));    /* CLuaWrapper::DoFile */
ORIG_DATA(00562F60);                                                  /* the shared "__gc" */
ORIG_DATA(00563020);                                                  /* the shared "__eq" */

ORIG_DATA(008CF1D8);
ORIG_DATA(00564A10);
ORIG_DATA(00563150);
ORIG_DATA(00562F10);
ORIG_DATA(006C50C4);
ORIG_DATA(0056A1B0);
ORIG_DATA(008CF2E0);
ORIG_DATA(00564C80);
ORIG_DATA(00562F80);
ORIG_DATA(006C6898);
ORIG_DATA(0056A300);
ORIG_DATA(008CF3E8);
ORIG_DATA(00564EF0);
ORIG_DATA(00562FD0);
ORIG_DATA(006C3410);
ORIG_DATA(0056A380);
ORIG_DATA(006CA838);
ORIG_DATA(00565160);
ORIG_DATA(004ED100);
ORIG_DATA(006C2A2C);
ORIG_DATA(004EE1C0);
ORIG_DATA(008CF4F0);
ORIG_DATA(00565240);
ORIG_DATA(00563060);
ORIG_DATA(006C5030);
ORIG_DATA(0056A540);
ORIG_DATA(008CF5F8);
ORIG_DATA(005654B0);
ORIG_DATA(005630B0);
ORIG_DATA(006C16FC);
ORIG_DATA(0056A880);
ORIG_DATA(008CF700);
ORIG_DATA(00565720);
ORIG_DATA(00563100);
ORIG_DATA(006BF9A8);
ORIG_DATA(0056AAA0);
ORIG_DATA(008CF808);
ORIG_DATA(00565990);
ORIG_DATA(00563180);
ORIG_DATA(006C689C);
ORIG_DATA(0056AC10);
ORIG_DATA(008CF910);
ORIG_DATA(00565C00);
ORIG_DATA(005631D0);
ORIG_DATA(006C68A0);
ORIG_DATA(00569910);
ORIG_DATA(008D0FE8);
ORIG_DATA(008CFA18);
ORIG_DATA(00565E70);
ORIG_DATA(00563220);
ORIG_DATA(006C68A4);
ORIG_DATA(0056AD00);
ORIG_DATA(008CFB20);
ORIG_DATA(005660E0);
ORIG_DATA(00563270);
ORIG_DATA(006C0E48);
ORIG_DATA(005699D0);
ORIG_DATA(008D1000);
ORIG_DATA(008CFC28);
ORIG_DATA(00566350);
ORIG_DATA(005632C0);
ORIG_DATA(006C68A8);
ORIG_DATA(0056AEC0);
ORIG_DATA(008CFD30);
ORIG_DATA(005665C0);
ORIG_DATA(00563310);
ORIG_DATA(006C68AC);
ORIG_DATA(00569A90);
ORIG_DATA(008D1018);
ORIG_DATA(008CFF40);
ORIG_DATA(00566AA0);
ORIG_DATA(005633B0);
ORIG_DATA(006C68B4);
ORIG_DATA(0056AFF0);
ORIG_DATA(008D0048);
ORIG_DATA(00566D10);
ORIG_DATA(00563400);
ORIG_DATA(006C68B8);
ORIG_DATA(0056B0C0);
ORIG_DATA(008D0150);
ORIG_DATA(00566F80);
ORIG_DATA(00563450);
ORIG_DATA(006C68BC);
ORIG_DATA(0056B1E0);
ORIG_DATA(008D0258);
ORIG_DATA(005671F0);
ORIG_DATA(005634A0);
ORIG_DATA(006C68C0);
ORIG_DATA(0056B350);
ORIG_DATA(008D0360);
ORIG_DATA(00567460);
ORIG_DATA(005634F0);
ORIG_DATA(006C32C8);
ORIG_DATA(0056B3F0);
ORIG_DATA(008D0468);
ORIG_DATA(005676D0);
ORIG_DATA(00563540);
ORIG_DATA(006C3504);
ORIG_DATA(0056B590);
ORIG_DATA(008D0570);
ORIG_DATA(00567940);
ORIG_DATA(00563590);
ORIG_DATA(006C1EA8);
ORIG_DATA(0056B6B0);
ORIG_DATA(008D0678);
ORIG_DATA(00567BB0);
ORIG_DATA(005635E0);
ORIG_DATA(006C4FD8);
ORIG_DATA(0056B7F0);
ORIG_DATA(008D0780);
ORIG_DATA(00567E20);
ORIG_DATA(00563630);
ORIG_DATA(006C1008);
ORIG_DATA(00569E50);
ORIG_DATA(008D1048);
ORIG_DATA(008D0888);
ORIG_DATA(00568090);
ORIG_DATA(00563680);
ORIG_DATA(006C68C4);
ORIG_DATA(0056B8C0);
ORIG_DATA(008D0A98);
ORIG_DATA(00568570);
ORIG_DATA(00563720);
ORIG_DATA(006C3944);
ORIG_DATA(0056B9A0);
ORIG_DATA(008D0BA0);
ORIG_DATA(005687E0);
ORIG_DATA(00563770);
ORIG_DATA(006C68C8);
ORIG_DATA(00569FD0);
ORIG_DATA(008D1068);
ORIG_DATA(008D0CA8);
ORIG_DATA(00568A50);
ORIG_DATA(005637C0);
ORIG_DATA(006C68CC);
ORIG_DATA(0056A030);
ORIG_DATA(008D1078);
ORIG_DATA(008D0DB0);
ORIG_DATA(00568CC0);
ORIG_DATA(00563810);
ORIG_DATA(006C1390);
ORIG_DATA(0056A090);
ORIG_DATA(008D1088);
ORIG_DATA(006CA210);
ORIG_DATA(005690C0);
ORIG_DATA(0047CF50);
ORIG_DATA(006C146C);
ORIG_DATA(0047DB60);
ORIG_DATA(008D0FC0);
ORIG_DATA(005691A0);
ORIG_DATA(005638B0);
ORIG_DATA(006C0268);
ORIG_DATA(0056BB50);
ORIG_DATA(008CFE38);
ORIG_DATA(00566830);
ORIG_DATA(00563360);
ORIG_DATA(006C68B0);
ORIG_DATA(0056F5E0);
ORIG_DATA(008D0EB8);
ORIG_DATA(0056F9B0);
ORIG_DATA(0056FAE0);
ORIG_DATA(00563860);
ORIG_DATA(006C1600);
ORIG_DATA(0056A0F0);
ORIG_DATA(006C76E0);

void RegisterLuaClassModule(const char *name, const LuaClassModule &module)
{
    void *lua = g_luaState;
    *module.nameSlot = name;
    ORIG_CALL(00403120)(lua, name);
    ORIG_CALL(004033D0)(lua, 0, 0);
    int moduleTable = ORIG_CALL(00402A60)(lua);
    ORIG_CALL(004030E0)(lua, d_006114AC, 3);                  /* "new" */
    ORIG_CALL(004031F0)(lua, (void *)module.create, 0);
    ORIG_CALL(004034C0)(lua, moduleTable);
    ORIG_CALL(004034C0)(lua, kLuaGlobalsIndex);
    ORIG_CALL(004033D0)(lua, 0, 0);
    int methods = ORIG_CALL(00402A60)(lua);
    ORIG_CALL(004033D0)(lua, 0, 0);
    int metatable = ORIG_CALL(00402A60)(lua);
    ORIG_CALL(004030E0)(lua, d_0060CA4C, 6);                  /* "delete" */
    ORIG_CALL(004031F0)(lua, (void *)module.remove, 0);
    ORIG_CALL(004034C0)(lua, methods);
    ORIG_CALL(004030E0)(lua, d_0068A54C, 10);                 /* "__tostring" */
    ORIG_CALL(004031F0)(lua, (void *)module.tostring, 0);
    ORIG_CALL(004034C0)(lua, metatable);
    ORIG_CALL(004030E0)(lua, d_00689840, 4);                  /* "__eq" */
    ORIG_CALL(004031F0)(lua, (void *)d_00563020, 0);
    ORIG_CALL(004034C0)(lua, metatable);
    ORIG_CALL(004030E0)(lua, d_00689850, 4);                  /* "__gc" */
    ORIG_CALL(004031F0)(lua, (void *)d_00562F60, 0);
    ORIG_CALL(004034C0)(lua, metatable);
    ORIG_CALL(004030E0)(lua, d_00689864, 7);                  /* "__index" */
    ORIG_CALL(00402BF0)(lua, methods);
    ORIG_CALL(004034C0)(lua, metatable);
    *module.metatableRef = ORIG_CALL(00402190)(lua, kLuaRegistryIndex);
    for (const LuaModuleFiller *filler = module.fill; filler->function; ++filler)
        ((void (__cdecl *)(const void *))filler->function)(filler->data);
    ORIG_CALL(00402A70)(lua, -2);
}

DECOMP(0056BC40)
void RegisterLuaParticleSystemModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056A1B0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF1D8,
                              (const void *)d_00564A10,
                              (const void *)d_00563150,
                              (const void *)d_00562F10,
                              (int *)d_006C50C4,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056BE20)
void RegisterLuaRenderObjectModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056A300, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF2E0,
                              (const void *)d_00564C80,
                              (const void *)d_00563150,
                              (const void *)d_00562F80,
                              (int *)d_006C6898,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056C000)
void RegisterLuaTacticCreatureModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056A380, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF3E8,
                              (const void *)d_00564EF0,
                              (const void *)d_00563150,
                              (const void *)d_00562FD0,
                              (int *)d_006C3410,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056C1E0)
void RegisterLuaUnitSoundManagerModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_004EE1C0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_006CA838,
                              (const void *)d_00565160,
                              (const void *)d_00563150,
                              (const void *)d_004ED100,
                              (int *)d_006C2A2C,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056C3C0)
void RegisterLuaWorldUnitModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056A540, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF4F0,
                              (const void *)d_00565240,
                              (const void *)d_00563150,
                              (const void *)d_00563060,
                              (int *)d_006C5030,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056C5A0)
void RegisterLuaParticleSystemMeshModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056A880, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF5F8,
                              (const void *)d_005654B0,
                              (const void *)d_00563150,
                              (const void *)d_005630B0,
                              (int *)d_006C16FC,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056C780)
void RegisterLuaGUIElementModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AAA0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF700,
                              (const void *)d_00565720,
                              (const void *)d_00563150,
                              (const void *)d_00563100,
                              (int *)d_006BF9A8,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056C960)
void RegisterLuaImageModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AC10, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF808,
                              (const void *)d_00565990,
                              (const void *)d_00563150,
                              (const void *)d_00563180,
                              (int *)d_006C689C,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056CB40)
void RegisterLuaButtonContourModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AC10, nullptr },
        { (const void *)d_00569910, (const void *)d_008D0FE8 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CF910,
                              (const void *)d_00565C00,
                              (const void *)d_00563150,
                              (const void *)d_005631D0,
                              (int *)d_006C68A0,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056CD30)
void RegisterLuaTextModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AD00, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CFA18,
                              (const void *)d_00565E70,
                              (const void *)d_00563150,
                              (const void *)d_00563220,
                              (int *)d_006C68A4,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056CF10)
void RegisterLuaButtonAlphaModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AC10, nullptr },
        { (const void *)d_00569910, (const void *)d_008D0FE8 },
        { (const void *)d_005699D0, (const void *)d_008D1000 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CFB20,
                              (const void *)d_005660E0,
                              (const void *)d_00563150,
                              (const void *)d_00563270,
                              (int *)d_006C0E48,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056D110)
void RegisterLuaViewportModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AEC0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CFC28,
                              (const void *)d_00566350,
                              (const void *)d_00563150,
                              (const void *)d_005632C0,
                              (int *)d_006C68A8,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056D2F0)
void RegisterLuaRectModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AAA0, nullptr },
        { (const void *)d_00569A90, (const void *)d_008D1018 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CFD30,
                              (const void *)d_005665C0,
                              (const void *)d_00563150,
                              (const void *)d_00563310,
                              (int *)d_006C68AC,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056D4E0)
void RegisterLuaGUISceneClassModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AFF0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CFF40,
                              (const void *)d_00566AA0,
                              (const void *)d_00563150,
                              (const void *)d_005633B0,
                              (int *)d_006C68B4,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056D6C0)
void RegisterLuaUnitIconModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B0C0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0048,
                              (const void *)d_00566D10,
                              (const void *)d_00563150,
                              (const void *)d_00563400,
                              (int *)d_006C68B8,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056D8A0)
void RegisterLuaTroopIconModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B1E0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0150,
                              (const void *)d_00566F80,
                              (const void *)d_00563150,
                              (const void *)d_00563450,
                              (int *)d_006C68BC,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056DA80)
void RegisterLuaButtonModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B350, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0258,
                              (const void *)d_005671F0,
                              (const void *)d_00563150,
                              (const void *)d_005634A0,
                              (int *)d_006C68C0,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056DC60)
void RegisterLuaGUISceneClass2Module(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B3F0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0360,
                              (const void *)d_00567460,
                              (const void *)d_00563150,
                              (const void *)d_005634F0,
                              (int *)d_006C32C8,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056DE40)
void RegisterLuaGUISceneClass3Module(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B590, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0468,
                              (const void *)d_005676D0,
                              (const void *)d_00563150,
                              (const void *)d_00563540,
                              (int *)d_006C3504,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056E020)
void RegisterLuaCNpcModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B6B0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0570,
                              (const void *)d_00567940,
                              (const void *)d_00563150,
                              (const void *)d_00563590,
                              (int *)d_006C1EA8,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056E200)
void RegisterLuaGUISceneClassWorldModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B7F0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0678,
                              (const void *)d_00567BB0,
                              (const void *)d_00563150,
                              (const void *)d_005635E0,
                              (int *)d_006C4FD8,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056E3E0)
void RegisterLuaMainMenuSceneClassModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AFF0, nullptr },
        { (const void *)d_00569E50, (const void *)d_008D1048 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0780,
                              (const void *)d_00567E20,
                              (const void *)d_00563150,
                              (const void *)d_00563630,
                              (int *)d_006C1008,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056E5D0)
void RegisterLuaItemIconModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B8C0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0888,
                              (const void *)d_00568090,
                              (const void *)d_00563150,
                              (const void *)d_00563680,
                              (int *)d_006C68C4,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056E9A0)
void RegisterLuaAttackSphereModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056B9A0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0A98,
                              (const void *)d_00568570,
                              (const void *)d_00563150,
                              (const void *)d_00563720,
                              (int *)d_006C3944,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056EB80)
void RegisterLuaEditorArmyModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_00569FD0, (const void *)d_008D1068 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0BA0,
                              (const void *)d_005687E0,
                              (const void *)d_00563150,
                              (const void *)d_00563770,
                              (int *)d_006C68C8,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056ED70)
void RegisterLuaToolTipModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056AD00, nullptr },
        { (const void *)d_0056A030, (const void *)d_008D1078 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0CA8,
                              (const void *)d_00568A50,
                              (const void *)d_00563150,
                              (const void *)d_005637C0,
                              (int *)d_006C68CC,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056EF60)
void RegisterLuaMessageModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056A090, (const void *)d_008D1088 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0DB0,
                              (const void *)d_00568CC0,
                              (const void *)d_00563150,
                              (const void *)d_00563810,
                              (int *)d_006C1390,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056F150)
void RegisterLuaMusicManagerModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0047DB60, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_006CA210,
                              (const void *)d_005690C0,
                              (const void *)d_00563150,
                              (const void *)d_0047CF50,
                              (int *)d_006C146C,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056F330)
void RegisterLuaEnemyArmyModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056BB50, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0FC0,
                              (const void *)d_005691A0,
                              (const void *)d_00563150,
                              (const void *)d_005638B0,
                              (int *)d_006C0268,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056F7D0)
void RegisterLuaChooseHeroRotatorModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056F5E0, nullptr },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008CFE38,
                              (const void *)d_00566830,
                              (const void *)d_00563150,
                              (const void *)d_00563360,
                              (int *)d_006C68B0,
                              fill };
    RegisterLuaClassModule(name, module);
}

DECOMP(0056FB20)
void RegisterLuaNPCListModule(const char *name)
{
    const LuaModuleFiller fill[] = {
        { (const void *)d_0056A0F0, (const void *)d_006C76E0 },
        { nullptr, nullptr },
    };
    LuaClassModule module = { (const char **)d_008D0EB8,
                              (const void *)d_0056F9B0,
                              (const void *)d_0056FAE0,
                              (const void *)d_00563860,
                              (int *)d_006C1600,
                              fill };
    RegisterLuaClassModule(name, module);
}

ORIG_DATA(006C88D4); /* CLuaWrapper */
ORIG_DATA(00563CC0); /* "String" the scripts get */
ORIG_DATA(00563DD0); /* "LuaWrapper" */
ORIG_DATA(00563ED0); /* "CWorldHero" */
ORIG_DATA(00563FE0); /* "CBorder" */
ORIG_DATA(00610484);
ORIG_DATA(0061CEF0);
ORIG_DATA(0060BF28);
ORIG_DATA(00614A84);
ORIG_DATA(006CA98C);
ORIG_DATA(008D0FC4);
ORIG_DATA(006CAAC8);
ORIG_DATA(008D0FC8);
ORIG_DATA(0061CC44);
ORIG_DATA(0061CC54);
ORIG_DATA(0061CC64);
ORIG_DATA(0061CC74);
ORIG_DATA(0061CC88);
ORIG_DATA(0061CC94);
ORIG_DATA(0061CC9C);
ORIG_DATA(00611ADC);
ORIG_DATA(0061CCAC);
ORIG_DATA(0061CCB8);
ORIG_DATA(0061CCC4);
ORIG_DATA(0061CDC0);
ORIG_DATA(0061CD08);
ORIG_DATA(0061CD18);
ORIG_DATA(0061CD24);
ORIG_DATA(0061CD30);
ORIG_DATA(0061CD54);
ORIG_DATA(0060C26C);
ORIG_DATA(0061CD68);
ORIG_DATA(0061CD74);
ORIG_DATA(0061CD80);
ORIG_DATA(0061CD90);
ORIG_DATA(0061CD38);
ORIG_DATA(0061CDA4);
ORIG_DATA(0061CD40);
ORIG_DATA(0061CDD4);
ORIG_DATA(0061CD9C);
ORIG_DATA(0060AE90);
ORIG_DATA(00612C28);
ORIG_DATA(0061CDB4);
ORIG_DATA(0061CDDC);

/* 0x562A50: runs the script file the std::string names (the game's DoFile takes the c_str) */
DECOMP(00562A50)
void RunLuaFile(const std::string *fileName)
{
    ORIG_CALL(00432620)(ORIG_VAR(006C88D4, void *), fileName->c_str());
}

/* 0x56FE20: on the first call, the four bindings the scripts use (std::string, the wrapper itself, the world
 * hero and the border) enter _G, then every class module is registered by name and MainInit runs. */
DECOMP(0056FE20)
void __fastcall RegisterLuaModules(LuaModuleInit *init)
{
    if (!init->pending)
        return;
    init->pending = false;
    void *lua = g_luaState;
    ORIG_CALL(004031F0)(lua, (void *)d_00563CC0, 0);
    ORIG_CALL(004034F0)(lua, kLuaGlobalsIndex, d_00610484); /* "String" */
    ORIG_VAR(006CA98C, void *) = ORIG_CALL(0044E5A0)();
    ORIG_CALL(004031F0)(lua, (void *)d_00563DD0, 0);
    ORIG_CALL(004034F0)(lua, kLuaGlobalsIndex, d_0061CEF0); /* "LuaWrapper" */
    ORIG_VAR(008D0FC4, void *) = ORIG_CALL(0044E5A0)();
    ORIG_CALL(004031F0)(lua, (void *)d_00563ED0, 0);
    ORIG_CALL(004034F0)(lua, kLuaGlobalsIndex, d_0060BF28); /* "CWorldHero" */
    ORIG_VAR(006CAAC8, void *) = ORIG_CALL(0044E5A0)();
    ORIG_CALL(004031F0)(lua, (void *)d_00563FE0, 0);
    ORIG_CALL(004034F0)(lua, kLuaGlobalsIndex, d_00614A84); /* "CBorder" */
    ORIG_VAR(008D0FC8, void *) = ORIG_CALL(0044E5A0)();

    RegisterLuaParticleSystemMeshModule(d_0061CC74);
    RegisterLuaGUIElementModule(d_0061CC88);
    RegisterLuaImageModule(d_0061CC94);
    RegisterLuaButtonContourModule(d_0061CC9C);
    RegisterLuaTextModule(d_00611ADC);
    RegisterLuaButtonAlphaModule(d_0061CCAC);
    RegisterLuaViewportModule(d_0061CCB8);
    RegisterLuaRectModule(d_0061CCC4);
    RegisterLuaParticleSystemModule(d_0061CC44);
    RegisterLuaRenderObjectModule(d_0061CC54);
    RegisterLuaChooseHeroRotatorModule(d_0061CDC0);
    RegisterLuaGUISceneClassModule(d_0061CD08);
    RegisterLuaUnitIconModule(d_0061CD18);
    RegisterLuaTroopIconModule(d_0061CD24);
    RegisterLuaButtonModule(d_0061CD30);
    RegisterLuaMainMenuSceneClassModule(d_0061CD54);
    RegisterLuaWorldUnitModule(d_0060C26C);
    RegisterLuaItemIconModule(d_0061CD68);
    RegisterLuaTriggerModule(d_0061CD74);
    RegisterLuaAttackSphereModule(d_0061CD80);
    RegisterLuaEditorArmyModule(d_0061CD90);
    RegisterLuaCNpcModule(d_0061CD38);
    RegisterLuaMessageModule(d_0061CDA4);
    RegisterLuaGUISceneClass3Module(d_0061CD08);
    RegisterLuaGUISceneClassWorldModule(d_0061CD40);
    RegisterLuaNPCListModule(d_0061CDD4);
    RegisterLuaTacticCreatureModule(d_0061CC64);
    RegisterLuaToolTipModule(d_0061CD9C);
    RegisterLuaMusicManagerModule(d_0060AE90);
    RegisterLuaUnitSoundManagerModule(d_00612C28);
    RegisterLuaGUISceneClass2Module(d_0061CD08);
    RegisterLuaEnemyArmyModule(d_0061CDB4);

    std::string mainInit(d_0061CDDC);
    RunLuaFile(&mainInit);
}

ORIG_FN(005E3EAE, void *, (unsigned int size)); /* operator new, through the original thunk */
ORIG_THISCALL(004AFEF0, void *, (void *self, void *lua, void *collector)); /* CRenderString */
ORIG_THISCALL(00571130, void *, (void *self, void *lua, void *collector)); /* the LuaWrapper object */
ORIG_THISCALL(00465950, void *, (void *self, void *lua, void *collector)); /* CHero */
ORIG_THISCALL(00525B50, void *, (void *self, void *lua, void *collector)); /* CBorder */

ORIG_DATA(0061048C); /* String's first method name (none in this build) */
ORIG_DATA(00610494); /* String's {name, function} entries from the second one */
ORIG_DATA(00563900); /* String's method dispatcher */
ORIG_DATA(0061CF00); /* LuaWrapper's first method name */
ORIG_DATA(0061CF08);
ORIG_DATA(00563950);
ORIG_DATA(006C0AC8); /* CWorldHero's first method name */
ORIG_DATA(006C0AD8);
ORIG_DATA(005639A0);
ORIG_DATA(006C3960); /* CBorder's first method name */
ORIG_DATA(006C3968);
ORIG_DATA(005639F0);

/* 0x563CC0, 0x563DD0, 0x563ED0, 0x563FE0: the closures _G.String, _G.LuaWrapper, _G.CWorldHero and _G.CBorder
 * hold.  Each returns the class's method table; every method's value is the class's dispatcher closure, carrying
 * the method's index as its upvalue (the dispatcher then finds the implementation in the class's table), and the
 * table's [0] is a fresh wrapper around the collector object.  A class without a collector yields nil. */
struct LuaBindingTable {
    const char *first;         /* the first method's name, in the class's own global */
    const char *const *names;  /* the second method's name; the entries are "stride" bytes apart */
    unsigned stride;
    const void *dispatcher;
};

static void PushBindingTable(void *lua, const LuaBindingTable &table)
{
    ORIG_CALL(004033D0)(lua, 0, 0);
    const char *name = table.first;
    for (int index = 0; name; ++index) {
        ORIG_CALL(00403120)(lua, name);
        ORIG_CALL(004030A0)(lua, (float)index);
        ORIG_CALL(004031F0)(lua, (void *)table.dispatcher, 1);
        ORIG_CALL(004034C0)(lua, -3);
        name = *(const char *const *)((const char *)table.names + index * table.stride);
    }
}

DECOMP(00563CC0)
int __cdecl LuaStringBinding(void *lua)
{
    if (ORIG_VAR(006CA98C, void *) == nullptr) {
        ORIG_CALL(00403080)(lua);
        return 1;
    }
    LuaBindingTable table = { ORIG_VAR(0061048C, const char *), (const char *const *)d_00610494, 8,
                              (const void *)d_00563900 };
    PushBindingTable(lua, table);
    void *wrapper = ORIG_CALL(005E3EAE)(0x254);
    if (wrapper)
        wrapper = ORIG_CALL(004AFEF0)(wrapper, lua, ORIG_VAR(006CA98C, void *));
    ORIG_CALL(004032A0)(lua, wrapper);
    ORIG_CALL(00403610)(lua, -2, 0);
    return 1;
}

DECOMP(00563DD0)
int __cdecl LuaWrapperBinding(void *lua)
{
    if (ORIG_VAR(008D0FC4, void *) == nullptr) {
        ORIG_CALL(00403080)(lua);
        return 1;
    }
    LuaBindingTable table = { ORIG_VAR(0061CF00, const char *), (const char *const *)d_0061CF08, 8,
                              (const void *)d_00563950 };
    PushBindingTable(lua, table);
    void *wrapper = ORIG_CALL(005E3EAE)(0x38);
    if (wrapper)
        wrapper = ORIG_CALL(00571130)(wrapper, lua, ORIG_VAR(008D0FC4, void *));
    ORIG_CALL(004032A0)(lua, wrapper);
    ORIG_CALL(00403610)(lua, -2, 0);
    return 1;
}

DECOMP(00563ED0)
int __cdecl LuaWorldHeroBinding(void *lua)
{
    if (ORIG_VAR(006CAAC8, void *) == nullptr) {
        ORIG_CALL(00403080)(lua);
        return 1;
    }
    LuaBindingTable table = { ORIG_VAR(006C0AC8, const char *), (const char *const *)d_006C0AD8, 16,
                              (const void *)d_005639A0 };
    PushBindingTable(lua, table);
    void *wrapper = ORIG_CALL(005E3EAE)(0x508);
    if (wrapper)
        wrapper = ORIG_CALL(00465950)(wrapper, lua, ORIG_VAR(006CAAC8, void *));
    ORIG_CALL(004032A0)(lua, wrapper);
    ORIG_CALL(00403610)(lua, -2, 0);
    return 1;
}

DECOMP(00563FE0)
int __cdecl LuaBorderBinding(void *lua)
{
    if (ORIG_VAR(008D0FC8, void *) == nullptr) {
        ORIG_CALL(00403080)(lua);
        return 1;
    }
    LuaBindingTable table = { ORIG_VAR(006C3960, const char *), (const char *const *)d_006C3968, 8,
                              (const void *)d_005639F0 };
    PushBindingTable(lua, table);
    void *wrapper = ORIG_CALL(005E3EAE)(0xC8);
    if (wrapper)
        wrapper = ORIG_CALL(00525B50)(wrapper, lua, ORIG_VAR(008D0FC8, void *));
    ORIG_CALL(004032A0)(lua, wrapper);
    ORIG_CALL(00403610)(lua, -2, 0);
    return 1;
}
