/* 0x004D1DC0: CTalker::Update(dt): when active (+0x74) the base update runs (0x004AB7A0), the cursor is "Default",
 * then by state (+0x7C): 0 once the speaker (+0x128) has faded in (+0x29C >= 1) the last line (+0x148) starts (vf4C)
 * and the state is 1; 1 Frederic or Ulrick (+0x70) end at once (0x004D1450), otherwise space / escape (+0x134) skip
 * (0x004D1100) and a click goes on (+0x150 script, not when +0x135); 2 the choices (+0x144..+0x148) are white-blue,
 * the hovered one yellow with the "Use" cursor, a click on a choice calls Dialog.Select(+0x168[i]) and goes on, keys
 * 2..10 pick a choice (+0x13C, yellow, state 4, +0x138 = 20); 3 when the speaker is done (vf60) the talker ends
 * (0x005335F0, 0x006CA5A4 +0x50). The input (+0x11C) is consumed (0x0046CF30), its result returned; inactive, EAX
 * keeps the caller's exception chain as in the original */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4D1DC0;                 /* std::string */
typedef struct { unsigned int w[0x30 / 4]; } Tmp_4D1DC0;
DECOMP_C void __cdecl sub_004AB7A0(void *self, unsigned int eax, float dt);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C void __thiscall sub_00443460(void *self, void *name);
DECOMP_C void __thiscall sub_004D1450(void *self);
DECOMP_C void __thiscall sub_004D1100(void *self);
DECOMP_C int __thiscall sub_0046CF30(void *self);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004AD550(void *self, void *s);
DECOMP_C unsigned char __thiscall sub_004AD740(void *self, void *mouse);
DECOMP_C void *__thiscall sub_0057B320(void *self, void *out, int i);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void *__thiscall sub_0057A230(void *f, void *out, void *arg, int n);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C int __thiscall sub_00422000(void *self);
DECOMP_C void __thiscall sub_005335F0(void *self);
DECOMP_C char d_00607C00[], d_0068AE40[], d_006120E8[], d_006120E0[], d_0060B7B8[], d_00608A88[], d_00608A6C[],
    d_0061208C[], d_00612084[], d_008D122C[], d_0060826C[], d_00607CB8[], d_006CA5A4[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *vf_4D1DC0)(void *self);
typedef unsigned char (__thiscall *vfb_4D1DC0)(void *self);
typedef void *(__thiscall *vfp_4D1DC0)(void *self);

static void cursor_4D1DC0(const char *name)
{
    Str_4D1DC0 s;
    imp_00607324(&s, name);
    sub_00443460(sub_00421680(), &s);
    imp_00607330(&s);
}

static void color_4D1DC0(void *choice, const char *tex)
{
    Str_4D1DC0 s;
    imp_00607324(&s, tex);
    sub_004AD550(choice, &s);
    imp_00607330(&s);
}

static unsigned char hover_4D1DC0(void *choice)
{
    void *m = sub_00421680();
    return sub_004AD740(choice, ((vfp_4D1DC0)(*(void ***)m)[0x88 / 4])(m));
}

static void next_4D1DC0(char *this)
{
    if (!this[0x135]) {
        Tmp_4D1DC0 r;
        sub_0057A180(this + 0x150, &r, 0);
        sub_00427820(&r);
    }
}

DECOMP(004D1DC0)
int __thiscall f_004D1DC0(char *this, float dt)
{
    char *inp;
    void **v, **e;
    unsigned int i, n;

    if (!this[0x74]) {
        int chain;
        __asm__("movl %%fs:0, %0" : "=r"(chain));
        return chain;
    }
    sub_004AB7A0(this, 0, dt);
    cursor_4D1DC0(d_00607C00);
    switch (*(unsigned int *)(this + 0x7c)) {
    case 0:
        if (*(float *)(*(char **)(this + 0x128) + 0x29c) >= *(float *)d_0068AE40) {
            void *last = *(void **)(*(char **)(this + 0x148) - 4);
            *(int *)(this + 0x7c) = 1;
            ((vf_4D1DC0)(*(void ***)last)[0x4c / 4])(last);
        }
        sub_0046CF30(*(void **)(this + 0x11c));
        break;
    case 1:
        if (*(char **)(this + 0x70) && (imp_006071E4(*(char **)(this + 0x70) + 8, d_006120E8) ||
                                        imp_006071E4(*(char **)(this + 0x70) + 8, d_006120E0))) {
            sub_004D1450(this);
            break;
        }
        inp = *(char **)(this + 0x11c);
        n = *(unsigned int *)(inp + 0x664);
        for (i = 0; i < n; i++) {
            unsigned char *k = *(unsigned char **)(inp + 0x660) + i * 2;
            if (this[0x134] && (k[1] ? k[0] == 0x39 : k[0] == 1)) {
                sub_0046CF30(inp);
                sub_004D1100(this);
                goto done;
            }
        }
        n = *(unsigned int *)(inp + 0x670);
        for (i = 0; i < n; i++)
            if ((*(int **)(inp + 0x66c))[i] == 0 && this[0x134]) {
                sub_0046CF30(inp);
                next_4D1DC0(this);
                break;
            }
        break;
    case 2: {
        unsigned char *keys;
        cursor_4D1DC0(d_00607C00);
        for (e = *(void ***)(this + 0x144); e != *(void ***)(this + 0x148); e++) {
            color_4D1DC0(*e, d_0060B7B8);
            if (hover_4D1DC0(*e)) {
                color_4D1DC0(*e, d_00608A88);
                cursor_4D1DC0(d_00608A6C);
            }
        }
        inp = *(char **)(this + 0x11c);
        n = *(unsigned int *)(inp + 0x670);
        {
            int *btn = *(int **)(inp + 0x66c);
            for (i = 0; i < n; i++) {
                unsigned int j = 0;
                if (btn[i])
                    continue;
                while (1) {
                    unsigned char hit;
                    v = *(void ***)(this + 0x144);
                    if (!v || j >= (unsigned int)(*(void ***)(this + 0x148) - v))
                        break;
                    hit = hover_4D1DC0(v[j]);
                    j++;
                    if (hit) {
                        Tmp_4D1DC0 t, d, fn, res;
                        struct { void *vt; void *child; int a; } o;
                        sub_0057B320(this + 0x168, &t, j);
                        o.child = 0;
                        o.vt = d_0060826C;
                        o.a = 0;
                        {
                            void *f = sub_0057B770(sub_004323E0(&d, d_0061208C), &fn, d_00612084);
                            sub_00403390(*(void **)d_008D122C, -10000, t.w[2]);
                            o.a++;
                            sub_0057A230(f, &res, &o, 0);
                        }
                        sub_00427820(&res);
                        sub_004378D0(&fn);
                        sub_004220A0(&d);
                        o.vt = d_00607CB8;
                        sub_00422000(&o);
                        sub_0046CF30(*(void **)(this + 0x11c));
                        next_4D1DC0(this);
                        sub_004220A0(&t);
                        break;
                    }
                }
            }
        }
        inp = *(char **)(this + 0x11c);
        n = *(unsigned int *)(inp + 0x664);
        keys = *(unsigned char **)(inp + 0x660);
        for (i = 0; i < n; i++)
            if (keys[i * 2 + 1] && keys[i * 2] >= 2 && keys[i * 2] <= 10) {
                unsigned int c = keys[i * 2] - 2;
                *(unsigned int *)(this + 0x13c) = c;
                v = *(void ***)(this + 0x144);
                if (v && (unsigned int)(*(void ***)(this + 0x148) - v) > c) {
                    color_4D1DC0(v[*(unsigned int *)(this + 0x13c)], d_00608A88);
                    *(int *)(this + 0x7c) = 4;
                    *(int *)(this + 0x138) = 0x14;
                }
            }
        break;
    }
    case 3: {
        void *spk = *(void **)(this + 0x128);
        if (((vfb_4D1DC0)(*(void ***)spk)[0x60 / 4])(spk)) {
            this[0x74] = 0;
            if (*(void **)(this + 0x70)) {
                sub_005335F0(*(void **)(this + 0x70));
                *(void **)(this + 0x70) = 0;
            }
            *(*(char **)d_006CA5A4 + 0x50) = 1;
        }
        sub_0046CF30(*(void **)(this + 0x11c));
        break;
    }
    }
done:
    return sub_0046CF30(*(void **)(this + 0x11c));
}
