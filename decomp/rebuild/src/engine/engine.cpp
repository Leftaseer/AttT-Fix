/* CEngine: frame, render, activation, gamma, window messages (Engine.cpp of the original). */
#include "game/common.h"
#include "game/globals.h"
#include "game/engine.h"

#if DECOMP_GAME_ATTT
/* Valkyrie has no Miles sound system: its SetActive only pauses the timer (not decompiled for it yet). */
extern "C" __declspec(dllimport) void __stdcall AIL_set_digital_master_volume_level(void *driver, float level);

DECOMP(00449F80)
void CEngine::SetActive(bool active)
{
    if (active) {
        AIL_set_digital_master_volume_level(g_milesDriver, g_masterVolume);
        timers->frame.Resume();
    } else {
        AIL_set_digital_master_volume_level(g_milesDriver, 0.0f);
        timers->frame.paused = false;
    }
}
#endif

extern "C" __declspec(dllimport) double __cdecl pow(double x, double y);

/* Gamma ramp from CEngine::gamma: value(i) = (i / 256) ^ gamma * 65536, clamped to 0..65535. */
DECOMP(00449E80)
void CEngine::ApplyGamma()
{
    IDirect3DDevice9 *dev = g_d3dDevice;
    D3DCAPS9 caps;
    __builtin_memset(&caps, 0, sizeof(caps));
    dev->GetDeviceCaps(&caps);
    dev->SetRenderState((D3DRENDERSTATETYPE)194 /* D3DRS_SRGBWRITEENABLE */, TRUE);
    D3DGAMMARAMP ramp;
    for (int i = 0; i < 256; i++) {
        double v = pow(i * 0.00390625, gamma) * 65536.0;
        if (v < 0)
            v = 0;
        else if (v > 65535.0)
            v = 65535.0;
        ramp.red[i] = ramp.green[i] = ramp.blue[i] = (WORD)(int)v;
    }
    dev->SetGammaRamp(0, D3DSGR_NO_CALIBRATION, &ramp);
    dev->SetRenderState((D3DRENDERSTATETYPE)194, FALSE);
}

/* Window messages go to the current scene first.  Mouse messages get the position of the game's own cursor
 * (it moves by DirectInput, not by the Windows cursor).  A message the scene used resets the input state. */
static bool IsMouseMessage(UINT msg)
{
    return msg == WM_MOUSEMOVE || msg == WM_LBUTTONDOWN || msg == WM_LBUTTONUP || msg == WM_RBUTTONDOWN ||
           msg == WM_RBUTTONUP || msg == WM_MBUTTONDOWN || msg == WM_MBUTTONUP || msg == WM_LBUTTONDBLCLK;
}

DECOMP(0044BAB0)
bool CEngine::HandleMessage(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (!scene)
        return false;
    if (IsMouseMessage(msg)) {
        const float *pos = CCursor::Instance()->ScreenPos();
        lp = ((int)(long long)pos[1] << 16) | (int)(long long)pos[0];
    }
    bool used = scene->HandleMessage(hwnd, msg, wp, lp);
    if (used) {
        if (msg != WM_MOUSEMOVE && IsMouseMessage(msg)) {
            CInput::Instance()->updater->Update(0.0f);
            CInput::Instance()->ResetMouse();
        }
        if (msg == WM_KEYDOWN || msg == WM_KEYUP || msg == WM_CHAR) {
            CInput::Instance()->updater->Update(0.0f);
            CInput::Instance()->ResetKeys();
        }
    }
    return used;
}

#ifdef DECOMP_TEST_INPUT
/* Scripted input for automatic tests (tools/rungame.py, where DirectInput sees no mouse): testinput.txt in the
 * game folder, one event per line, "MS click X Y" or "MS key VK": at MS milliseconds after the first frame the
 * game's cursor is moved to X,Y and a left click goes the way DirectInput's button events go (the button state
 * list of CInput and the button event listeners), the down this turn and the up the next; "MS lua CODE" runs a
 * Lua chunk in the game's script machine (e.g. loading a save game from the main menu).  Called by the main
 * loop before every CEngine::Step (the menus do not go through CEngine::Frame). */
ORIG_FN(0044A3F0, void, (void *listeners, unsigned int eax, void *info));  /* sends an event to its listeners */
ORIG_DATA(006C9014);    /* listeners of the left button going down */
ORIG_DATA(006C901C);    /* ... going up */
ORIG_DATA(0060AC14);    /* nEvent::NullInfo::vftable */
ORIG_DATA(006C9054);    /* listeners of mouse motion */
ORIG_DATA(0060C798);    /* evMoveInfo::vftable */
ORIG_THISCALL(0057D220, void, (void *vm, const char *buf, int len, const char *name));   /* runs a Lua chunk */
ORIG_DATA(006C88D4);    /* the script machine (its lua_State is used by every DoFile) */

static void TestMove(float dx, float dy)
{
    struct { void *vftable; float dx, dy, dz; } move = { d_0060C798, dx, dy, 0.0f };
    ORIG_CALL(0044A3F0)(d_006C9054, 0, &move);
}

/* Lua of the test input runs at the end of a frame, where the GUI's own event handlers run: a scene switch
 * between frames leaves the engine without a scene for the next one */
static char g_testLua[2048];
static int g_testDik;           /* "MS dik N": a DirectInput key put among the next frame's key events (CEngine::Frame) */
static int g_testHoldDik;       /* "MS hold N MS2": that key held down (its keyboard state) for MS2 milliseconds */
static DWORD g_testHoldUntil;
static int g_testLuaWait;       /* main loop turns it has waited: the menus do not run CEngine::Frame */

/* Lua functions for the test input: DecompLog(...) writes its string and number arguments as a line in
 * decomp_debug.log (the game's Lua has no io library, and print goes nowhere); DecompAutoload(n) tells the
 * "loadsave" line how far it got.  The arguments are read off the Lua 5.1 stack itself: L->top at +8, L->base at
 * +12, a TValue is 8 bytes (the game's lua_Number is a float: value, then the type at +4), a string's characters
 * follow its 16-byte TString. */
ORIG_FN(004031F0, void, (void *L, int (__cdecl *fn)(void *), int n));    /* lua_pushcclosure */
ORIG_FN(004034F0, void, (void *L, int index, const char *name));        /* lua_setfield */

static void LuaArgs(void *L, char *line, int size)
{
    int n = 0;
    line[0] = 0;
    for (char *v = *(char **)((char *)L + 12); v < *(char **)((char *)L + 8) && n < size - 120; v += 8) {
        int tt = *(int *)(v + 4);
        if (tt == 4)           /* LUA_TSTRING */
            n += sprintf(line + n, "%.100s ", *(char **)v + 16);
        else if (tt == 3)      /* LUA_TNUMBER */
            n += sprintf(line + n, "%g ", *(float *)v);
        else
            n += sprintf(line + n, "<type %d> ", tt);
    }
}

static int __cdecl DecompLogLua(void *L)
{
    char line[1024];
    LuaArgs(L, line, sizeof(line));
#ifdef DECOMP_DEBUG_LOG
    DebugLog(line);
#else
    OutputDebugStringA(line);
#endif
    return 0;
}

/* "MS loadsave NAME" (the bisection script's game0): from the main menu, open the load menu, choose the saved game
 * NAME (Saves/NAME.sav, '*' the first one) and load it, tried every second until it is done or the save is not
 * there.  Once the world's GUI scene is up again, "autoload: loaded at MS ms" goes to the debugger output (the
 * tests wait for it, tools/rungame.py 'until'), and lines "L+MS ..." run MS milliseconds after that. */
static char g_autoload[64];
static int g_autoloadState;     /* 0 none, 1 trying, 2 loading, 3 not found, 4 loaded */
static DWORD g_autoloadNext, g_loadedAt;

static int __cdecl DecompAutoloadLua(void *L)
{
    char *v = *(char **)((char *)L + 12);
    if (v < *(char **)((char *)L + 8) && *(int *)(v + 4) == 3)
        g_autoloadState = (int)*(float *)v;
    return 0;
}

static void AutoloadStep(DWORD start)
{
    if (g_autoloadState == 4 && !g_loadedAt) {
        g_loadedAt = GetTickCount();
        char b[64];
        sprintf(b, "autoload: loaded at %u ms", (unsigned)(g_loadedAt - start));
        OutputDebugStringA(b);
    }
    if ((g_autoloadState != 1 && g_autoloadState != 2) || g_testLua[0] || (int)(GetTickCount() - g_autoloadNext) < 0)
        return;
    g_autoloadNext = GetTickCount() + 1000;
    if (g_autoloadState == 2)      /* loading: done when the world level's GUI scene is up (also under a battle) */
        sprintf(g_testLua, "pcall(function() local W = GUIScene and GUIScene.WorldLevel "
                           "if W and rawget(W, 'scene') then DecompAutoload(4) end end)");
    else
        sprintf(g_testLua,
                "pcall(function() local L = GUIScene and GUIScene.Load "
                "if L and L.scene and L._SlotNames then "
                "for i, n in pairs(L._SlotNames) do if n == '%s' or '%s' == '*' then L._CurrentSlotNum = i "
                "DecompAutoload(2) DecompLog('autoload: ' .. n) L:StrongLoad() return end end "
                "DecompAutoload(3) DecompLog('autoload: no saved game %s') return end "
                "for k, v in pairs(GUIScene or {}) do if type(v) == 'table' and rawget(v, '_ChooseHero') and v.scene then "
                "v:_Load() return end end end)", g_autoload, g_autoload, g_autoload);
    g_testLuaWait = 0;
}

void TestLua()
{
    if (!g_testLua[0])
        return;
    void *vm = *(void **)d_006C88D4;
    static void *registered;       /* the lua_State they were given to (a new one comes with some scenes) */
    if (vm && *(void **)((char *)vm + 4) != registered) {
        void *L = *(void **)((char *)vm + 4);         /* CLua: the lua_State */
        ORIG_CALL(004031F0)(L, DecompLogLua, 0);
        ORIG_CALL(004034F0)(L, -10002 /* LUA_GLOBALSINDEX */, "DecompLog");
        ORIG_CALL(004031F0)(L, DecompAutoloadLua, 0);
        ORIG_CALL(004034F0)(L, -10002, "DecompAutoload");
        registered = L;
    }
    if (vm)
        ORIG_CALL(0057D220)(vm, g_testLua, (int)strlen(g_testLua), "=testinput");
    g_testLua[0] = 0;
}

/* a line with the game's own cursor (drawn by the hardware, not in screenshots): where a click lands */
static void TestPos(const char *what, unsigned ms)
{
    const float *p = CCursor::Instance()->ScreenPos();
    char b[96];
    sprintf(b, "%s %u ms, cursor %d %d", what, ms, (int)p[0], (int)p[1]);
    OutputDebugStringA(b);
}

void TestInput(CInput *input)
{
    static FILE *f;
    static bool opened, pending, upNext;
    static DWORD start, due;
    static char line[2048];
    struct { void *vftable; } info = { d_0060AC14 };
    if (!opened) {
        opened = true;
        f = fopen("testinput.txt", "r");
        start = GetTickCount();
        OutputDebugStringA(f ? "testinput.txt opened" : "no testinput.txt");
    }
    static DWORD beat;
    if (GetTickCount() - beat > 5000) {
        beat = GetTickCount();
        TestPos("TestInput alive at", beat - start);
    }
    if (g_testLua[0] && ++g_testLuaWait > 30)
        TestLua();
    AutoloadStep(start);
    {   /* every move of the game's cursor, to see where scripted mouse input lands */
        static int lx = -1, ly = -1;
        const float *p = CCursor::Instance()->ScreenPos();
        if ((int)p[0] != lx || (int)p[1] != ly) {
            lx = (int)p[0];
            ly = (int)p[1];
            TestPos("moved at", GetTickCount() - start);
        }
    }
    if (upNext && input->mouseButtons) {
        upNext = false;
        input->mouseButtons[input->mouseButtonCount++] = 1;
        ORIG_CALL(0044A3F0)(d_006C901C, 0, &info);
    }
    for (;;) {
        static bool afterLoad;
        if (!pending) {
            if (!f || !fgets(line, sizeof(line), f))
                return;
            unsigned ms = 0;
            afterLoad = line[0] == 'L';
            if (sscanf(line + afterLoad, "%u", &ms) != 1)
                continue;
            due = ms;
            pending = true;
        }
        if (afterLoad && !g_loadedAt)
            return;
        if ((int)(GetTickCount() - (afterLoad ? g_loadedAt : start) - due) < 0)
            return;
        pending = false;
        if (afterLoad)                  /* the rest of the line as if it had a plain time */
            memmove(line, line + 1, strlen(line));
        unsigned ms = 0;
        int x, y;
        sscanf(line, "%u", &ms);
        if (sscanf(line, "%u click %d %d", &ms, &x, &y) == 3 && input->mouseButtons) {
            OutputDebugStringA(line);
            TestMove(-10000.0f, -10000.0f);      /* to the corner, then to X,Y */
            TestMove((float)x, (float)y);
            input->mouseButtons[input->mouseButtonCount++] = 0;
            ORIG_CALL(0044A3F0)(d_006C9014, 0, &info);
            upNext = true;
            return;
        } else if (strstr(line, " pos")) {
            TestPos("cursor at", ms);
        } else if (const char *name = strstr(line, " loadsave ")) {
            sscanf(name + 10, "%63s", g_autoload);
            g_autoloadState = 1;
            g_autoloadNext = GetTickCount();
        } else if (const char *lua = strstr(line, " lua ")) {
            OutputDebugStringA(line);
            lstrcpynA(g_testLua, lua + 5, sizeof(g_testLua));   /* run inside the next frame (TestLua) */
            g_testLuaWait = 0;
        } else if (sscanf(line, "%u key %d", &ms, &x) == 2) {
            PostMessageA(g_hWnd, WM_KEYDOWN, x, 1);
            PostMessageA(g_hWnd, WM_KEYUP, x, 0xC0000001);
        } else if (sscanf(line, "%u hold %d %d", &ms, &x, &y) == 3) {
            OutputDebugStringA(line);
            g_testDik = g_testHoldDik = x;
            g_testHoldUntil = GetTickCount() + (DWORD)y;
        } else if (sscanf(line, "%u dik %d", &ms, &x) == 2) {
            OutputDebugStringA(line);
            g_testDik = x;              /* (the game reads keys through DirectInput: posted messages miss it) */
        }
    }
}
#endif

/* State 1 of the engine: timers, input, PrintScreen (screenshot) and Pause (pauses the game clock), then the
 * updaters, the scene and the GUI. */
DECOMP(0044A9C0)
void CEngine::Frame()
{
    state = 2;
    timers->frame.Wait();
    float dt = timers->frame.dt;
    ++frameCount;
    g_updateRoot->Update(dt);
    input->updater->Update(dt);
#ifdef DECOMP_TEST_INPUT
    if (g_testDik) {                         /* one more event of this frame (the buffer holds 0x40) */
        if (input->keyCount < 0x40) {
            input->keys[input->keyCount].dik = (unsigned char)g_testDik;
            input->keys[input->keyCount].pressed = 1;
            input->keyCount++;
        }
        g_testDik = 0;
    }
    if (g_testHoldDik) {
        if ((int)(GetTickCount() - g_testHoldUntil) < 0)
            input->keyState[g_testHoldDik & 0xff] = 0x80;
        else
            g_testHoldDik = 0;
    }
#endif
    for (unsigned i = 0; i < input->keyCount; i++) {
        const CInputKey &k = input->keys[i];
        if (!k.pressed || k.dik == 0x3D /* DIK_F3 */)
            continue;
        if (k.dik == 0xB7)                   /* DIK_SYSRQ */
            Screenshot();
        else if (k.dik == 0xC5)              /* DIK_PAUSE */
            timers->frame.paused = !timers->frame.paused;
    }
    overlay->Update(dt);
    scene->Update(dt);
    gui->updater->Update(dt);
#ifdef DECOMP_TEST_INPUT
    TestLua();
#endif
}

/* State 2: draw the scene and the overlay.  A failed Present is retried through a device reset only for
 * D3DERR_DEVICENOTRESET; any other failure (e.g. D3DERR_DEVICELOST while minimised) throws, as in the
 * original. */
DECOMP(0044E480)
void CEngine::Render()
{
    state = 1;
    *(int *)((char *)gui + 0x208) = 0;
    IDirect3DDevice9 *dev = g_d3dDevice;
    dev->Clear(0, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, clearColor, 1.0f, 0);
    dev->BeginScene();
    scene->Render();
    overlay->Render();
    dev->EndScene();
    if (g_d3dDevice->Present(nullptr, nullptr, nullptr, nullptr) < 0) {
        if (g_d3dDevice->TestCooperativeLevel() != D3DERR_DEVICENOTRESET)
            ThrowGameException("D3DERR_DEVICENOTRESET", ".\\Engine.cpp", 0x6F0);
        RestoreDevice();
    }
}
