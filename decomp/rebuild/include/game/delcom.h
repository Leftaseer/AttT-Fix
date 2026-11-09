/* CDelCom: the text reader DatFile uses (0xB0 bytes): the character read last, the stream and the whole text.
 *
 * ReadFile (0x445630) opens the stream and fills the text a character at a time through ReadChar; the loader
 * puts the text into its source cache. */
#pragma once
#include "game/common.h"
#include "msvc8/fstream.h"

struct CDelCom {
    void *vftable;      /* +00 0x60A4BC */
    char ch;            /* +04 the character read last, 0 at the end of the file */
    char pad005[3];
    std::ifstream file; /* +08 */
    std::string text;   /* +94 the whole file */

    CDelCom();       /* 0x444AD0 */
    ~CDelCom();      /* 0x444B40 */
    bool ReadChar(); /* 0x444BA0 takes the next character of the file into ch */
};
static_assert(sizeof(CDelCom) == 0xB0, "CDelCom is 0xB0 bytes");
static_assert(__builtin_offsetof(CDelCom, ch) == 0x004, "CDelCom::ch");
static_assert(__builtin_offsetof(CDelCom, file) == 0x008, "CDelCom::file");
static_assert(__builtin_offsetof(CDelCom, text) == 0x094, "CDelCom::text");
