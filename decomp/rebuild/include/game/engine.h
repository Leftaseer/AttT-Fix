/* CEngine: the game singleton (0xD8 bytes).  Owns the scene state machine, the timers, the input and the
 * sound managers; WinMain runs CEngine::Step until it returns false.  Layout from the original code. */
#pragma once
#include "game/common.h"

/* Interfaces of other engine objects, only the virtual slots the engine calls (thiscall). */
struct CUpdateObject {                       /* vtable of the updatable part of an object */
    virtual void Release(int flags);         /* 0: scalar deleting destructor */
    virtual void Update(float dt);           /* 1: once per frame (CUpdateObject::Update accumulates and calls Tick) */
    virtual void Render();                   /* 2 */
    virtual void Slot3();
    virtual void Slot4();
    virtual void Tick(float stepMs);         /* 5: fixed 33.3 ms steps */
};

/* A CUpdateObject embedded in a larger object (CInput +4, the GUI +4): its vtable is the one of the owner's class
 * (CInput's Update reads DirectInput).  A member declared as CUpdateObject would tell the compiler its exact type,
 * and it calls CUpdateObject::Update directly instead of through the vtable; this goes through the pointer. */
struct CUpdatePart {
    void *vftable;
    CUpdateObject *operator->() { return (CUpdateObject *)this; }
};

struct CScene {                              /* CScene / GUIScene / CWorldLevel, primary vtable */
    virtual void Release(int flags);         /* 0 */
    virtual void Slot1();
    virtual void Activate(int arg);          /* 2: entered (CWorldLevel: arg 0 = new game) */
    virtual void Slot3();                    /* 3 */
    virtual CScene *Leave();                 /* 4: returns the scene to switch to */
    virtual void Update(float dt);           /* 5 */
    virtual void Render();                   /* 6 */
    virtual void Slot7();
    virtual void Slot8();
    virtual void Slot9();
    virtual void Slot10();
    virtual bool HandleMessage(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp);   /* 11 */
};

struct CTimer {                              /* CGlobalTimer + 8 */
    char pad00[0x10];
    bool paused;                             /* +10 (CGlobalTimer +18) */
    char pad11[3];
    float dt;                                /* +14 (CGlobalTimer +1C): frame time in ms */
    float Wait();                            /* 0x4E4220: frame limiter, returns the elapsed time */
    void Resume();                           /* 0x4E4200 */
};

struct CGlobalTimer {
    char pad00[8];
    CTimer frame;                          /* +08 */
};

struct CInputKey {                           /* pressed key of this frame */
    unsigned char dik;                       /* DirectInput key code */
    unsigned char pressed;
};

struct CInput {                              /* CSingleton<CInput> (0x7CC bytes), CUpdateObject at +4 */
    void *vftable;
    CUpdatePart updater;                     /* +004 */
    char pad008[0x048 - 0x008];
    unsigned char keyState[256];             /* +048 DirectInput keyboard state */
    char pad148[0x660 - 0x148];
    CInputKey *keys;                         /* +660 key events of this frame */
    unsigned keyCount;                       /* +664 */
    char pad668[0x66C - 0x668];
    int *mouseButtons;                       /* +66C button states (6 = released) */
    unsigned mouseButtonCount;               /* +670 */
    char pad674[0x7C4 - 0x674];
    bool click;                              /* +7C4 */
    bool doubleClick;                        /* +7C5 */
    bool rightClick;                         /* +7C6 */
    char pad7C7[0x7CC - 0x7C7];

    static CInput *Instance();               /* 0x4215D0 */
    void ResetMouse();                       /* 0x46CEB0 */
    void ResetKeys();                        /* 0x46CEF0 */
    void Reset();                            /* 0x46CF30 */
};
static_assert(sizeof(CInput) == 0x7CC, "CInput is 0x7CC bytes");
#ifdef DECOMP_DEBUG_LOG
void DebugLog(const char *text);             /* main.cpp: a line in decomp_debug.log next to the exe */
#endif
#ifdef DECOMP_TEST_INPUT
void TestInput(CInput *input);
void TestLua();                              /* engine.cpp: Lua of the test input, at the end of a frame */
#endif
void StartICallTrace();                      /* icalltrace.cpp (DECOMP_TRACE_ICALLS): indirect callee pops */
void StartProfiler();                        /* profile.cpp (DECOMP_PROFILE): where the main thread spends its time */

struct CCursor {                             /* CSingleton<CCursor> (0x284 bytes) */
    void **vftable;
    static CCursor *Instance();              /* 0x421680 */
    const float *ScreenPos() { return ((const float *(__thiscall *)(CCursor *))vftable[34])(this); }
};

struct CUpdateRoot {                         /* g_updateRoot */
    void Update(float dt);                   /* 0x4DEED0 */
};

struct CConfig;

struct CEngine {
    void *vftable;                           /* +00 CSingleton<CEngine> */
    void *musicManager;                      /* +04 NSound::MusicManager */
    void *unitSoundManager;                  /* +08 */
    void *ambientSoundManager;               /* +0C NSound::AmbientSoundManager */
    char pad10[0x40 - 0x10];
    double gamma;                            /* +40 */
    char pad48[0x54 - 0x48];
    CConfig *config;                         /* +54 */
    char pad58[0x5C - 0x58];
    CScene *scene;                           /* +5C current scene */
    CScene *prevScene;                       /* +60 */
    char pad64[0x68 - 0x64];
    CScene *mainMenu;                        /* +68 */
    char pad6C[0x70 - 0x6C];
    CScene *worldLevel;                      /* +70 */
    char pad74[0x7C - 0x74];
    CGlobalTimer *timers;                    /* +7C */
    CInput *input;                           /* +80 */
    char pad84[0x8C - 0x84];
    struct { void *vftable; CUpdatePart updater; } *gui;   /* +8C (+208: hover, +228) */
    CUpdateObject *overlay;                  /* +90 updated and drawn after the scene */
    char pad94[0xA0 - 0x94];
    D3DCOLOR clearColor;                     /* +A0 */
    char padA4[0xA8 - 0xA4];
    unsigned frameCount;                     /* +A8 */
    int state;                               /* +AC: 0 idle, 1 update, 2 render, 3 start main menu, 4 event,
                                                5 scene finished, 6 leave scene, 7 load world, 8 new game */
    char padB0[0xD8 - 0xB0];

    static CEngine *Instance();              /* 0x42F160 */
    void Init(const std::string &cmdLine);   /* 0x44F2E0 */
    bool Step();                             /* 0x44FD50: one turn of the state machine; false = quit */
    void SetActive(bool active);             /* 0x449F80 */
    void ApplyGamma();                       /* 0x449E80 */
    void Screenshot();                       /* 0x449FE0 */
    void Frame();                            /* 0x44A9C0 */
    bool HandleMessage(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp);   /* 0x44BAB0 */
    void RestoreDevice();                    /* 0x44DD20 */
    void Render();                           /* 0x44E480 */
};
static_assert(sizeof(CEngine) == 0xD8, "CEngine is 0xD8 bytes");
static_assert(__builtin_offsetof(CEngine, state) == 0xAC, "CEngine::state");
static_assert(__builtin_offsetof(CInput, keys) == 0x660, "CInput::keys");
