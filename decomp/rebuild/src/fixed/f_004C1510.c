/* 0x004C1510: NSound::Sound::InitDirectSound(rate, bits, channels, hwnd) (static): creates the DirectSound object
 * (DirectSoundCreate8 into 0x6CA4A4), priority level, the primary buffer (hardware mixing flag from the caps the
 * original reads without setting their size) set to PCM rate/bits/channels, then released */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C long __stdcall sub_005E37B6(const void *guid, void **ds, void *outer);   /* DirectSoundCreate8 */
DECOMP_C char d_006CA4A4[];
typedef long (__stdcall *Coop_4C1510)(void *ds, void *hwnd, unsigned int level);
typedef long (__stdcall *Caps_4C1510)(void *ds, void *caps);
typedef long (__stdcall *Create_4C1510)(void *ds, const void *desc, void **buf, void *outer);
typedef long (__stdcall *SetFormat_4C1510)(void *buf, const void *wfx);
typedef unsigned long (__stdcall *Release_4C1510)(void *buf);

#define DS (*(void ***)d_006CA4A4)
#define VT(o) (*(void ***)(o))

DECOMP(004C1510)
void __cdecl f_004C1510(unsigned int rate, unsigned int bits, unsigned int channels, void *hwnd)
{
    void **primary;
    struct { unsigned short tag, ch; unsigned int rate, avg; unsigned short align, bits, cb; } wfx;
    unsigned int desc[9];                       /* DSBUFFERDESC */
    unsigned int caps[0x18];                    /* DSCAPS (its dwSize left as the stack has it) */
    unsigned short align;
    sub_005E37B6(0, (void **)d_006CA4A4, 0);
    ((Coop_4C1510)VT(DS)[0x18 / 4])(DS, hwnd, 2);   /* DSSCL_PRIORITY */
    primary = 0;
    ((Caps_4C1510)VT(DS)[0x10 / 4])(DS, caps);
    desc[0] = 0x24;
    desc[1] = (caps[8] ? 4 : 0) + 1;            /* DSBCAPS_PRIMARYBUFFER | LOCHARDWARE when free hardware buffers */
    desc[2] = desc[3] = desc[4] = 0;
    desc[5] = desc[6] = desc[7] = desc[8] = 0;
    ((Create_4C1510)VT(DS)[0xc / 4])(DS, desc, (void **)&primary, 0);
    wfx.tag = 1;
    wfx.ch = (unsigned short)channels;
    wfx.rate = rate;
    wfx.bits = (unsigned short)bits;
    align = (unsigned short)((unsigned short)bits >> 3) * (unsigned short)channels;
    wfx.align = align;
    wfx.avg = align * rate;
    wfx.cb = 0;
    ((SetFormat_4C1510)VT(primary)[0x38 / 4])(primary, &wfx);
    if (primary)
        ((Release_4C1510)VT(primary)[2])(primary);
}
