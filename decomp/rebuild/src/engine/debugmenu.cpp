/* Debug menu of the debug build (DECOMP_DEBUG_MENU): a small Win32 window with the manual test actions of the
 * playtest builds -- the barracks with any unit of the game, every spell of the hero, and a battle against an army
 * whose units get +100000 health.  The actions are Lua chunks handed to DecompQueueLua (engine.cpp), which TestLua
 * runs at the end of a frame, where the game's own script handlers run; a scene switch between frames would leave
 * the engine without a scene for the next one.
 *
 * The window and the game window belong to one process, so Windows sends no WM_ACTIVATEAPP when the focus moves
 * between them: the game keeps running its frame loop and its DirectInput.  The window therefore pauses the game
 * itself while it has the focus (WM_ACTIVATE), and the main loop's wait condition (main.cpp) takes the flag into
 * account.  Focusing the game window again (the buttons do it after queueing) resumes the game. */
#ifdef DECOMP_DEBUG_MENU

#ifndef DECOMP_TEST_INPUT
#error DECOMP_DEBUG_MENU hands its Lua chunks to the test-input queue (DecompQueueLua, engine.cpp): build with DECOMP_TEST_INPUT too
#endif

#include "game/common.h"
#include "game/globals.h"
#include "game/engine.h"

extern "C" bool DecompQueueLua(const char *chunk);      /* engine.cpp: a Lua chunk for the end of a frame */
extern "C" int __cdecl DecompDebugMenuLua(void *L);      /* registered as DecompDbg in TestLua */

static HWND g_menu, g_status, g_list;
static HICON g_icon;
static HCURSOR g_arrow;
static bool g_created, g_visible, g_paused;
static int g_cursorShows;                               /* ShowCursor calls made to bring the count to >= 0 */
static int g_unitIndex = -1;                            /* the unit selected in the list */

/* ---------------------------------------------------------------------------------------------------------------
 * Status: the last lines DecompDbg() was called with (four, oldest first), shown in the window. */

static const int kStatusLines = 4;
static const int kStatusChars = 110;
static char g_lines[kStatusLines][kStatusChars];
static int g_lineCount;
static char g_text[kStatusLines * (kStatusChars + 2) + 1];

static void CopyStr(char *dst, int size, const char *src)
{
    int i = 0;
    for (; src[i] && i < size - 1; i++)
        dst[i] = src[i];
    dst[i] = 0;
}

static void RefreshStatus()
{
    if (!g_status)
        return;
    int n = 0;
    for (int i = 0; i < g_lineCount; i++) {
        for (const char *p = g_lines[i]; *p && n < (int)sizeof(g_text) - 3; p++)
            g_text[n++] = *p;
        if (i + 1 < g_lineCount) {
            g_text[n++] = '\r';
            g_text[n++] = '\n';
        }
    }
    g_text[n] = 0;
    wchar_t wide[sizeof(g_text)];
    MultiByteToWideChar(CP_ACP, 0, g_text, -1, wide, (int)(sizeof(wide) / sizeof(wide[0])));
    SetWindowTextW(g_status, wide);
}

static void AddStatus(const char *text)
{
    if (g_lineCount == kStatusLines) {
        for (int i = 1; i < kStatusLines; i++)
            CopyStr(g_lines[i - 1], kStatusChars, g_lines[i]);
        g_lineCount = kStatusLines - 1;
    }
    CopyStr(g_lines[g_lineCount++], kStatusChars, text);
    RefreshStatus();
#ifdef DECOMP_DEBUG_LOG
    DebugLog(text);
#endif
}

/* DecompDbg(text) from Lua (TestLua registers it on the lua_State of the game): a line in the window and in
 * decomp_debug.log.  The stack layout is the one of DecompLogLua: L->base at +12, a string TValue at +0 (a TString
 * pointer, its characters after the 16-byte header) and its type at +4 (4 = LUA_TSTRING). */
extern "C" int __cdecl DecompDebugMenuLua(void *L)
{
    char *v = *(char **)((char *)L + 12);
    if (v < *(char **)((char *)L + 8) && *(int *)(v + 4) == 4)
        AddStatus(*(char **)v + 16);
    else
        AddStatus("DecompDbg: no string argument");
    return 0;
}

/* ---------------------------------------------------------------------------------------------------------------
 * Pausing: the menu's WM_ACTIVATE, the main loop asks DecompDebugMenuPaused(). */

extern "C" bool DecompDebugMenuPaused()
{
    return g_paused;
}

static void PauseGame()
{
    if (g_paused)
        return;
    g_paused = true;
    if (g_engine)
        g_engine->SetActive(false);         /* silences the music, stops the frame timer (as an inactive window does) */
    ClipCursor(nullptr);
    /* The game sets the cursor to NULL (0x443C00 / 0x443E80 keep a saved cursor and clear it every step), so while
     * the menu has the focus there is no cursor at all.  Bring the display count to >= 0 and set the arrow: the game
     * is not stepping now, so nothing clears it again.  -nologo launches leave the count at -1 (0x44F7BB). */
    g_cursorShows = 0;
    for (;;) {
        int n = ShowCursor(TRUE);
        g_cursorShows++;
        if (n >= 0)
            break;
    }
    SetCursor(g_arrow);
}

static void ResumeGame()
{
    if (!g_paused)
        return;
    g_paused = false;
    while (g_cursorShows > 0) {             /* back to the display count the game had */
        ShowCursor(FALSE);
        g_cursorShows--;
    }
    if (g_engine && g_appActive) {
        g_engine->SetActive(true);
        CInput::Instance()->Reset();        /* the clicks and key presses of the menu are not the game's */
        RECT r;
        GetWindowRect(g_hWnd, &r);
        ClipCursor(&r);
    }
}

/* ---------------------------------------------------------------------------------------------------------------
 * The actions: Lua chunks for TestLua (the name "=debugmenu" is only for syntax errors; TestLua passes its own). */

/* Two steps: the first click learns only the spells the game actually implements (the 24 entries the spell
 * scripts put into SpellAct, plus spA07_Portal, which the spellbook casts through the Portal scene), the second
 * (when none of those is missing any more) learns every key of Spell, unfinished ones included.  The unfinished
 * spells have no SpellAct entry and crash when cast (e.g. spF03_FireWall: "СТЕНА ОГНЯ" only has a description).
 * SpellAct is unioned in so a mod's implemented spells are treated as real too; the literal list keeps the first
 * click useful when the state has no spell scripts loaded. */
static const char *kSpells =
    "local ok, err = pcall(function() "
    "local u = Unit and Unit.Hero "
    "local b = u and u.BattleParams "
    "if not (b and type(b.Magic) == 'table') then error('Unit.Hero.BattleParams.Magic is missing (load a saved game)') end "
    "local M, have = b.Magic, {} "
    "for i = 1, #M do have[M[i]] = true end "
    "local real = {} "
    "for k in ('spF01_Fireball spF04_TrippleFireball spF05_AresSword spF08_FieryRain spF09_DragonBreath "
    "spF10_Armageddon spW01_Healing spW02_HolyBalzam spW03_Poison spW04_PoisonWeapon spW05_Regeneration "
    "spW06_WaterResist spW07_AirResist spW08_EarthResist spW09_FireResist spW10_Ressurection spA01_Speed "
    "spA04_ShootDamage spA05_Teleport spA06_Snapgoat spA07_Portal spA08_Lighting spE01_Slow spE04_Armor "
    "spE08_StoneRain'):gmatch('%S+') do real[k] = true end "
    "for k in pairs(SpellAct or {}) do if Spell[k] then real[k] = true end end "
    "local miss = 0 "
    "for k in pairs(real) do if Spell[k] and not have[k] then miss = miss + 1 end end "
    "local n, all = 0, false "
    "if miss > 0 then "
    "  for k in pairs(real) do if Spell[k] and not have[k] then M[#M + 1] = k have[k] = true n = n + 1 end end "
    "else "
    "  all = true "
    "  for k in pairs(Spell) do if type(k) == 'string' and not have[k] then M[#M + 1] = k have[k] = true n = n + 1 end end "
    "end "
    "DecompDbg('spells: learned ' .. n .. (all and ' (ALL, unfinished too)' or ' (working only; click again for all)')"
    " .. '; hero knows ' .. #M) "
    "end) "
    "if not ok then DecompDbg('spells ERROR: ' .. tostring(err)) end";

static const char *kGold =
    "local ok, err = pcall(function() "
    "local inv = Hero and Hero.Inventory "
    "if not inv then error('Hero.Inventory is missing (load a saved game)') end "
    "inv.Gold = (inv.Gold or 0) + 100000 "
    "DecompDbg('gold: ' .. inv.Gold) "
    "end) "
    "if not ok then DecompDbg('gold ERROR: ' .. tostring(err)) end";

/* The barracks fills AddInfo.curCount units in troops of HeroArmy.MaxQnUnitInTroop (10) each: 100 is exactly ten
 * troops of ten (scenebarrack.dis).  lastTime = Clock_GetHours() keeps it from adding the time since the last
 * visit, so the count is what the line says. *
 * The battle army is put 250 units away from the hero (its 'Простой' brain would attack on its own if the hero
 * were inside its radius) and starts the fight through Actions['Fight With Army'] with selfHero = false: the
 * normal troop-per-troop battle of heroarmy.dis, not the special hero unit.  The fourth argument true keeps the
 * action from saving the game over game00 (false would save it).  ChangeParam is added to every unit's
 * BattleParams by WorldArmy:BeginBattle: one uDragon (201 health) gets 100201.  AttT has no game speed setting;
 * the battle runs at its normal 1x. */
static const char *kTough =
    "local ok, err = pcall(function() "
    "if not (GUIScene and GUIScene.WorldLevel and rawget(GUIScene.WorldLevel, 'scene')) then"
    "  error('load a saved game and stand on the world map') end "
    "if not (WorldLevel and WorldHero and WorldArmy and Army and ArmyPos) then"
    "  error('the world scripts are not loaded') end "
    "local old = WorldLevel.Armys and WorldLevel.Armys['DecompTough'] "
    "if old then pcall(function() old:delete() end) end "
    "local x, z = WorldHero:GetPos() "
    "ArmyPos['DecompTough'] = { x = x + 250, z = z + 250, radius = 50 } "
    "Army['DecompTough'] = { DisplayName = 'DEBUG ARMY', Attitude = 'Agressive', Standard = 'stVagrant',"
    "  TroopList = { { Unit = 'uDragon', Quantity = 1 } } } "
    "local a = WorldArmy:new('DecompTough') "
    "a.ChangeParam = { Health = 100000 } "
    "local hp = Unit.uDragon.BattleParams.Health + 100000 "
    "Actions['Fight With Army'](Actions, 'DecompTough', false, true) "
    "DecompDbg('battle: 1 x uDragon, ' .. hp .. ' HP, speed 1x (normal)') "
    "end) "
    "if not ok then DecompDbg('battle ERROR: ' .. tostring(err)) end";

/* ---------------------------------------------------------------------------------------------------------------
 * Window and controls. */

enum { IDC_SPELLS = 1001, IDC_GOLD, IDC_LIST, IDC_BARRACKS, IDC_TOUGH, IDC_BACK };
static const int kHotkey = 0x4D01;

static const char *kUnitIds[] = {
    "uValkyr1", "uValkyr2", "uValkyr2_ring", "uValkyr3", "uRafael2", "uRafael3", "uPeasant", "uMilitiaman",
    "uPeter", "uVeteran", "uGoblin", "uGoblinSpearman", "uHobgoblin", "uZombi", "uCadavre", "uRevenant",
    "uWolf", "uFullgrownWolf", "uWerewolf", "uViking", "uYarl", "uConung", "uSpawn", "uBogle", "uGhnol",
    "uArcher", "uLokhar", "uSam", "uBowman", "uYeoman", "uDwarf", "uDvergar", "uSiggurd", "uTangar",
    "uDarkSlave", "uJailer", "uSlaveholder", "uSwordsman", "uFightInstructor", "uSwordMaster", "uLeper",
    "uLeper2", "uIllGuardsman", "uIllGuardsman2", "uCursedCrusader", "uCursedCrusader2", "uWitch",
    "uEnchantress", "uKira", "uSorceress", "uPalmer", "uPilgrim", "uSohay", "uOrc", "uZaghadar",
    "uTogurghar", "uButcher", "uBourreaur", "uInquisitor", "uBear", "uGrizzly", "uCaveBear", "uOgre",
    "uOrog", "uOgtur", "uApostate", "uHeretic", "uMalephic", "uAmazon", "uHelga", "uVirago", "uFury",
    "uTroll", "uZaghon", "uOlogShakh", "uAssassin", "uNizarit", "uFidayin", "uGladiator", "uMirmilon",
    "uConqueror", "uGolem", "uVarklap", "uStoneElemental", "uVampire", "uGangrule", "uNosferatu", "uPaladin",
    "uSunknight", "uDragonslayer", "uDarkKnight", "uBanneret", "uWarlord", "uDarkPriest", "uDemonologiest",
    "uArchont", "uGiant", "uIotun", "uGrimturs", "uDragon", "uPlague", "uMorana", "uMortiss", "uConrad",
    "uDiana", "uEdward", "uFrederic", "uHarbord", "uSamael", "uSamaelDemon", "uTokugava", "uVeliar",
    "uOnager", "uShip", "uTest",
};
static const int kUnitCount = (int)(sizeof(kUnitIds) / sizeof(kUnitIds[0]));

static void ShowMenu(bool activate)
{
    if (!g_menu)
        return;
    g_visible = true;
    ShowWindow(g_menu, activate ? SW_SHOW : SW_SHOWNOACTIVATE);
    SetWindowPos(g_menu, HWND_TOPMOST, 0, 0, 0, 0,
                 SWP_NOMOVE | SWP_NOSIZE | (activate ? 0 : SWP_NOACTIVATE));
    if (activate) {
        SetForegroundWindow(g_menu);
        SetActiveWindow(g_menu);
    }
}

static void HideMenu()
{
    if (!g_menu)
        return;
    g_visible = false;
    ShowWindow(g_menu, SW_HIDE);
    if (g_appActive)
        SetForegroundWindow(g_hWnd);
}

static void ToggleMenu()
{
    if (g_visible)
        HideMenu();
    else
        ShowMenu(true);
}

/* A queued chunk is run by the game's frame (TestLua), so the focus goes back to the game window: the chunk runs
 * at the end of the next frame, and this window stays on top (hidden with Ctrl+Alt+D or its Close button). */
static void QueueAction(const char *chunk, const char *what)
{
    if (!DecompQueueLua(chunk)) {
        AddStatus("busy: the previous Lua chunk has not run yet (click the game window)");
        return;
    }
    AddStatus(what);
    AddStatus("queued; the game runs it at the end of the next frame");
    if (g_hWnd) {
        SetActiveWindow(g_hWnd);
        SetForegroundWindow(g_hWnd);
    }
}

static void OpenBarracks(const char *unit)
{
    char chunk[2048];
    sprintf(chunk,
            "local ok, err = pcall(function() "
            "local W = GUIScene and GUIScene.WorldLevel "
            "if not (W and rawget(W, 'scene')) then error('load a saved game and stand on the world map') end "
            "local u = Unit and Unit['%s'] "
            "if not (u and u.BattleParams) then error('unit %s has no BattleParams') end "
            "local info = { [2] = '%s', [3] = 100, curCount = 100, lastTime = Clock_GetHours() } "
            "W.scene:ChooseScene('Barrack', info) "
            "DecompDbg('barracks: 100 x %s (10 troops x 10)') "
            "end) "
            "if not ok then DecompDbg('barracks ERROR: ' .. tostring(err)) end",
            unit, unit, unit, unit);
    QueueAction(chunk, "barracks: queued");
}

static HWND Make(HWND parent, const wchar_t *cls, const wchar_t *text, DWORD style, int x, int y, int w, int h,
                 int id)
{
    return CreateWindowExW(0, cls, text, WS_CHILD | WS_VISIBLE | style, x, y, w, h, parent,
                           (HMENU)(LONG_PTR)id, GetModuleHandleA(nullptr), nullptr);
}

static void CreateControls(HWND hwnd)
{
    const int x = 10, w = 400;
    int y = 8;
    Make(hwnd, L"STATIC", L"AttT decomp debug menu  (DECOMP_DEBUG_MENU build)", SS_LEFT, x, y, w, 18, 0);
    y += 22;
    Make(hwnd, L"STATIC",
         L"Load a saved game and stand on the world map.  Each action is queued and runs at the end of the next"
         L" game frame; this window returns the focus to the game.  Ctrl+Alt+D shows or hides it.",
         SS_LEFT, x, y, w, 44, 0);
    y += 48;
    Make(hwnd, L"BUTTON", L"Learn spells (working first; click again for all)", BS_PUSHBUTTON | WS_TABSTOP, x, y, w,
         26, IDC_SPELLS);
    y += 30;
    Make(hwnd, L"BUTTON", L"Gold +100000", BS_PUSHBUTTON | WS_TABSTOP, x, y, w, 26, IDC_GOLD);
    y += 34;
    Make(hwnd, L"STATIC", L"Barracks -- 100 units of the unit selected below (10 troops x 10):",
         SS_LEFT, x, y, w, 18, 0);
    y += 20;
    g_list = Make(hwnd, L"LISTBOX", nullptr, WS_BORDER | WS_VSCROLL | WS_TABSTOP | LBS_NOINTEGRALHEIGHT,
                  x, y, w, 150, IDC_LIST);    if (g_list) {
        for (int i = 0; i < kUnitCount; i++) {
            wchar_t item[64];
            MultiByteToWideChar(CP_ACP, 0, kUnitIds[i], -1, item, 64);
            SendMessageW(g_list, LB_ADDSTRING, 0, (LPARAM)item);
            if (!strcmp(kUnitIds[i], "uDragon"))
                g_unitIndex = i;
        }
        if (g_unitIndex >= 0)
            SendMessageW(g_list, LB_SETCURSEL, (WPARAM)g_unitIndex, 0);
    }
    y += 156;
    Make(hwnd, L"BUTTON", L"Open the barracks with the selected unit", BS_PUSHBUTTON | WS_TABSTOP, x, y, w, 26,
         IDC_BARRACKS);
    y += 30;
    Make(hwnd, L"BUTTON",
         L"Tough battle: 1 x uDragon with +100000 health (100201 HP), speed 1x",
         BS_PUSHBUTTON | WS_TABSTOP, x, y, w, 26, IDC_TOUGH);
    y += 32;
    Make(hwnd, L"STATIC", L"Status:", SS_LEFT, x, y, w, 16, 0);
    y += 18;
    g_status = Make(hwnd, L"STATIC", L"status: idle", SS_LEFT, x, y, w, 120, 0);
    y += 126;
    Make(hwnd, L"BUTTON", L"Back to the game (Ctrl+Alt+D)", BS_PUSHBUTTON | WS_TABSTOP, x, y, w, 26, IDC_BACK);
    RefreshStatus();
}

static LRESULT CALLBACK MenuProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    switch (msg) {
    case WM_CREATE:
        CreateControls(hwnd);
        return 0;
    case WM_ACTIVATE:
        if (LOWORD(wp) == WA_INACTIVE)
            ResumeGame();
        else
            PauseGame();
        return 0;
    case WM_SETCURSOR:
        /* the game clears the cursor itself (SetCursor(NULL) every step), and only the window that gets
         * WM_SETCURSOR may set it back: the arrow over the menu and over its child controls */
        if (LOWORD(lp) == HTCLIENT) {
            SetCursor(g_arrow ? g_arrow : LoadCursorA(nullptr, IDC_ARROW));
            return TRUE;
        }
        break;
    case WM_HOTKEY:
        if ((int)wp == kHotkey)
            ToggleMenu();
        return 0;
    case WM_COMMAND:
        switch (LOWORD(wp)) {
        case IDC_SPELLS:
            QueueAction(kSpells, "spells: queued");
            break;
        case IDC_GOLD:
            QueueAction(kGold, "gold: queued");
            break;
        case IDC_BARRACKS: {
            int i = (int)SendMessageW(g_list, LB_GETCURSEL, 0, 0);
            if (i < 0 || i >= kUnitCount)
                AddStatus("barracks: select a unit in the list first");
            else
                OpenBarracks(kUnitIds[i]);
            break;
        }
        case IDC_TOUGH:
            QueueAction(kTough, "battle: queued");
            break;
        case IDC_BACK:
            HideMenu();
            break;
        }
        return 0;
    case WM_CLOSE:
        HideMenu();
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

/* Called by GameMain after the game window and the engine exist (main.cpp).  The window appears without taking
 * the focus, so the game keeps running until the player clicks the menu; Ctrl+Alt+D shows or hides it. */
extern "C" void DecompDebugMenuInit()
{
    if (g_created)
        return;
    g_arrow = LoadCursorA(nullptr, IDC_ARROW);
    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = MenuProc;
    wc.hInstance = GetModuleHandleA(nullptr);
    wc.hIcon = g_icon;
    wc.hCursor = g_arrow;
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.lpszClassName = L"AttTDecompDebugMenu";
    if (!RegisterClassExW(&wc)) {
        OutputDebugStringA("debugmenu: RegisterClassExW failed");
        return;
    }
    RECT r;
    GetWindowRect(g_hWnd, &r);
    const int w = 436, h = 660;
    int x = r.left + 24, y = r.top + 48;
    const int sw = GetSystemMetrics(SM_CXSCREEN), sh = GetSystemMetrics(SM_CYSCREEN);
    if (x + w > sw)
        x = sw - w - 8;
    if (x < 0)
        x = 0;
    if (y + h > sh)
        y = sh - h - 8;
    if (y < 0)
        y = 0;
    g_menu = CreateWindowExW(WS_EX_TOPMOST | WS_EX_TOOLWINDOW, L"AttTDecompDebugMenu", L"AttT debug menu",
                             WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU, x, y, w, h, nullptr, nullptr,
                             GetModuleHandleA(nullptr), nullptr);
    if (!g_menu) {
        OutputDebugStringA("debugmenu: CreateWindowExW failed");
        return;
    }
    g_created = true;
    ShowMenu(false);
    AddStatus("debug menu ready (Ctrl+Alt+D)");
    if (RegisterHotKey(g_menu, kHotkey, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 'D'))
        OutputDebugStringA("debugmenu: Ctrl+Alt+D registered");
    else
        OutputDebugStringA("debugmenu: RegisterHotKey(Ctrl+Alt+D) failed");
}

#endif /* DECOMP_DEBUG_MENU */
