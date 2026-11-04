#include "auto_pre.h"

DECOMP_C char d_006082A0[], d_00611588[];
DECOMP_C unsigned int __fastcall sub_004C1F30(int sound);

/* @func 004C2C00 custom */
DECOMP(004C2C00)
unsigned int __cdecl f_004C2C00(_NSound_Sound3D *sound, unsigned int eax,
                                unsigned int volume_bits, unsigned char force)
{
    if (!*(unsigned char *)&sound->field5_0x8)
        return eax;

    eax = sub_004C1F30((int)sound);
    float volume = BITCAST(float, volume_bits);
    if (volume == sound->field72_0x64 && !force)
        return (eax & 0xffff00ffu) | 0x4200u;

    // FCOMIP/JBE takes the scaled path for equality and unordered inputs.
    unsigned int level = (unsigned int)-10000;
    if (!(*(double *)d_006082A0 > volume)) {
        int scaled = GH_FTOL32(volume * *(double *)d_00611588 * sound->field38_0x2c);
        level = (unsigned int)-5000 - (unsigned int)scaled;
    }
    void *buffer = sound->field70_0x5c;
    typedef unsigned int (__stdcall *SetVolume)(void *, unsigned int);
    SetVolume set_volume = *(SetVolume *)(*(char **)buffer + 0x3c);
    unsigned int result = set_volume(buffer, level);
    __builtin_memcpy(&sound->field72_0x64, &volume_bits, sizeof(volume_bits));
    return result;
}
