/* CConfig: graphic.cfg / game.cfg settings (0x98 bytes, singleton 0x6C884C). */
#pragma once
#include "game/common.h"

struct CConfig {
    void *vftable;                           /* +00 CSingleton<CConfig> */
    char pad04[0x40 - 0x04];
    int width;                               /* +40 window / back buffer size */
    int height;                              /* +44 */
    int x;                                   /* +48 window position */
    int y;                                   /* +4C */
    char pad50[0x88 - 0x50];
    float musicVolume;                       /* +88 */
    float soundVolume;                       /* +8C */
    float ambientVolume;                     /* +90 */
    char pad94[0x98 - 0x94];

    static CConfig *Instance();              /* 0x427990 */
    void LoadGraphicCfg(const std::string &name);   /* 0x441DF0 */
};
static_assert(sizeof(CConfig) == 0x98, "CConfig is 0x98 bytes");

struct CConsole {
    static CConsole *Instance();             /* 0x42F050 */
    void OpenLog(const std::string &name);   /* 0x4425E0 */
};

namespace nCfg {
struct GamePath {                            /* 0x3C bytes */
    void *vftable;
    std::string exePath;                     /* +04 full path of the exe */
};
}
