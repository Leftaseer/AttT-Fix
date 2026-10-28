/* 0x0046C510: initialises the input (mode at +0x674): DirectInput 8 (+0x3C, the result codes ORed into +0x40), the
 * keyboard (+0x44) and the mouse (+0x148): their data formats, foreground non-exclusive, a 64-event buffer, acquired;
 * the mouse motion cleared (+0x650..+0x658); mode 1 records into a new 1000000-byte buffer (+0x678), mode 2 plays
 * back (0x0046B4F0); the next time (+0x2C = +0x28 + the double at 0x60A178) and the first keyboard state (+0x48) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C long __stdcall sub_005E3630(void *hinst, unsigned int ver, const void *iid, void **out, void *outer);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);             /* operator new[] */
DECOMP_C void __thiscall sub_0046B4F0(void *self);
DECOMP_C char d_006C8898[], d_006C889C[], d_00686B84[], d_00686A14[], d_00686A24[], d_0068580C[], d_00685604[],
              d_0060A178[];
typedef long (__stdcall *CreateDevice_46C510)(void *di, const void *guid, void **dev, void *outer);
typedef long (__stdcall *SetFormat_46C510)(void *dev, const void *fmt);
typedef long (__stdcall *SetCoop_46C510)(void *dev, void *hwnd, unsigned int flags);
typedef long (__stdcall *SetProp_46C510)(void *dev, unsigned int prop, const void *hdr);
typedef long (__stdcall *Acquire_46C510)(void *dev);
typedef long (__stdcall *GetState_46C510)(void *dev, unsigned int size, void *data);

#define VT(o) (*(void ***)(o))

static long setup_46C510(void **dev, const void *fmt)
{
    unsigned int prop[5] = { 0x14, 0x10, 0, 0, 0x40 };    /* DIPROPDWORD: DIPROP_BUFFERSIZE 64 */
    long hr = ((SetFormat_46C510)VT(dev)[0x2c / 4])(dev, fmt);
    hr |= ((SetCoop_46C510)VT(dev)[0x34 / 4])(dev, *(void **)d_006C889C, 6);
    hr |= ((SetProp_46C510)VT(dev)[0x18 / 4])(dev, 1, prop);
    return hr | ((Acquire_46C510)VT(dev)[0x1c / 4])(dev);
}

DECOMP(0046C510)
void __thiscall f_0046C510(void *this, unsigned int mode)
{
    char *s = (char *)this;
    long *hr = (long *)(s + 0x40);
    void **di, **kb;
    *(unsigned int *)(s + 0x674) = mode;
    *hr = sub_005E3630(*(void **)d_006C8898, 0x800, d_00686B84, (void **)(s + 0x3c), 0);
    di = *(void ***)(s + 0x3c);
    *hr |= ((CreateDevice_46C510)VT(di)[0xc / 4])(di, d_00686A14, (void **)(s + 0x44), 0);   /* keyboard */
    *hr |= setup_46C510(*(void ***)(s + 0x44), d_0068580C);
    di = *(void ***)(s + 0x3c);
    *hr = ((CreateDevice_46C510)VT(di)[0xc / 4])(di, d_00686A24, (void **)(s + 0x148), 0);  /* mouse */
    *hr |= setup_46C510(*(void ***)(s + 0x148), d_00685604);
    *(float *)(s + 0x658) = 0.0f;
    *(float *)(s + 0x654) = 0.0f;
    *(float *)(s + 0x650) = 0.0f;
    if (mode == 1) {
        *(void **)(s + 0x678) = sub_005E3B10(1000000);
        *(unsigned int *)(s + 0x67c) = 0;
    } else if (mode == 2)
        sub_0046B4F0(this);
    s[0x7c7] = 1;
    *(float *)(s + 0x2c) = (float)(*(float *)(s + 0x28) + *(double *)d_0060A178);
    s[0x7c8] = 1;
    kb = *(void ***)(s + 0x44);
    *hr = ((GetState_46C510)VT(kb)[0x24 / 4])(kb, 0x100, s + 0x48);
}
