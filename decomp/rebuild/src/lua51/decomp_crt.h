/* Included first in the Lua sources (build.py -include): the mingw-w64 headers describe the CRT the game uses,
 * MSVCR80, once __MSVCRT_VERSION__ says so; their _mingw.h leaves __MINGW_IMPORT undefined for clang, which
 * time.h needs for its variables (unused by Lua). */
#include <_mingw.h>
#ifndef __MINGW_IMPORT
#define __MINGW_IMPORT extern
#endif
