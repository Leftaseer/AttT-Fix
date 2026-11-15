/* CInput: the recorded-input loader (0x46B4F0) and the per-frame state resets (the DirectInput reading itself is
 * not decompiled yet). */
#include "game/common.h"
#include "game/engine.h"
#include "game/gamefile.h"

ORIG_DATA(0060C79C);                                                       /* "input.dat" */
ORIG_THISCALL(00459290, CGameFile *, (CGameFile *self, const std::string *name, int noLoad));
ORIG_FN(005E3B10, void *, (unsigned int size));                             /* operator new[] */

/* Reads the whole input.dat: the size, then that many bytes into a fresh buffer.  A missing file leaves the input
 * with no recording and switches the mode off. */
DECOMP(0046B4F0)
void CInput::LoadPlayback()
{
    alignas(CGameFile) unsigned char fileStorage[sizeof(CGameFile)];
    CGameFile *file = (CGameFile *)fileStorage;
    {
        std::string name(ORIG_STR(0060C79C));
        sub_00459290(file, &name, 1);
    }

    if (!file->opened) {
        playbackSize = 0;
        mode = 0;
        file->~CGameFile();
        return;
    }

    file->Read(&playbackSize, 4);
    playbackData = (unsigned char *)sub_005E3B10(playbackSize);
    file->Read(playbackData, playbackSize);
    file->Close();
    playbackCursor = 0;
    file->~CGameFile();
}

DECOMP(0046CEB0)
void CInput::ResetMouse()
{
    for (unsigned i = 0; i < mouseButtonCount; i++)
        mouseButtons[i] = 6;                 /* released */
    doubleClick = false;
    click = false;
    rightClick = false;
}

DECOMP(0046CEF0)
void CInput::ResetKeys()
{
    __builtin_memset(keyState, 0, sizeof(keyState));
    for (unsigned i = 0; i < keyCount; i++)
        keys[i].dik = 0;
}

DECOMP(0046CF30)
void CInput::Reset()
{
    ResetMouse();
    ResetKeys();
}
