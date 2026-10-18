/* CInput: per-frame state resets (the DirectInput reading itself is not decompiled yet). */
#include "game/common.h"
#include "game/engine.h"

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
