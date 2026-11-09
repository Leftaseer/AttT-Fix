/* The script machine (CLuaWrapper, the singleton at 0x6C88D4): the Lua state and the chunks the game runs in it.
 * Only the entry points the translated code calls are declared. */
#pragma once
#include "game/common.h"

struct CLuaWrapper {
    void DoFile(const char *fileName); /* 0x432620: runs fileName with ".lua" appended, loaded from the archive */
};
