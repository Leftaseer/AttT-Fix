/* CInput: the recorded-input player and recorder and the per-frame state resets (the DirectInput reading itself is
 * not decompiled yet). */
#include "game/common.h"
#include "game/engine.h"
#include "game/gamefile.h"

ORIG_DATA(0060C79C);                                                       /* "input.dat" */
ORIG_THISCALL(00459290, CGameFile *, (CGameFile *self, const std::string *name, int noLoad));
ORIG_FN(005E3B10, void *, (unsigned int size));                             /* operator new[] */
ORIG_THISCALL(0046C980, unsigned int, (void *self));                        /* the keyboard poll */
ORIG_FN(0046CB50, unsigned int, (void *self, unsigned int previous));       /* the mouse poll (ECX + EAX) */

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

/* The recording is the frame's key state overrides (count, then the dik and the state of every pressed key), the
 * key events (count, then dik and whether the event is a press), the mouse buttons (count, then a byte each) and
 * the twelve bytes of the three motion floats. */
DECOMP(0046D0E0)
void CInput::RecordFrame()
{
    sub_0046CB50(this, sub_0046C980(this));

    unsigned char *data = playbackData;
    unsigned start = playbackSize;
    unsigned cursor = start + 1;
    unsigned char pressed = 0;
    for (unsigned i = 0; i < sizeof(keyState); i++) {
        if (keyState[i] & 0x80) {
            data[cursor++] = (unsigned char)i;
            data[cursor++] = keyState[i];
            pressed++;
        }
    }
    data[start] = pressed;

    data[cursor++] = (unsigned char)keyCount;
    for (unsigned i = 0; i < keyCount; i++) {
        data[cursor++] = keys[i].dik;
        data[cursor++] = keys[i].pressed == 1;
    }

    data[cursor++] = (unsigned char)mouseButtonCount;
    for (unsigned i = 0; i < mouseButtonCount; i++)
        data[cursor++] = (unsigned char)mouseButtons[i];

    unsigned char *motion = (unsigned char *)&mouseX;
    for (unsigned i = 0; i < 12; i++)
        data[cursor++] = motion[i];

    playbackSize = cursor;
}

/* Replays one frame from the same layout: the key state is cleared and then overridden, the key events and the
 * mouse buttons are restored with their counts and the motion bytes go back into the three floats. */
DECOMP(0046C6E0)
void CInput::PlaybackFrame()
{
    __builtin_memset(keyState, 0, sizeof(keyState));

    unsigned char *data = playbackData;
    unsigned cursor = playbackCursor;
    for (unsigned n = data[cursor++]; n != 0; n--) {
        unsigned char dik = data[cursor++];
        keyState[dik] = data[cursor++];
    }

    keyCount = 0;
    for (unsigned n = data[cursor++]; n != 0; n--) {
        unsigned char dik = data[cursor++];
        keys[keyCount].dik = dik;
        keys[keyCount].pressed = data[cursor++] != 0;
        keyCount++;
    }

    mouseButtonCount = 0;
    for (unsigned n = data[cursor++]; n != 0; n--)
        mouseButtons[mouseButtonCount++] = data[cursor++];

    unsigned char *motion = (unsigned char *)&mouseX;
    for (unsigned i = 0; i < 12; i++)
        motion[i] = data[cursor++];

    playbackCursor = cursor;
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
