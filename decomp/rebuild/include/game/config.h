/* CConfig: graphic.cfg / game.cfg settings (0x98 bytes, singleton 0x6C884C).
 * graphic.cfg is 66 bytes, field by field (0x441DF0): W, H, back buffer format, ?, windowed, ?, depth format,
 * two caps bytes, three option bytes, three volumes, three option bytes, four floats, gamma. */
#pragma once
#include "game/common.h"
#include "game/engine.h"

struct CConfig {
    void *vftable;                           /* +00 CSingleton<CConfig> */
    std::string configDir;                   /* +04 game folder + the directory given to LoadGraphicCfg */
    std::string gameDir;                     /* +20 folder of the exe */
    bool windowed;                           /* +3C 1 = windowed, 0 = fullscreen (no window offset) */
    char pad3D[3];
    int width;                               /* +40 back buffer width */
    int height;                              /* +44 */
    int x;                                   /* +48 window position (0 in a windowed mode) */
    int y;                                   /* +4C */
    int backBufferFormat;                    /* +50 D3DFORMAT: X8R8G8B8 0x16 or A8R8G8B8 0x15 */
    char pad54[8];                           /* +54 (not in graphic.cfg) */
    int depthFormat;                         /* +5C D3DFORMAT (D24S8 0x4B by default) */
    bool compressedTextures;                 /* +60 DXT1..DXT5 all supported */
    char pad61[3];
    int unknown64;                           /* +64 default 1 (not read by the engine yet) */
    bool nonSquareTextures;                  /* +68 D3DPTEXTURECAPS_SQUAREONLY is absent */
    bool tweening;                           /* +69 D3DVTXPCAPS_TWEENING (D3DCAPS9::VertexProcessingCaps) */
    bool grass;                              /* +6A "Grass" */
    bool shadow;                             /* +6B "Shadow" */
    bool reflection;                         /* +6C "Reflection" */
    bool unknown6D;                          /* +6D default 0 */
    bool unknown6E;                          /* +6E default 1 */
    bool unknown6F;                          /* +6F default 0 */
    float unknown70;                         /* +70 default 100.0 */
    float unknown74;                         /* +74 default 400.0 */
    float unknown78;                         /* +78 default 500.0 */
    float unknown7C;                         /* +7C default 100.0 */
    double gamma;                            /* +80 default 1.0 */
    float musicVolume;                       /* +88 default 0.6 */
    float soundVolume;                       /* +8C default 1.0 */
    float ambientVolume;                     /* +90 default 1.0 */
    char pad94[4];                           /* +94 */

    CConfig();                               /* 0x441D10 */
    ~CConfig();                              /* 0x441D70 */
    static CConfig *Instance();              /* 0x427990 */
    void LoadGraphicCfg(const std::string &dir);   /* 0x441DF0 */
};
static_assert(sizeof(CConfig) == 0x98, "CConfig is 0x98 bytes");
static_assert(__builtin_offsetof(CConfig, configDir) == 0x04, "CConfig::configDir");
static_assert(__builtin_offsetof(CConfig, gameDir) == 0x20, "CConfig::gameDir");
static_assert(__builtin_offsetof(CConfig, windowed) == 0x3C, "CConfig::windowed");
static_assert(__builtin_offsetof(CConfig, width) == 0x40, "CConfig::width");
static_assert(__builtin_offsetof(CConfig, backBufferFormat) == 0x50, "CConfig::backBufferFormat");
static_assert(__builtin_offsetof(CConfig, depthFormat) == 0x5C, "CConfig::depthFormat");
static_assert(__builtin_offsetof(CConfig, gamma) == 0x80, "CConfig::gamma");
static_assert(__builtin_offsetof(CConfig, musicVolume) == 0x88, "CConfig::musicVolume");

struct CConsole {                            /* 0x1658 bytes */
    void *vftable;                           /* +0000 CSingleton<CConsole> */
    CUpdateObject updater;                   /* +0004 the console's own updater (vtable 0x60A2C8) */
    std::string unknown3C;                   /* +003C */
    std::string lines[200];                  /* +0058 the console's line history */
    std::string gameFolder;                  /* +1638 "<folder of the exe>\" */
    char pad1654[4];                         /* +1654 the allocation is 0x1658 bytes; neither ctor nor dtor touches it */

    CConsole();                              /* 0x4426E0 */
    ~CConsole();                             /* 0x4427E0 */
    static CConsole *Instance();             /* 0x42F050 */
    void OpenLog(const std::string &name);   /* 0x4425E0 */
    std::string &GameFolder();               /* 0x441C50 */
};
static_assert(sizeof(CConsole) == 0x1658, "CConsole is 0x1658 bytes");
static_assert(__builtin_offsetof(CConsole, gameFolder) == 0x1638, "CConsole::gameFolder");

namespace nCfg {
struct GamePath {                            /* 0x3C bytes */
    void *vftable;
    std::string exePath;                     /* +04 full path of the exe */
};
}
