/* 0x0044F2E0: CEngine::Init(command line): the log (0x0044B140), the 0x8018-byte pool 0x006C8C40, the settings
 * (+0x54, 0x00427990), Miles sound (0x004C4A40 "MSS", 44100 Hz 16 bit stereo), the resource pack (+0x88,
 * "<GamePath>Resource.pak"), the start-up 0x0044EA20; Direct3D 9 and its device (0x006C8C10; mixed, then
 * software vertex processing, then the reference device; failures throw from Engine.cpp lines 0x340 / 0x399),
 * cleared; the input (+0x80, 0x0046C510 with -save 1 / -replay 2), the world level script, the camera (+0x8C,
 * screen size), the logo videos (unless -nologo or the editor), the default effect (+0x84), the ambient colour
 * from +0x64 and its lights; then the main menu (+0x68) or, with -nologo / the editor, the world level (+0x70)
 * becomes the scene (+0x5C) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_44F2E0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_44F2E0;                 /* nScript::Table */
typedef struct { unsigned int w[6]; } Get_44F2E0;                 /* nScript::TableGet */
DECOMP_C void __cdecl sub_0044B140(Str_44F2E0 cmd);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C void __cdecl sub_004C4A40(void *name, int rate, int bits, int channels, void *hwnd);
DECOMP_C void __cdecl sub_004C4DE0(void);
DECOMP_C void __cdecl sub_00432EA0(void *eax);
DECOMP_C void *__cdecl sub_0044ABE0(void);
DECOMP_C void __thiscall sub_00451E90(void *self, void *name);
DECOMP_C void __cdecl sub_0044AB70(void);
DECOMP_C void __cdecl sub_0044B020(void);
DECOMP_C void __cdecl sub_0044EA20(void *self, unsigned int ebx);
DECOMP_C void *__stdcall sub_005B8014(unsigned int sdk);            /* Direct3DCreate9 */
DECOMP_C const char *__stdcall sub_005B8210(long hr);               /* DXGetErrorString9 */
DECOMP_C void *__cdecl sub_005E40BE(void *p, int c, unsigned int n);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char *__cdecl sub_00599A20(void);
DECOMP_C void __thiscall sub_005964B0(void *self, void *dev);
DECOMP_C void __thiscall sub_00594380(void *self);
DECOMP_C void __thiscall sub_00441C60(void *self);
DECOMP_C void __thiscall sub_0044E690(void *self);
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C void __thiscall sub_0046C510(void *self, int mode);
DECOMP_C void __cdecl sub_0044AD90(void);
DECOMP_C void __thiscall sub_00432620(void *self, const char *name);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void __thiscall sub_004357B0(void *self, float w, float h);
DECOMP_C void __cdecl sub_0044AB10(void);
DECOMP_C void *__cdecl sub_00442E20(void);
DECOMP_C void __thiscall sub_004A0990(void *self);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C void __cdecl sub_004F7780(Str_44F2E0 name, int w, int h);
DECOMP_C void *__thiscall sub_00448F10(void *self, void *name);
DECOMP_C void __cdecl sub_00551570(int a, int b);
DECOMP_C void __thiscall sub_005ACB40(void *self);
DECOMP_C void *__thiscall sub_00437970(void *self, const char *name, int a);
DECOMP_C void *__thiscall sub_00472CB0(void *self, void *level);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_00543410(void *self);
DECOMP_C void __thiscall sub_00545400(void *self, Str_44F2E0 name, void *save);
DECOMP_C char *__cdecl sub_0042F050(void);
DECOMP_C void __cdecl sub_0054B510(void *eax, void *msg, int a);
DECOMP_C void __thiscall sub_004E4200(void *self);
DECOMP_C char d_0060AC70[], d_006C8C40[], d_0060B104[], d_006C889C[], d_0060B0F4[], d_0060B0D0[], d_0060ADF8[],
    d_0069916C[], d_006C8C10[], d_0060B0A8[], d_0060B0A0[], d_0060B098[], d_006C88D8[], d_006C88D4[], d_0060B088[],
    d_0060AEB4[], d_0068AE08[], d_0060B084[], d_0068AE40[], d_0060B080[], d_0060B07C[], d_0060B074[], d_0060B068[],
    d_0060B05C[], d_0060B050[], d_0060B044[], d_00607C00[], d_006C8714[], d_00609620[], d_0060B034[], d_0060B02C[],
    d_0060ACC8[], d_00607CC4[], d_006C8C38[], d_006C8C30[], d_0060FA8B[], d_0060B00C[], d_0060B008[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C unsigned char (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C int (__stdcall *imp_GetWindowRect)(void *, void *) __asm__("__imp__GetWindowRect@8");
DECOMP_C int (__stdcall *imp_SetWindowPos)(void *, void *, int, int, int, int, unsigned int) __asm__("__imp__SetWindowPos@28");
DECOMP_C int (__stdcall *imp_ShowCursor)(int) __asm__("__imp__ShowCursor@4");
typedef long (__stdcall *create_44F2E0)(void *d3d, unsigned int adapter, int type, void *hwnd, unsigned int flags,
                                         void *pp, void *dev);
typedef long (__stdcall *clear_44F2E0)(void *dev, unsigned int n, void *rects, unsigned int flags, unsigned int color,
                                        float z, unsigned int stencil);
typedef long (__stdcall *rs_44F2E0)(void *dev, unsigned int state, unsigned int v);
typedef long (__stdcall *light_44F2E0)(void *dev, unsigned int i, void *light);
typedef long (__stdcall *enable_44F2E0)(void *dev, unsigned int i, int on);
typedef void (__thiscall *begin_44F2E0)(void *self, unsigned int *passes, int flags);
typedef void (__thiscall *vfi_44F2E0)(void *self, int a);
typedef void (__thiscall *vf0_44F2E0)(void *self);
typedef void (__thiscall *get_44F2E0)(void *self, const char *name, void *out);
typedef void (__thiscall *show_44F2E0)(void *self, void *name, void *args, int a);
typedef void (__thiscall *vfp_44F2E0)(void *self, void *p);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define CFG (*(char **)(this + 0x54))
#define HWND (*(void **)d_006C889C)
#define DEV (*(void **)d_006C8C10)

static void fail_44F2E0(void *msg, int line)
{
    unsigned int exc[7];
    sub_00421220(exc, msg, d_0060ADF8, line);
    sub_005E3EC0(exc, d_0069916C);
}

/* c-string equality the way the original compares n bytes */
static int same_44F2E0(const char *a, const char *b, int n)
{
    while (n--)
        if (*a++ != *b++)
            return 0;
    return 1;
}

static void logo_44F2E0(char *this, const char *file)
{
    Str_44F2E0 s;
    int w = *(int *)(CFG + 0x40), h = *(int *)(CFG + 0x44);
    imp_00607324(&s, file);
    sub_004F7780(s, w, h);
}

/* a colour channel: the float times 0x00609620, truncated */
static int chan_44F2E0(float f)
{
    return (int)(long long)(float)(f * *(double *)d_00609620);
}

DECOMP(0044F2E0)
void __thiscall f_0044F2E0(void *self, const void *cmd)
{
    char *this = (char *)self;
    unsigned int pp[0x38 / 4];
    void *mem, *d3d;

    {
        Str_44F2E0 s;
        imp_00607334(&s, cmd);
        sub_0044B140(s);
    }
    mem = sub_005E3EAE(0x8018);
    if (mem) {
        *(void **)mem = d_0060AC70;
        ((int *)mem)[3] = 0;
    }
    *(void **)d_006C8C40 = mem;
    *(char **)(this + 0x54) = sub_00427990();
    this[0xb1] = 0;
    {
        Str_44F2E0 s;
        imp_00607324(&s, d_0060B104);
        sub_004C4A40(&s, 0xac44, 0x10, 2, HWND);
        imp_00607330(&s);
    }
    sub_004C4DE0();
    sub_00432EA0(0);
    *(void **)(this + 0x88) = sub_0044ABE0();
    {
        Str_44F2E0 s;
        imp_006071DC(&s, CFG + 0x20, d_0060B0F4);
        sub_00451E90(*(void **)(this + 0x88), &s);
        imp_00607330(&s);
    }
    sub_0044AB70();
    sub_0044B020();
    sub_0044EA20(this, 0);
    d3d = sub_005B8014(0x20);
    *(void **)(this + 0x58) = d3d;
    if (!d3d) {
        Str_44F2E0 s;
        imp_00607324(&s, d_0060B0D0);
        fail_44F2E0(&s, 0x340);
    }
    {
        char *cfg = CFG;
        unsigned int fmt = *(unsigned int *)(cfg + 0x50), depth = *(unsigned int *)(cfg + 0x5c);
        long hr;
        sub_005E40BE(pp, 0, 0x38);
        pp[2] = fmt;
        pp[3] = 1;
        pp[4] = 0;
        pp[6] = 1;
        pp[7] = (unsigned int)(size_t)HWND;
        pp[9] = 1;
        pp[10] = depth;
        pp[11] = 1;
        pp[13] = 0x80000000u;
        if (cfg[0x3c]) {
            pp[8] = 0;
            pp[0] = *(unsigned int *)(cfg + 0x40);
            pp[1] = *(unsigned int *)(cfg + 0x44);
            pp[12] = 0;
        } else
            pp[8] = 1;
        if (((create_44F2E0)VF(d3d, 0x40))(d3d, 0, 1, HWND, 0x80, pp, d_006C8C10) < 0) {
            d3d = *(void **)(this + 0x58);
            if (((create_44F2E0)VF(d3d, 0x40))(d3d, 0, 1, HWND, 0x20, pp, d_006C8C10) < 0) {
                d3d = *(void **)(this + 0x58);
                hr = ((create_44F2E0)VF(d3d, 0x40))(d3d, 0, 2, HWND, 0x20, pp, d_006C8C10);
                if (hr < 0) {
                    Str_44F2E0 s, m;
                    imp_00607324(&s, d_0060B0A8);
                    imp_006071DC(&m, &s, sub_005B8210(hr));
                    fail_44F2E0(&m, 0x399);
                }
            }
        }
    }
    sub_005964B0(sub_00599A20(), DEV);
    sub_00594380(sub_00599A20());
    ((clear_44F2E0)VF(DEV, 0xac))(DEV, 0, 0, 3, 0, 1.0f, 0);
    sub_00441C60(CFG);
    sub_0044E690(this);
    {
        int mode;
        char *in;
        if (same_44F2E0(imp_0060732C(cmd), d_0060B0A0, 6)) {
            in = sub_004215D0();
            mode = 1;
        } else if (same_44F2E0(imp_0060732C(cmd), d_0060B098, 8)) {
            in = sub_004215D0();
            mode = 2;
        } else {
            in = sub_004215D0();
            mode = 0;
        }
        *(char **)(this + 0x80) = in;
        sub_0046C510(in, mode);
    }
    sub_0044AD90();
    sub_00432620(*(void **)d_006C88D4, (*(char **)d_006C88D8)[0x40] ? d_0060B088 : d_0060AEB4);
    {
        char *cam = sub_00424E70();
        *(char **)(this + 0x8c) = cam;
        sub_004357B0(cam, (float)*(unsigned int *)(CFG + 0x40), (float)*(unsigned int *)(CFG + 0x44));
        cam = *(char **)(this + 0x8c);
        *(float *)(cam + 0x74) = *(float *)d_0060B084;
        *(float *)(cam + 0x78) = *(float *)d_0068AE40;
        *(float *)(cam + 0x7c) = *(float *)d_0060B080;
        *(float *)(cam + 0x80) = *(float *)d_0060B07C;
        cam[0x84] = 1;
        cam = *(char **)(this + 0x8c);
        cam[0x211] = 0;
        *(float *)(cam + 0x214) = 0.0f;
        (*(char **)(this + 0x8c))[0x218] = 0;
    }
    sub_0044AB10();
    sub_004A0990(sub_00442E20());
    *(void **)(this + 0x90) = sub_00421680();
    if (imp_00607214(cmd, d_0060B074) && !(*(char **)d_006C88D8)[0x40]) {
        Str_44F2E0 path;
        int rc[4];
        imp_00607334(&path, CFG + 0x20);
        imp_GetWindowRect(HWND, rc);
        imp_SetWindowPos(HWND, 0, 0, 0, 0, 0, 3);
        imp_ShowCursor(0);
        logo_44F2E0(this, d_0060B068);
        logo_44F2E0(this, d_0060B05C);
        logo_44F2E0(this, d_0060B050);
        imp_00607330(&path);
    }
    {
        Str_44F2E0 s;
        imp_00607324(&s, (*(char **)d_006C88D8)[0x40] ? d_0060B044 : d_00607C00);
        *(void **)(this + 0x84) = sub_00448F10(*(void **)d_006C8714, &s);
        imp_00607330(&s);
    }
    {
        void *e = *(void **)(this + 0x84);
        unsigned int passes;
        ((begin_44F2E0)VF(e, 0x18))(e, &passes, 1);
        e = *(void **)(this + 0x84);
        ((vfi_44F2E0)VF(e, 0x20))(e, 0);
        e = *(void **)(this + 0x84);
        ((vf0_44F2E0)VF(e, 0x24))(e);
        e = *(void **)(this + 0x84);
        ((vf0_44F2E0)VF(e, 0x1c))(e);
    }
    {
        float *f = *(float **)(this + 0x64);
        unsigned int c = (unsigned int)(chan_44F2E0(f[1]) & 0xff);
        c = ((unsigned int)chan_44F2E0(f[4]) << 8 | c) << 8;
        c = (c | (unsigned int)(chan_44F2E0(f[2]) & 0xff)) << 8;
        c |= (unsigned int)(chan_44F2E0(f[3]) & 0xff);
        ((rs_44F2E0)VF(DEV, 0xe4))(DEV, 0x8b, c);
    }
    sub_00551570(0x1388, 4);
    {
        unsigned char *e;
        unsigned int i = 0;
        for (e = *(unsigned char **)(*(char **)(this + 0x64) + 0x18);
             e != *(unsigned char **)(*(char **)(this + 0x64) + 0x1c); e += 0x6c, i++) {
            ((light_44F2E0)VF(DEV, 0xcc))(DEV, i, e + 4);
            ((enable_44F2E0)VF(DEV, 0xd4))(DEV, i, *e);
        }
    }
    ((get_44F2E0)VF(*(void **)(this + 0x84), 0x30))(*(void **)(this + 0x84), d_0060B034, this + 0xa0);
    *(unsigned int *)(CFG + 0x94) = *(unsigned int *)(this + 0xa0);
    sub_005ACB40(*(void **)d_006C88D8);
    this[0xd0] = 1;
    if (!imp_006071E4(cmd, d_0060B074) && !(*(char **)d_006C88D8)[0x40]) {
        void *m;
        mem = sub_005E3EAE(0x198);
        if (mem) {
            Get_44F2E0 g;
            m = sub_00472CB0(mem, sub_00437970(&g, d_0060B02C, 1));
            *(void **)(this + 0x68) = m;
            sub_00427820(&g);
        } else
            *(void **)(this + 0x68) = 0;
        {
            Str_44F2E0 s;
            Tbl_44F2E0 nil;
            imp_00607324(&s, d_0060ACC8);
            nil.w[1] = 0;
            nil.w[0] = (unsigned int)(size_t)d_00607CC4;
            nil.w[2] = 0xffffffffu;
            m = *(void **)(this + 0x68);
            ((show_44F2E0)VF(m, 0x3c))(m, &s, &nil, 1);
            sub_004220A0(&nil);
            imp_00607330(&s);
        }
        m = *(char **)(this + 0x68) + 4;
        ((vfp_44F2E0)VF(m, 0xc))(m, *(void **)d_006C8C38);
        m = *(char **)(this + 0x68) + 4;
        ((vfp_44F2E0)VF(m, 0xc))(m, *(void **)d_006C8C30);
        *(void **)(this + 0x5c) = *(void **)(this + 0x68);
    } else {
        char *w, *cam;
        mem = sub_005E3EAE(0x3ec);
        w = mem ? (char *)sub_00543410(mem) : 0;
        *(char **)(this + 0x70) = w;
        {
            Str_44F2E0 save, e;
            imp_00607324(&save, d_0060FA8B);
            imp_00607324(&e, d_0060FA8B);
            sub_00545400(*(void **)(this + 0x70), e, &save);
            imp_00607330(&save);
        }
        if (*(void **)(*(char **)(this + 0x70) + 0x78)) {
            int k;
            for (k = 0; k < 4; k++) {
                cam = **(char ***)(*(char **)(*(char **)(this + 0x70) + 0x78) + 0x68);
                *(float *)(cam + 0x58 + 4 * k) = *(float *)(this + 0x2c + 4 * k);
            }
        }
        *(void **)(this + 0x5c) = *(void **)(this + 0x70);
    }
    ((vfi_44F2E0)VF(*(void **)(this + 0x5c), 8))(*(void **)(this + 0x5c), 0);
    {
        Str_44F2E0 a, b, c;
        imp_00607324(&a, d_0060B00C);
        imp_006071C0(&b, &a, *(char **)(this + 0x5c) + 0x1c);
        imp_006071DC(&c, &b, d_0060B008);
        sub_0054B510(sub_0042F050(), &c, 1);
        imp_00607330(&c);
        imp_00607330(&b);
        imp_00607330(&a);
    }
    this[0xa4] = 0;
    this[0xb0] = 0;
    *(double *)(this + 0x40) = *(double *)(CFG + 0x80);
    sub_004E4200(*(char **)(this + 0x7c) + 8);
    *(int *)(this + 0x60) = 0;
}
