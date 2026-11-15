/* CInput: the recorded-input player and recorder and the per-frame state resets (the DirectInput reading itself is
 * not decompiled yet). */
#include "game/common.h"
#include "game/engine.h"
#include "game/gamefile.h"
#include "game/lua.h"

ORIG_DATA(0060C79C);                                                       /* "input.dat" */
ORIG_THISCALL(00459290, CGameFile *, (CGameFile *self, const std::string *name, int noLoad));
ORIG_FN(005E3B10, void *, (unsigned int size));                             /* operator new[] */
ORIG_DATA(006C8684);                                                       /* CSingleton<CInput>::m_instance */
ORIG_DATA(00607BC8);                                                       /* "Ошибка при создании m_instance в CSingleton" */
ORIG_DATA(00607BAC);                                                       /* "e:\\prog\\att1\\singleton.h" */
ORIG_THISCALL(0046F300, void *, (void *self));                             /* CInput::CInput */
ORIG_DATA(0060AC14);                                                       /* nEvent::NullInfo::vftable */
ORIG_DATA(0060C798);                                                       /* evMoveInfo::vftable */
ORIG_DATA(0060CA1C);                                                       /* evKeyInfo::vftable */
ORIG_DATA(006C88D8);                                                       /* EditorUtils::m_instance */
ORIG_DATA(006C9014);                                                       /* listeners of the left button down */
ORIG_DATA(006C901C);                                                       /* ... the left button up */
ORIG_DATA(006C9024);                                                       /* ... the right button down */
ORIG_DATA(006C902C);                                                       /* ... the right button up */
ORIG_DATA(006C9034);                                                       /* ... the middle button down */
ORIG_DATA(006C903C);                                                       /* ... the middle button up */
ORIG_DATA(006C9044);                                                       /* ... a key down */
ORIG_DATA(006C904C);                                                       /* ... a key up */
ORIG_DATA(006C9054);                                                       /* ... mouse motion */
ORIG_DATA(006C9058);                                                       /* ... the next one being sent to */
ORIG_FN(0044A3F0, unsigned, (void *listeners, unsigned previous, void *info));   /* sends an event to its listeners */
ORIG_FN(004030A0, void, (void *L, float value));                           /* lua_pushnumber */
ORIG_DATA(0060826C);                                                       /* an event's script-argument list */
ORIG_DATA(00607CB8);                                                       /* the list's base-class vtable */
ORIG_THISCALL(00422000, void, (void *self));                               /* ~Object of the list */

typedef long (__stdcall *device_getdata)(void *dev, unsigned size, void *data, unsigned *count, unsigned flags);
typedef long (__stdcall *device_acquire)(void *dev);

extern "C" __declspec(dllimport) char *__cdecl _strlwr(char *text); /* 0x607414 */

#define DIERR_OTHERAPPHASPRIO_ (-0x7ff8ffe2L)      /* 0x8007001E: another application has the device */

/* The editor takes the mouse buttons for its own tools, so outside it a press of one button while the other is
 * down does not count. */
static bool InEditor()
{
    return (*(char **)d_006C88D8)[0x40] != 0;
}

/* The singleton accessor: the input object is built on the first request and a failed allocation throws the
 * CSingleton error instead of returning null. */
DECOMP(004215D0)
CInput *CInput::Instance()
{
    CInput *&instance = *(CInput **)d_006C8684;
    if (!instance) {
        void *memory = operator new(sizeof(CInput));
        instance = memory ? (CInput *)ORIG_CALL(0046F300)(memory) : nullptr;
        if (!instance)
            ThrowGameException(ORIG_STR(00607BC8), ORIG_STR(00607BAC), 16);
    }
    return instance;
}

/* 0x46D380: the DirectInput scan code the input configuration's key name stands for (the name is matched
 * case-insensitively; the original lowercases the copy it is handed).  0xFF means no key has that name.  The three
 * generic modifier names at the end are the game's own pseudo-codes, not scan codes. */
static const struct {
    const char *name;
    unsigned char dik;
} kKeyNames[] = {
    { "esc", 1 },
    { "1", 2 },
    { "2", 3 },
    { "3", 4 },
    { "4", 5 },
    { "5", 6 },
    { "6", 7 },
    { "7", 8 },
    { "8", 9 },
    { "9", 10 },
    { "0", 11 },
    { "-", 12 },
    { "=", 13 },
    { "backspace", 14 },
    { "tab", 15 },
    { "q", 16 },
    { "w", 17 },
    { "e", 18 },
    { "r", 19 },
    { "t", 20 },
    { "y", 21 },
    { "u", 22 },
    { "i", 23 },
    { "o", 24 },
    { "p", 25 },
    { "[", 26 },
    { "]", 27 },
    { "enter", 28 },
    { "leftctrl", 29 },
    { "a", 30 },
    { "s", 31 },
    { "d", 32 },
    { "f", 33 },
    { "g", 34 },
    { "h", 35 },
    { "j", 36 },
    { "k", 37 },
    { "l", 38 },
    { ";", 39 },
    { "'", 40 },
    { "`", 41 },
    { "leftshift", 42 },
    { "\\", 43 },
    { "z", 44 },
    { "x", 45 },
    { "c", 46 },
    { "v", 47 },
    { "b", 48 },
    { "n", 49 },
    { "m", 50 },
    { ",", 51 },
    { ".", 52 },
    { "/", 53 },
    { "rightshift", 54 },
    { "numpad*", 55 },
    { "leftalt", 56 },
    { "space", 57 },
    { "capslock", 58 },
    { "f1", 59 },
    { "f2", 60 },
    { "f3", 61 },
    { "f4", 62 },
    { "f5", 63 },
    { "f6", 64 },
    { "f7", 65 },
    { "f8", 66 },
    { "f9", 67 },
    { "f10", 68 },
    { "numlock", 69 },
    { "scrolllock", 70 },
    { "numpad7", 71 },
    { "numpad8", 72 },
    { "numpad9", 73 },
    { "numpad-", 74 },
    { "numpad4", 75 },
    { "numpad5", 76 },
    { "numpad6", 77 },
    { "numpad+", 78 },
    { "numpad1", 79 },
    { "numpad2", 80 },
    { "numpad3", 81 },
    { "numpad0", 82 },
    { "numpad.", 83 },
    { "numpad/", 181 },
    { "numpadenter", 156 },
    { "f11", 87 },
    { "f12", 88 },
    { "rightctrl", 157 },
    { "printscreen", 183 },
    { "pause", 197 },
    { "rightalt", 184 },
    { "leftwin", 219 },
    { "rightwin", 220 },
    { "app", 221 },
    { "up", 200 },
    { "down", 208 },
    { "left", 203 },
    { "right", 205 },
    { "insert", 210 },
    { "delete", 211 },
    { "home", 199 },
    { "end", 207 },
    { "pgup", 201 },
    { "pgdown", 209 },
    { "shift", 243 },
    { "ctrl", 244 },
    { "alt", 245 },
};

DECOMP(0046D380)
unsigned char __cdecl KeyCodeFromName(std::string name)
{
    _strlwr(&name[0]);
    for (const auto &key : kKeyNames)
        if (name == key.name)
            return key.dik;
    return 0xFF;
}

/* 0x46C1A0: a lowercased copy of a string (the map keys the input configuration and the key lookup use).  The
 * original copies the text into a 256-byte buffer first, so the source can be whatever the caller passes. */
DECOMP(0046C1A0)
void __stdcall LowercaseCopy(const std::string *text, std::string *out)
{
    char buffer[256];
    __builtin_strcpy(buffer, text->c_str());
    _strlwr(buffer);
    *out = buffer;
}

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

/* 0x46C980: the keyboard poll: while acquired (+0x7C7) it advances the per-key edge flags (+0x6C4: a pending
 * press or release of the last poll becomes the seen state 1 / 4) and reads up to 0x40 buffered DirectInput events
 * (device +0x44, GetDeviceData into +0x150, count +0x14C, results ORed into +0x40); on failure it re-acquires
 * (looping while DIERR_OTHERAPPHASPRIO) and clears the key state and the frame's key count; otherwise every event
 * becomes a key event (+0x660, count +0x664), a press (0x80 in the data) going to the listeners of 0x006C9044 and
 * a release to those of 0x006C904C (an evKeyInfo 0x0060CA1C sent by 0x0044A3F0), and sets the held bit of the key
 * state and the key's pending flag.  The function's own value is the last event count (the recorder threads it
 * through the mouse poll); without the device it leaves the caller's EAX alone, which is returned as 0 here since
 * only the mouse poll consumes it. */
DECOMP(0046C980)
unsigned CInput::PollKeyboard()
{
    if (!keyboardAcquired)
        return 0;

    for (unsigned i = 0; i < 0x100; i++) {
        if (keyEdge[i] & 2)
            keyEdge[i] = 1;
        else if (keyEdge[i] & 8)
            keyEdge[i] = 4;
    }

    eventCount = 0x40;
    long hr = ((device_getdata)(*(void ***)keyboard)[0x28 / 4])(keyboard, sizeof(CInputEvent), events, &eventCount, 0);
    result |= hr;
    if (result) {
        hr = ((device_acquire)(*(void ***)keyboard)[0x1c / 4])(keyboard);
        result = hr;
        while (hr == DIERR_OTHERAPPHASPRIO_) {
            hr = ((device_acquire)(*(void ***)keyboard)[0x1c / 4])(keyboard);
            result = hr;
        }
        __builtin_memset(keyState, 0, sizeof(keyState));
        keyCount = 0;
        return (unsigned long)(size_t)keyState;      /* the memset's destination is what the original returns */
    }

    keyCount = 0;
    for (unsigned i = 0; i < eventCount; i++) {
        CInputEvent *e = &events[i];
        struct { void *vftable; unsigned char dik; } ev;
        ev.vftable = d_0060CA1C;
        ev.dik = (unsigned char)e->offset;
        keys[keyCount].dik = ev.dik;
        keys[keyCount].pressed = (unsigned char)((e->data >> 7) & 1);
        keyCount++;
        if (e->data & 0x80)
            sub_0044A3F0(d_006C9044, 0, &ev);
        else
            sub_0044A3F0(d_006C904C, 0, &ev);
        if (e->data & 0x80) {
            keyState[ev.dik] = ev.dik | 0x80;
            keyEdge[ev.dik] = (unsigned char)((keyEdge[ev.dik] & 0xfb) | 2);
        } else {
            keyState[ev.dik] = ev.dik & 0x7f;
            keyEdge[ev.dik] = (unsigned char)((keyEdge[ev.dik] & 0xfe) | 8);
        }
    }
    return eventCount;
}

/* The button log: the code (0..5) is appended to +0x66C and the event goes to the button's listeners; a left or
 * right button event threads the log's address (its index for the middle button) through EAX. */
static unsigned LogMouseButton(CInput *input, int code, void *listeners, bool withLogAddress)
{
    unsigned i = input->mouseButtonCount;
    input->mouseButtons[i] = code;
    input->mouseButtonCount = i + 1;
    struct { void *vftable; } ev;
    ev.vftable = d_0060AC14;
    return sub_0044A3F0(listeners, withLogAddress ? (unsigned)(size_t)input->mouseButtons : i, &ev);
}

/* 0x46CB50: the mouse's per-frame poll: while acquired (+0x7C8) it reads up to 0x40 buffered DirectInput events
 * (device +0x148, GetDeviceData into +0x150, count +0x14C, result +0x40); on failure it re-acquires (looping while
 * DIERR_OTHERAPPHASPRIO) and clears the frame's motion (+0x650..+0x658) and button log (+0x670); otherwise it sums
 * the X / Y / wheel offsets (+0x650 / +0x654 / +0x658, marking motion at +0x7C9) and turns button 0 / 1 / 2
 * presses and releases into the log (+0x66C array, codes 0..5), their held flags (+0x7C5 / +0x7C4 / +0x7C6) and
 * the button event lists 0x006C9014..0x006C903C (0x0044A3F0 with an empty event 0x0060AC14; a press of the left or
 * right button counts only in the editor or while the other one is up); with motion the listeners of 0x006C9054 are
 * sent a move event (0x0060C798, x, y, wheel) one by one, the next one being walked through 0x006C9058.  Returns
 * what the original leaves in EAX (the previous EAX unchanged when not acquired). */
DECOMP(0046CB50)
unsigned PollMouse(CInput *input, unsigned previous)
{
    if (!input->mouseAcquired)
        return previous;

    input->eventCount = 0x40;
    long hr = ((device_getdata)(*(void ***)input->mouse)[0x28 / 4])(input->mouse, sizeof(CInputEvent),
                                                                    input->events, &input->eventCount, 0);
    input->result = hr;
    if (hr) {
        hr = ((device_acquire)(*(void ***)input->mouse)[0x1c / 4])(input->mouse);
        input->result = hr;
        while (hr == DIERR_OTHERAPPHASPRIO_) {
            hr = ((device_acquire)(*(void ***)input->mouse)[0x1c / 4])(input->mouse);
            input->result = hr;
        }
        input->mouseButtonCount = 0;
        input->mouseWheel = 0.0f;
        input->mouseY = 0.0f;
        input->mouseX = 0.0f;
        return (unsigned long)hr;
    }

    input->mouseWheel = 0.0f;
    input->mouseY = 0.0f;
    input->mouseX = 0.0f;
    input->mouseButtonCount = 0;
    input->mouseMoved = false;
    unsigned eax = 0;
    for (unsigned i = 0; i < input->eventCount; i++) {
        CInputEvent *e = &input->events[i];
        bool down = (e->data & 0x80) != 0;
        switch (e->offset) {
        case 0:
            input->mouseX += (float)(int)e->data;
            input->mouseMoved = true;
            break;
        case 4:
            input->mouseY += (float)(int)e->data;
            input->mouseMoved = true;
            break;
        case 8:
            input->mouseWheel += (float)(int)e->data;
            input->mouseMoved = true;
            break;
        case 0xC:                                     /* left button */
            if (down) {
                if (!InEditor() && input->rightButton)
                    break;
                input->leftButton = true;
                LogMouseButton(input, 0, d_006C9014, true);
            } else {
                input->leftButton = false;
                LogMouseButton(input, 1, d_006C901C, true);
            }
            break;
        case 0xD:                                     /* right button */
            if (down) {
                if (!InEditor() && input->leftButton)
                    break;
                input->rightButton = true;
                LogMouseButton(input, 2, d_006C9024, false);
            } else {
                input->rightButton = false;
                LogMouseButton(input, 3, d_006C902C, false);
            }
            break;
        case 0xE:                                     /* middle button */
            if (down) {
                input->middleButton = true;
                LogMouseButton(input, 4, d_006C9034, false);
            } else {
                input->middleButton = false;
                LogMouseButton(input, 5, d_006C903C, false);
            }
            break;
        }
        eax = i + 1;
    }
    if (input->mouseMoved) {
        struct { void *vftable; float x, y, z; } ev;
        ev.vftable = d_0060C798;
        ev.x = input->mouseX;
        ev.y = input->mouseY;
        ev.z = input->mouseWheel;
        eax = *(unsigned *)&input->mouseX;
        for (void *listener = *(void **)d_006C9054; listener; listener = *(void **)d_006C9058) {
            *(void **)d_006C9058 = ((void **)listener)[1];
            eax = ((unsigned(__thiscall *)(void *, void *))((void **)*(void **)listener)[1])(listener, &ev);
        }
    }
    return eax;
}

/* The event infos as their script conversion sees them: a move carries x, y and the wheel offset, a key event the
 * DIK code.  Their first virtual hands the event to a script listener: the fields are pushed on the script stack
 * and the 0x0C-byte argument list at the caller's out address records how many values the listener owns (the list
 * keeps the vtable 0x0060826C until the destructor switches it to the base 0x00607CB8 and drops it).  The temporary
 * list the conversion builds follows the same idiom as the Lua bindings' NLuaTempObject in engine.cpp. */
struct ScriptArgumentList {
    void *vftable; /* +00 */
    void *spare;   /* +04 */
    int count;     /* +08 */
};

struct MoveEventInfo {
    void *vftable; /* +00 0x0060C798 */
    float x;       /* +04 */
    float y;       /* +08 */
    float wheel;   /* +0C */
};

struct KeyEventInfo {
    void *vftable;      /* +00 0x0060CA1C */
    unsigned char dik;  /* +04 */
};

/* 0x46EB10: "evMoveInfo" to the script (vtable slot 0): x, y and the wheel offset. */
DECOMP(0046EB10)
ScriptArgumentList *__thiscall MoveEventScriptArguments(const MoveEventInfo *info, ScriptArgumentList *arguments)
{
    ScriptArgumentList temporary = { d_0060826C, nullptr, 0 };
    ORIG_CALL(004030A0)(g_luaState, info->x);
    temporary.count = 1;
    ORIG_CALL(004030A0)(g_luaState, info->y);
    temporary.count = 2;
    ORIG_CALL(004030A0)(g_luaState, info->wheel);
    temporary.count = 3;
    arguments->spare = nullptr;
    arguments->vftable = d_0060826C;
    arguments->count = 3;
    temporary.vftable = d_00607CB8;
    ORIG_CALL(00422000)(&temporary);
    return arguments;
}

/* 0x46EC30: "evKeyInfo" to the script (vtable slot 0): the DIK code. */
DECOMP(0046EC30)
ScriptArgumentList *__thiscall KeyEventScriptArguments(const KeyEventInfo *info, ScriptArgumentList *arguments)
{
    ScriptArgumentList temporary = { d_0060826C, nullptr, 0 };
    ORIG_CALL(004030A0)(g_luaState, (float)info->dik);
    temporary.count = 1;
    arguments->spare = nullptr;
    arguments->vftable = d_0060826C;
    arguments->count = 1;
    temporary.vftable = d_00607CB8;
    ORIG_CALL(00422000)(&temporary);
    return arguments;
}

/* 0x46D030: the input's update part (CInput + 4, vtable 0x60CC20 slot 1).  Mode 0 polls the devices and returns
 * the mouse poll's value; in the recording / playback modes (1 and 2) the elapsed time accumulates and, once an
 * interval is full, one fixed Tick runs (slot 5) and the accumulator drains of intervals, otherwise the frame's
 * mouse motion, key events and button log are dropped (the counts go to zero, the buffers stay).  Other modes do
 * nothing but return mode - 1. */
DECOMP(0046D030)
unsigned UpdateInputFrame(CUpdatePart *updater, float dt)
{
    CInput *input = (CInput *)((char *)updater - __builtin_offsetof(CInput, updater));
    if (!input->mode)
        return PollMouse(input, input->PollKeyboard());
    if (input->mode - 1 >= 2)
        return input->mode - 1;

    CUpdateObject *timer = (CUpdateObject *)updater;
    timer->accumulator += dt;
    if (timer->accumulator < timer->interval) {
        input->mouseWheel = 0.0f;
        input->mouseY = 0.0f;
        input->mouseX = 0.0f;
        input->keyCount = 0;
        input->mouseButtonCount = 0;
        return input->mode - 1;
    }
    unsigned result = ((unsigned(__thiscall *)(CUpdateObject *))((void **)timer->vftable)[5])(timer);
    do {
        timer->accumulator -= timer->interval;
    } while (timer->accumulator >= timer->interval);
    return result;
}

/* The tick slot of the input part: mode 1 appends the current frame to the recording, mode 2 replays a recorded
 * frame; any other mode does nothing and yields the unused mode - 2.  The recorder and the player return 1, which
 * the caller sees as the result. */
DECOMP(0046EC00)
unsigned InputFrameTick(CUpdatePart *updater)
{
    CInput *input = (CInput *)((char *)updater - __builtin_offsetof(CInput, updater));
    if (input->mode == 1)
        return input->RecordFrame();
    if (input->mode != 2)
        return input->mode - 2;
    return input->PlaybackFrame();
}

/* The recording is the frame's key state overrides (count, then the dik and the state of every pressed key), the
 * key events (count, then dik and whether the event is a press), the mouse buttons (count, then a byte each) and
 * the twelve bytes of the three motion floats. */
DECOMP(0046D0E0)
unsigned CInput::RecordFrame()
{
    PollMouse(this, PollKeyboard());

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
    return 1;      /* the original leaves 1 in EAX (a true result) */
}

/* Replays one frame from the same layout: the key state is cleared and then overridden, the key events and the
 * mouse buttons are restored with their counts and the motion bytes go back into the three floats. */
DECOMP(0046C6E0)
unsigned CInput::PlaybackFrame()
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
    return 1;      /* the original leaves 1 in EAX (a true result) */
}

DECOMP(0046CEB0)
void CInput::ResetMouse()
{
    for (unsigned i = 0; i < mouseButtonCount; i++)
        mouseButtons[i] = 6;                 /* released */
    rightButton = false;
    leftButton = false;
    middleButton = false;
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
