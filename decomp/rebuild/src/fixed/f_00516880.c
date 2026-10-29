/* 0x00516880: CTacticCreature::Tick (CUpdateObject slot): the base update (0x004AC690), the current speed (+0x1F0,
 * vf80), then by the action state (+0x394): 1 walking the path (+0x398, step +0x39C) and turning to each node,
 * 2 / 3 / 5 / 7 waiting out +0x3A0 frames before the next animation (attack +0x234 -> 4, hit +0x240 or +0x23C ->
 * 6 with a random turn when killed, +0x238 -> 8), 4 / 8 attacking (the hit event 0x0060AC14 posted, the target
 * told, 8 then strikes, 0x00512940 -> 12), 6 taking the damage (+0x3DC: the floating number above the head, the
 * health bar +0x1E8, the blood effect, the hit events, dying 0x00512AE0), 11 waiting for the model, 12 the
 * strike's end (0x00512940 counter strike 0x005125B0), 13 / 14 the resurrection / teleport effect counting
 * +0x40C down; moving (0x004ACAC0) at 0.7 of the animation's step otherwise; then the animation (+0x224) and the
 * model (+0x220 vf14) run unless 9, and a pending slide (+0x410 frames of +0x414 / +0x418) moves the position */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_516880;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_516880;                 /* nScript::Table */
DECOMP_C void __cdecl sub_004AC690(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_00512400(void *self, void *out, int i);
DECOMP_C void __thiscall sub_004ACB80(void *self, float angle, int speed);
DECOMP_C void __thiscall sub_004AC9A0(void *self, void *pos);
DECOMP_C void __thiscall sub_004CAFE0(void *self, int a);
DECOMP_C unsigned int __cdecl sub_0044A3F0(void *self, unsigned int eax, void *ev);
DECOMP_C void __thiscall sub_004EF580(void *self, void *a, void *b);
DECOMP_C float *__thiscall sub_0042AAB0(void *self, void *out, float speed);
DECOMP_C int __thiscall sub_004ACAC0(void *self, void *step);
DECOMP_C void __thiscall sub_00512940(void *self);
DECOMP_C unsigned char __thiscall sub_004CAD80(void *self, void *model);
DECOMP_C void __cdecl sub_005125B0(void *self, unsigned int eax, void *target, int a);
DECOMP_C float __cdecl sub_004F6550(float lo, float hi, float steps);
DECOMP_C void __thiscall sub_00511E70(void *self, float angle);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float *__stdcall sub_005B80BC(float *out, const float *v, const void *vp, const void *proj, const void *view,
                                       const void *world);              /* D3DXVec3Project */
DECOMP_C void __thiscall sub_00513FA0(void *self, int health);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__cdecl sub_00584980(void *self, unsigned int ebx, float x, float y, Str_516880 text, int dead, int a);
DECOMP_C char *__cdecl sub_00432260(void);
DECOMP_C void __cdecl sub_005119A0(void *from, void *to, void *out, void *world);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void __thiscall sub_00512AE0(void *self);
DECOMP_C void __thiscall sub_00514650(void *self, unsigned int a);
DECOMP_C void *__thiscall sub_00550420(void *self, void *name, int a, int b);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C int __thiscall sub_0054FE30(void *self, int a, float b);
DECOMP_C void __cdecl sub_0054D350(void *self, int eax, float rate);
DECOMP_C void __thiscall sub_0042DC00(void *self, void *pos);
DECOMP_C void *__thiscall sub_005184B0(void *self);
DECOMP_C void *__cdecl sub_0044E7A0(void *name);
DECOMP_C float __thiscall sub_004ED000(void *self);
DECOMP_C void __thiscall sub_00512B60(void *self);
DECOMP_C void __thiscall sub_004CB070(void *self);
DECOMP_C char d_00607D54[], d_00613C24[], d_0060AC14[], d_006C8C3C[], d_0060A700[], d_00608B4C[], d_00613C20[],
    d_0060B888[], d_00613C68[], d_00613C58[], d_006CA2C4[], d_006C32E8[], d_00613E78[], d_00613E74[], d_00613BF8[],
    d_006CA8E8[], d_0060FA8B[], d_00613E60[], d_00613228[], d_00613214[], d_00613E4C[], d_00613E3C[], d_00613B6C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_00607320)(void *, const char *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C char *(__cdecl *imp_itoa)(int, char *, int) __asm__("__imp___itoa");
typedef float (__thiscall *vff_516880)(void *self);
typedef unsigned char (__thiscall *vfb_516880)(void *self);
typedef void (__thiscall *vf0_516880)(void *self);
typedef void (__thiscall *vfp_516880)(void *self, void *p);
typedef void (__thiscall *vfv_516880)(void *self, float v, int a);
typedef void (__thiscall *vf2_516880)(void *self, int a, int b);
typedef float *(__thiscall *pos_516880)(void *self);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define I(o) (*(int *)(this + (o)))
#define F(o) (*(float *)(this + (o)))
#define P(o) (*(void **)(this + (o)))
#define MODEL ((char *)P(0x220))
#define STATE I(0x394)

/* animation +off becomes the current one (+0x224) and starts */
static void anim_516880(char *this, int off, int a)
{
    P(0x224) = P(off);
    sub_004CAFE0(P(off), a);
}

/* moving by 0.7 of the animation's step at speed */
static void step_516880(char *this, float speed)
{
    unsigned int out[4];
    float *v = sub_0042AAB0(MODEL, out, speed), s[2];
    double k = *(double *)d_0060A700;
    float y = (float)(v[1] * k);
    s[0] = (float)(k * v[0]);
    s[1] = y;
    sub_004ACAC0(this, s);
}

/* the event ev with its owner posted to the queue q */
static void post_516880(void *q, void *ev)
{
    sub_0044A3F0(q, (unsigned int)(size_t)ev, ev);
}

/* waiting +0x3A4 up to +0x3A0 frames, then animation +off, the turn and state next: 1 when done */
static int wait_516880(char *this, int off, int next)
{
    if (++I(0x3a4) != I(0x3a0))
        return 0;
    anim_516880(this, off, 0);
    sub_004ACB80(this, F(0x3a8), 10);
    STATE = next;
    return 1;
}

/* the resurrection / teleport effect psp at the creature with its sound wav */
static void effect_516880(char *this, unsigned int a, const char *psp, const char *wav)
{
    char *ps, *snd;
    void *mem;
    Str_516880 s;
    sub_00514650(this, a);
    mem = sub_005E3EAE(0x690);
    if (mem) {
        Str_516880 e;
        imp_00607324(&e, d_0060FA8B);
        ps = (char *)sub_00550420(mem, &e, 0, 0);
        imp_00607330(&e);
    } else
        ps = 0;
    imp_00607324(&s, psp);
    sub_0054EA10(ps, &s);
    imp_00607330(&s);
    sub_0054D350(ps, sub_0054FE30(ps, 0, 0.0f), *(float *)d_00613228);
    ((vf0_516880)VF(ps, 0x4c))(ps);
    sub_0054FE30(ps, 0, 0.0f);
    ((void (__thiscall *)(void *, float))VF(ps, 4))(ps, *(float *)d_00613214);
    sub_0042DC00(ps + 0x2e4, this + 0x64);
    *(int *)(ps + 0x58) = *(int *)(ps + 0x64);
    *(int *)(ps + 0x5c) = *(int *)(ps + 0x68);
    *(int *)(ps + 0x60) = *(int *)(ps + 0x6c);
    *(float *)(ps + 0x64) = 0.0f;
    *(float *)(ps + 0x68) = 0.0f;
    *(float *)(ps + 0x6c) = 0.0f;
    ps[0x70] = 1;
    {
        void *list = sub_005184B0(sub_00432260());
        ((vfp_516880)VF(list, 4))(list, ps);
    }
    imp_00607324(&s, wav);
    snd = (char *)sub_0044E7A0(&s);
    *(char **)(sub_0042F160() + 0x48) = snd;
    imp_00607330(&s);
    snd = *(char **)(sub_0042F160() + 0x48);
    {
        void *f = VF(snd, 0x18);
        ((vfv_516880)f)(snd, sub_004ED000(*(void **)d_006C8C3C), 0);
    }
    snd = *(char **)(sub_0042F160() + 0x48);
    ((vf2_516880)VF(snd, 0xc))(snd, 1, 0);
}

/* the damage taken: the floating number, the health bar, the blood, the events */
static void damage_516880(char *this)
{
    float h, v[3];
    Str_516880 text;
    void *mem, *num;
    {
        Tbl_516880 t;
        h = sub_0057AD40(sub_004323E0(&t, d_00613C68), d_00613C58);
        sub_004220A0(&t);
    }
    {
        float d = F(0x368) - F(0x338), y;
        char *cam = *(char **)d_006CA2C4;
        v[2] = F(0x6c);
        v[0] = F(0x64);
        v[1] = F(0x68);
        y = d + d;
        y = y + h;
        v[1] = y + v[1];
        sub_005B80BC(v, v, cam + 0x22c, cam + 0xc8, cam + 0x88, d_006C32E8);
    }
    imp_006071E0(&text);
    {
        char buf[0x18];
        int n = I(0x3dc);
        if (this[0x3e0]) {
            imp_itoa(n, buf, 10);
            imp_0060731C(&text, this + 0x3f0);
            imp_00607320(&text, d_00613E78);
            imp_00607320(&text, buf);
        } else if (n < 0) {
            imp_itoa(-n, buf, 10);
            imp_006072F8(&text, d_00613E74);
            imp_00607320(&text, buf);
        } else {
            imp_itoa(n, buf, 10);
            imp_006072F8(&text, buf);
        }
    }
    sub_00513FA0(this, I(0x1ec) - I(0x3dc));
    mem = sub_005E3EAE(0x25c);
    if (mem) {
        Str_516880 t;
        int dead = I(0x1ec) - I(0x3dc) == 0;
        imp_00607334(&t, &text);
        num = sub_00584980(mem, 0, v[0], v[1], t, dead, 0);
    } else
        num = 0;
    {
        char *w = sub_00432260() + 4;
        ((vfp_516880)VF(w, 4))(w, num);
    }
    if (!P(0x3c0))
        P(0x3c0) = this;
    if (this[0x3d9]) {
        sub_004EF580(*(void **)d_006C8C3C, P(0x3c0), this);
        this[0x3d9] = 0;
    }
    F(0x1e8) = (float)(I(0x1ec) - I(0x3dc)) / (float)I(0x1e0);
    if (!this[0x3c8] && P(0x3c0)) {
        float p[3], q[3];
        char *w;
        p[1] = F(0x68);
        p[0] = F(0x64);
        p[1] = (F(0x368) - F(0x338)) + p[1];
        p[2] = F(0x6c);
        this[0x3c8] = 1;
        __builtin_memcpy(q, ((pos_516880)VF(P(0x3c0), 0x68))(P(0x3c0)), 12);
        w = *(char **)(sub_0042F160() + 0x5c);
        sub_005119A0(p, q, this + 0x248, w ? w + 4 : 0);
    }
    {
        void *ev1[2], *ev2[2];
        ev1[0] = d_00613BF8;
        ev1[1] = this;
        post_516880(this + 0x1d8, ev1);
        ev2[0] = d_00613BF8;
        ev2[1] = this;
        post_516880(d_006CA8E8, ev2);
    }
    imp_00607330(&text);
}

DECOMP(00516880)
void __thiscall f_00516880(void *self)
{
    char *this = (char *)self;

    sub_004AC690(this, 0);
    F(0x1f0) = ((vff_516880)VF(this, 0x80))(this);
    switch (STATE) {
    case 0:
        this[0x3c8] = 0;
        P(0x3c0) = 0;
        break;
    case 1: {
        char *path = (char *)P(0x398);
        unsigned int out[5];
        if (++I(0x39c) == *(int *)(path + 0x10)) {
            anim_516880(this, 0x228, 0);
            F(0x24) = *(float *)d_00607D54;
            STATE = 0;
            break;
        }
        {
            char *m = MODEL;
            int v = *(int *)sub_00512400(path, out, I(0x39c));
            *(int *)(m + 0x1cc) = v;
            *(int *)(*(char **)(m + 0x1c4) + 0x1d8) = v;
        }
        sub_004ACB80(this, ((float *)sub_00512400(P(0x398), out, I(0x39c)))[3], 10);
        sub_004AC9A0(this, (char *)sub_00512400(P(0x398), out, I(0x39c)) + 4);
        break;
    }
    case 2:
        if (++I(0x39c) == I(0x3a0)) {
            void *a = P(0x224);
            I(0x39c) = 0;
            F(0x24) = *(float *)d_00613C24;
            STATE = 1;
            sub_004CAFE0(a, 0);
            return;
        }
        break;
    case 3:
        if (wait_516880(this, 0x234, 4))
            return;
        break;
    case 4:
        if (((vfb_516880)VF(MODEL, 0xf8))(MODEL)) {
            void *ev = d_0060AC14;
            post_516880(this + 0x1d0, &ev);
            if (P(0x3c4))
                sub_004EF580(*(void **)d_006C8C3C, this, P(0x3c4));
        }
        if (MODEL[0x1dc]) {
            anim_516880(this, 0x228, 0);
            STATE = 0;
            break;
        }
        step_516880(this, F(0x84));
        break;
    case 5:
        if (++I(0x3a4) == I(0x3a0)) {
            if (I(0x1ec) - I(0x3dc) == 0) {
                float r;
                anim_516880(this, 0x240, 0);
                r = sub_004F6550(*(float *)d_0060B888, *(float *)d_00613C20, *(float *)d_00608B4C);
                F(0x3a8) = r + F(0x3a8);
                sub_00511E70(this, F(0x3a8));
            } else
                anim_516880(this, 0x23c, 0);
            sub_004ACB80(this, F(0x3a8), 10);
            STATE = 6;
            return;
        }
        break;
    case 6:
        if (((vfb_516880)VF(MODEL, 0xf8))(MODEL))
            damage_516880(this);
        if (MODEL[0x1dc]) {
            if (I(0x1ec) - I(0x3dc) != 0) {
                anim_516880(this, 0x228, 0);
                STATE = 0;
            } else
                sub_00512AE0(this);
            break;
        }
        step_516880(this, F(0x78));
        break;
    case 7:
        if (wait_516880(this, 0x238, 8))
            return;
        break;
    case 8:
        if (((vfb_516880)VF(MODEL, 0xf8))(MODEL)) {
            sub_00512940(this);
            I(0x3a4) = 0;
            STATE = 0xc;
        }
        step_516880(this, F(0x84));
        break;
    case 11:
        if (MODEL[0x1dc])
            STATE = 0;
        break;
    case 12:
        I(0x3a4)++;
        if (!(*(char **)(this + 0x3d0))[0x2c0]) {
            if (sub_004CAD80(P(0x228), MODEL)) {
                STATE = 0;
                break;
            }
            if (MODEL[0x1dc]) {
                anim_516880(this, 0x228, 0);
                STATE = 0;
                break;
            }
            if (!this[0x3d8]) {
                sub_004EF580(*(void **)d_006C8C3C, this, P(0x3c4));
                sub_005125B0(P(0x3c4), 0, this, -1);
                this[0x3d8] = 1;
            }
            break;
        }
        if (sub_004CAD80(P(0x238), MODEL) && MODEL[0x1dc]) {
            anim_516880(this, 0x228, 0);
            break;
        }
        step_516880(this, F(0x84));
        break;
    case 13:
        if (--I(0x40c) == 0xf)
            effect_516880(this, (unsigned int)I(0x2bc), d_00613E60, d_00613E4C);
        if (I(0x40c) == 0)
            sub_00512B60(this);
        break;
    case 14:
        if (--I(0x40c) == 0xf)
            effect_516880(this, (unsigned int)I(0x2c0), d_00613E3C, d_00613B6C);
        if (I(0x40c) == 0) {
            anim_516880(this, 0x228, 1);
            STATE = 0;
        }
        break;
    }
    if (STATE != 9) {
        sub_004CB070(P(0x224));
        ((vf0_516880)VF(MODEL, 0x14))(MODEL);
    }
    if (I(0x410) > 0) {
        int n = I(0x410);
        F(0x74) = F(0x414) + F(0x74);
        this[0x80] = 1;
        I(0x410) = n - 1;
        F(0x7c) = F(0x418) + F(0x7c);
    }
}
