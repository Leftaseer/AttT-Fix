/* 0x004F7780: shows the movie element built from the by-value name (0x004F7430 with the mode 0).  The master
 * volume is saved twice and muted twice (AIL_digital_master_volume_level 0x0060786C, then
 * AIL_set_digital_master_volume_level 0x00607868 with 0, the saved volume 0x6CA494 cleared to match) and the
 * application singleton (0x00421680) gets its +0x228 flag.  The element's player (+4) gives the video width
 * (0x00430DC0) and height (0x00430DD0) and the scale that fits the video into the screen (the two unsigned
 * arguments, the min of height / video height and width / video width; 0x00430CD0 prepares the player); the
 * animation (+0x1C) is placed centred on the screen with the scaled size (0x004CA820; the free x and y are
 * truncated to ints before halving) and played with the settings {27, 13, 32} for 100 (0x004F7640).  The element
 * is released through its vtable +0 with 1, the volume restored (the saved volume 0x6CA494 follows each of the
 * two calls) and the by-value name destroyed. */
/* @conv - 0 */
#include "auto_pre.h"

typedef struct { unsigned int words[7]; } Str_004F7780;                   /* std::string */

DECOMP_C float (__stdcall *imp_0060786C)(void *) __asm__("__imp__AIL_digital_master_volume_level@4");
DECOMP_C void (__stdcall *imp_00607868)(void *driver, float volume) __asm__("__imp__AIL_set_digital_master_volume_level@8");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                   /* operator new */
DECOMP_C void *__thiscall sub_004F7430(void *self, Str_004F7780 name, int mode);
DECOMP_C void __thiscall sub_00430CD0(void *self);
DECOMP_C int __thiscall sub_00430DC0(void *self);
DECOMP_C int __thiscall sub_00430DD0(void *self);
DECOMP_C void __thiscall sub_004CA820(void *self, float x, float y, float w, float h);
DECOMP_C void __thiscall sub_004F7640(void *self, const int *settings, unsigned int time);
DECOMP_C char d_006CA494[], d_006CA498[];
typedef void (__thiscall *release_4F7780)(void *self, int a);

DECOMP(004F7780)
void __cdecl f_004F7780(Str_004F7780 name, unsigned int screenW, unsigned int screenH)
{
    int settings[3];
    char *elem, *player;
    float old1, old2, vw, vh, rw, rh, scale, sw, sh;

    old1 = imp_0060786C(*(void **)d_006CA498);
    old2 = imp_0060786C(*(void **)d_006CA498);
    *(float *)d_006CA494 = 0.0f;
    imp_00607868(*(void **)d_006CA498, 0.0f);
    *(float *)d_006CA494 = 0.0f;
    imp_00607868(*(void **)d_006CA498, 0.0f);
    ((char *)sub_00421680())[0x228] = 1;
    settings[0] = 0x1b;
    settings[1] = 0x0d;
    settings[2] = 0x20;
    elem = (char *)sub_005E3EAE(0x34);
    if (elem)
        elem = (char *)sub_004F7430(elem, name, 0);
    player = elem + 4;
    vw = (float)sub_00430DC0(player);
    vh = (float)sub_00430DD0(player);
    rh = (float)screenH / vh;
    rw = (float)screenW / vw;
    scale = rh < rw ? rh : rw;
    sub_00430CD0(player);
    sw = scale * vw;
    sh = scale * vh;
    sub_004CA820(elem + 0x1c, (float)((int)((float)screenW - sw) / 2), (float)((int)((float)screenH - sh) / 2),
                 (float)(int)sw, (float)(int)sh);
    sub_004F7640(elem, settings, 0x64);
    if (elem)
        ((release_4F7780)(*(void ***)elem)[0])(elem, 1);
    *(float *)d_006CA494 = old1;
    imp_00607868(*(void **)d_006CA498, old1);
    *(float *)d_006CA494 = old2;
    imp_00607868(*(void **)d_006CA498, old2);
    imp_00607330(&name);
}
