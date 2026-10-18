/* Globals of the engine (AttT addresses; the build maps them for Valkyrie). */
#pragma once
#include "game/common.h"

struct CEngine;
struct CConfig;

ORIG_DATA(006BF6E0);  /* bool: the window is active (WM_ACTIVATEAPP) */
#define g_appActive          ORIG_VAR(006BF6E0, bool)
ORIG_DATA(006BF6E1);  /* bool: the error log still needs its "game started" header (initialised to 1) */
#define g_errorLogNeedsHeader ORIG_VAR(006BF6E1, bool)
ORIG_DATA(006C8898);  /* HINSTANCE of the exe */
#define g_hInstance          ORIG_VAR(006C8898, HINSTANCE)
ORIG_DATA(006C889C);  /* the game window */
#define g_hWnd               ORIG_VAR(006C889C, HWND)
ORIG_DATA(006C88A0);  /* CConsole* */
#define g_console            ORIG_VAR(006C88A0, void *)
ORIG_DATA(006C88A4);  /* CConfig* (copy of the singleton) */
#define g_config             ORIG_VAR(006C88A4, CConfig *)
ORIG_DATA(006C88A8);  /* CEngine* (copy of the singleton, cleared before it is destroyed) */
#define g_engine             ORIG_VAR(006C88A8, CEngine *)
ORIG_DATA(006C88AC);  /* bool: the crash handler is running */
#define g_inCrashHandler     ORIG_VAR(006C88AC, bool)
ORIG_DATA(006C88AD);  /* bool: pass every window message straight to DefWindowProc */
#define g_wndProcBypass      ORIG_VAR(006C88AD, bool)
ORIG_DATA(006C88AE);  /* bool: the error log header was written */
#define g_errorLogStarted    ORIG_VAR(006C88AE, bool)
ORIG_DATA(006C88B0);  /* CSingleton<CConsole>::m_instance */
#define g_consoleInstance    ORIG_VAR(006C88B0, void *)
ORIG_DATA(006C88B4);  /* nCfg::GamePath* (+4: std::string path of the exe) */
#define g_gamePath           ORIG_VAR(006C88B4, void *)
ORIG_DATA(006C88B8);  /* CSingleton<CEngine>::m_instance */
#define g_engineInstance     ORIG_VAR(006C88B8, CEngine *)
ORIG_DATA(006C884C);  /* CSingleton<CConfig>::m_instance */
#define g_configInstance     ORIG_VAR(006C884C, CConfig *)
ORIG_DATA(006C8C10);  /* the Direct3D device */
#define g_d3dDevice          ORIG_VAR(006C8C10, IDirect3DDevice9 *)
ORIG_DATA(006C8C24);  /* root of the per-frame updaters */
#define g_updateRoot         ORIG_VAR(006C8C24, void *)
