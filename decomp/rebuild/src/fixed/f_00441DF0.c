/* 0x00441DF0: CConfig::LoadGraphicCfg(dir): the game folder (0x0042F050 +0x1638) is +0x20 and + dir +4; an existing
 * graphic.cfg there is read field by field (screen size +0x40/+0x44, also into 0x006C8958..0x006C8964, formats,
 * flags, window offset from GetSystemMetrics unless +0x3C, ...); without one the defaults are written to a new one:
 * 1024x768, windowed, the back buffer format X8R8G8B8 or A8R8G8B8 (CheckDeviceType), DXT1..5 support, the first
 * supported depth format of D24S8, D24X4S4, D24X8, D16 (0x4F), D16, D15S1, two caps bits and the default options */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_441DF0;                 /* std::string */
typedef struct { unsigned int w[0xa0 / 4]; } Stream_441DF0;       /* std::ifstream / std::ofstream */
DECOMP_C char *__cdecl sub_0042F050(void);
DECOMP_C void *__stdcall sub_005B8014(unsigned int sdk);           /* Direct3DCreate9 */
DECOMP_C char d_0060A2A8[], d_0060A2A4[], d_0060A2A0[], d_0060A29C[], d_00608C20[], d_006C8964[], d_006C8960[],
    d_006C895C[], d_006C8958[];
DECOMP_C void (__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_006071FC)(void *, const void *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607320)(void *, const char *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_006071F8)(void *, int) __asm__("__imp_??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071F4)(void *, const char *, int, int) __asm__("__imp_?open@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXPBDHH@Z");
DECOMP_C unsigned char (__thiscall *imp_006071F0)(const void *) __asm__("__imp_??7ios_base@std@@QBE_NXZ");
DECOMP_C void (__thiscall *imp_006071EC)(void *) __asm__("__imp_?close@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C void (__thiscall *imp_006071D4)(void *) __asm__("__imp_??_D?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C void *(__thiscall *imp_006071A0)(void *, char *, int) __asm__("__imp_?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z");
DECOMP_C void (__thiscall *imp_006071E8)(void *, const char *, int, int, int) __asm__("__imp_??0?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z");
DECOMP_C void *(__thiscall *imp_006071B0)(void *, const char *, int) __asm__("__imp_?write@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV12@PBDH@Z");
DECOMP_C void (__thiscall *imp_006071B4)(void *) __asm__("__imp_?close@?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C void (__thiscall *imp_006071B8)(void *) __asm__("__imp_??_D?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C int (__stdcall *imp_00607670)(int) __asm__("__imp__GetSystemMetrics@4");
typedef long (__stdcall *cdt_441DF0)(void *d3d, unsigned int ad, unsigned int dt, unsigned int af, unsigned int bf,
                                     int windowed);
typedef long (__stdcall *cdf_441DF0)(void *d3d, unsigned int ad, unsigned int dt, unsigned int af,
                                     unsigned int usage, unsigned int rtype, unsigned int fmt);
typedef long (__stdcall *caps_441DF0)(void *d3d, unsigned int ad, unsigned int dt, void *caps);

#define F(a) (*(float *)(a))

/* screen size globals from +0x40 / +0x44 */
static void screen_441DF0(char *this)
{
    *(int *)d_006C8964 = *(int *)(this + 0x40);
    *(int *)d_006C8960 = *(int *)(this + 0x44);
    F(d_006C895C) = (float)*(unsigned int *)(this + 0x40);
    F(d_006C8958) = (float)*(unsigned int *)(this + 0x44);
}

/* window offset: none when windowed (+0x3C), else centred on the screen */
static void place_441DF0(char *this)
{
    if (this[0x3c]) {
        *(int *)(this + 0x4c) = 0;
        *(int *)(this + 0x48) = 0;
    } else {
        *(unsigned int *)(this + 0x48) = (unsigned int)(imp_00607670(0) - *(int *)(this + 0x40)) >> 1;
        *(unsigned int *)(this + 0x4c) = (unsigned int)(imp_00607670(1) - *(int *)(this + 0x44)) >> 1;
    }
}

/* the option block after the window offset, in file order */
static const short opt_441DF0[][2] = {
    {0x6a, 1}, {0x6b, 1}, {0x6c, 1}, {0x88, 4}, {0x8c, 4}, {0x90, 4}, {0x6d, 1}, {0x6e, 1}, {0x6f, 1}, {0x70, 0x10},
    {0x80, 8},
};

DECOMP(00441DF0)
void __thiscall f_00441DF0(char *this, void *dir)
{
    Stream_441DF0 in, out;
    Str_441DF0 name;
    unsigned int k;

    imp_0060731C(this + 0x20, sub_0042F050() + 0x1638);
    imp_0060731C(this + 4, this + 0x20);
    imp_006071FC(this + 4, dir);
    imp_006071F8(&in, 1);
    imp_006071F4(&in, imp_0060732C(imp_006071DC(&name, this + 0x20, d_0060A2A8)), 0x21, 0x40);
    imp_00607330(&name);
    if (!imp_006071F0((char *)&in + *(int *)(*(char **)&in + 4))) {
        static const short head[][2] = { {0x50, 4}, {0x64, 4}, {0x3c, 1}, {0x60, 1}, {0x5c, 4}, {0x68, 1}, {0x69, 1} };
        imp_006071A0(&in, this + 0x40, 4);
        imp_006071A0(&in, this + 0x44, 4);
        screen_441DF0(this);
        for (k = 0; k < sizeof head / sizeof head[0]; k++)
            imp_006071A0(&in, this + head[k][0], head[k][1]);
        place_441DF0(this);
        for (k = 0; k < sizeof opt_441DF0 / sizeof opt_441DF0[0]; k++)
            imp_006071A0(&in, this + opt_441DF0[k][0], opt_441DF0[k][1]);
        imp_006071EC(&in);
    } else {
        void *d3d;
        static const unsigned int depth[] = { 0x47, 0x4d, 0x4b, 0x4f, 0x50, 0x49 };
        unsigned int caps[0x130 / 4];
        int w, h;
        unsigned char c;
        imp_006071EC(&in);
        imp_006071F4(&in, imp_0060732C(imp_006071DC(&name, this + 0x20, d_0060A2A8)), 0x32, 0x40);
        imp_00607330(&name);
        d3d = sub_005B8014(0x20);
        if (d3d) {
            this[0x6a] = 1;
            *(double *)(this + 0x80) = 1.0;
            this[0x6b] = 1;
            this[0x6c] = 1;
            this[0x6d] = 0;
            this[0x6e] = 1;
            this[0x6f] = 0;
            F(this + 0x70) = F(d_0060A2A4);
            F(this + 0x7c) = F(d_0060A2A4);
            F(this + 0x88) = F(d_0060A29C);
            F(this + 0x8c) = 1.0f;
            F(this + 0x74) = F(d_0060A2A0);
            F(this + 0x78) = F(d_00608C20);
            F(this + 0x90) = 1.0f;
            imp_00607334(&name, sub_0042F050() + 0x1638);
            imp_00607320(&name, d_0060A2A8);
            imp_006071E8(&out, imp_0060732C(&name), 0x22, 0x40, 1);
            w = 0x400;
            *(int *)(this + 0x40) = w;
            h = 0x300;
            *(int *)(this + 0x44) = h;
            imp_006071B0(&out, (char *)&w, 4);
            imp_006071B0(&out, (char *)&h, 4);
            this[0x3c] = 1;
            screen_441DF0(this);
            *(int *)(this + 0x50) = 0x16;
            if (((cdt_441DF0)(*(void ***)d3d)[0x24 / 4])(d3d, 0, 1, 0x16, 0x15, (unsigned char)this[0x3c]) >= 0)
                *(int *)(this + 0x50) = 0x15;
            imp_006071B0(&out, this + 0x50, 4);
            *(int *)(this + 0x64) = 1;
            imp_006071B0(&out, this + 0x64, 4);
            imp_006071B0(&out, this + 0x3c, 1);
            this[0x60] = 1;
            for (c = '1'; c < '6'; c++)
                if (((cdf_441DF0)(*(void ***)d3d)[0x28 / 4])(d3d, 0, 1, *(unsigned int *)(this + 0x50), 0, 3,
                                                             ((unsigned int)c << 24) | 0x545844) < 0) {
                    this[0x60] = 0;
                    break;
                }
            imp_006071B0(&out, this + 0x60, 1);
            for (k = 0; k < 6; k++)
                if (((cdf_441DF0)(*(void ***)d3d)[0x28 / 4])(d3d, 0, 1, 0x16, 2, 1, depth[k]) >= 0) {
                    *(unsigned int *)(this + 0x5c) = depth[k];
                    break;
                }
            imp_006071B0(&out, this + 0x5c, 4);
            ((caps_441DF0)(*(void ***)d3d)[0x38 / 4])(d3d, 0, 1, caps);
            this[0x68] = (caps[0x3c / 4] & 0x20) ? 0 : 1;
            imp_006071B0(&out, this + 0x68, 1);
            ((caps_441DF0)(*(void ***)d3d)[0x38 / 4])(d3d, 0, 1, caps);
            this[0x69] = (caps[0x9c / 4] & 0x40) ? 1 : 0;
            imp_006071B0(&out, this + 0x69, 1);
            place_441DF0(this);
            for (k = 0; k < sizeof opt_441DF0 / sizeof opt_441DF0[0]; k++)
                imp_006071B0(&out, this + opt_441DF0[k][0], opt_441DF0[k][1]);
            imp_006071B4(&out);
            imp_006071B8(&out);
            imp_00607330(&name);
        }
    }
    imp_006071D4(&in);
}
