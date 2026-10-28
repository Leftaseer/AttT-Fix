/* 0x0047D5C0: MusicManager::SetState(state, frames): a new state (not the current one, +0x68) over the given number
 * of frames (0 throws the std::string "Количество кадров должно быть больше нуля", frame count must be above zero)
 * that is in the state map (+0x40, 0x00422D80; missing throws a std::string made by 0x00421220 from
 * "MusicManager::SetState - задано несуществующее состояние \"" (nonexistent state) + state + "\"" at
 * ".\MusicManager.cpp" line 0xC1): the playing one fades out (0x0047D140, which takes the map's end in EAX, when +0xA4),
 * the state is kept, the frames (+0x84, +0x88), the volume step (+0x9C / frames at +0x94, 1 / frames at +0x98), then
 * a random track of the state (+0x44 vector, rand) is put in +0x90 (0x00555F20; none releases it), started at the
 * volume +0xA0 = 0 (vf18) and played (vf0C(1)); +0xA4 set */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00422D80(void *map, char **out, void *key);
DECOMP_C void __cdecl sub_0047D140(void *self, void *eax);
DECOMP_C void __thiscall sub_00555F20(void *self, void *src);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char d_0060F154[], d_0060F118[], d_0060F114[], d_0060F100[], d_0069916C[];
DECOMP_C int (__cdecl *imp_00607210)(const void *, const void *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@0@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void *(__cdecl *imp_006071D8)(void *, const char *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBDABV10@@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
typedef void (__thiscall *del_47D5C0)(void *self, int flags);
typedef void (__thiscall *vol_47D5C0)(void *self, float v, int a);
typedef void (__thiscall *play_47D5C0)(void *self, int a, int b);

DECOMP(0047D5C0)
void __thiscall f_0047D5C0(void *this, void *state, unsigned int frames)
{
    char *s = (char *)this;
    char *node, **v;
    void **t;
    unsigned int n;
    float f;
    if ((char)imp_00607210(state, s + 0x68))
        return;
    if (!frames) {
        unsigned int msg[7], thrown[7];         /* two std::string */
        imp_00607324(msg, d_0060F154);
        imp_00607334(thrown, msg);
        sub_005E3EC0(thrown, d_0069916C);
    }
    sub_00422D80(s + 0x40, &node, state);
    if (node == *(char **)(s + 0x48)) {
        unsigned int a[7], b[7], thrown[7];
        imp_006071DC(b, imp_006071D8(a, d_0060F118, state), d_0060F114);
        sub_00421220(thrown, b, d_0060F100, 0xc1);
        sub_005E3EC0(thrown, d_0069916C);
    }
    if (s[0xa4])
        sub_0047D140(this, *(void **)(s + 0x48));
    imp_0060731C(s + 0x68, state);
    f = (float)(double)frames;
    *(unsigned int *)(s + 0x84) = frames;
    *(unsigned int *)(s + 0x88) = frames;
    *(float *)(s + 0x94) = *(float *)(s + 0x9c) / f;
    *(float *)(s + 0x98) = 1.0f / f;
    v = *(char ***)(node + 0x44);
    if (!v || !((*(char **)(node + 0x48) - (char *)v) >> 2)) {
        t = *(void ***)(s + 0x90);
        if (t && !--((int *)t)[1])
            ((del_47D5C0)(*(void ***)t)[0])(t, 1);
        *(void **)(s + 0x90) = 0;
    } else {
        n = (unsigned int)(*(char **)(node + 0x48) - (char *)v) >> 2;
        n = (unsigned int)imp_00607400() % n;
        *(float *)(s + 0xa0) = 0.0f;
        sub_00555F20(s + 0x90, *(char ***)(node + 0x44) + n);
        t = *(void ***)(s + 0x90);
        ((vol_47D5C0)(*(void ***)t)[0x18 / 4])(t, *(float *)(s + 0xa0), 0);
        t = *(void ***)(s + 0x90);
        ((play_47D5C0)(*(void ***)t)[0xc / 4])(t, 1, 0);
    }
    s[0xa4] = 1;
}
