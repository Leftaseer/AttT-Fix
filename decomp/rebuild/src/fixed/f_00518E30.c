/* 0x00518E30: CTacticLevel::vf3 (per-frame state step): first 0x004AD530 on +0x84 (its EAX input only passed through),
 * then by the state (+0x110): 1 - with the spell book's selected spell 4 (GUIScene.SpellBook.SelectedSpell)
 * 0x00509DA0 on +0xBC; releases the refcounted +0x114 (object at +4, count at +8); this level becomes current
 * (0x006CAAE8, 0x008D1230) and +0x130's +4 gets vf18; 2 and 3 - the closing screen (+0x21C) is drawn once more inside
 * BeginScene / EndScene (device vf A4 / A8) and deleted, the state cleared, TacticLevel.DeInit called, and the game
 * (+0x38) goes on (0x0046CF30 of its +0x80, its state +0xAC = 6); 4 - the closing screen is deleted (the pointer is
 * kept), the level becomes current (+0x130's +4 vf18, 0x0046CF30 of +0x8C) and with WorldLevel.SaveLoad 6 the state is
 * cleared and 0x00420960 runs on the game. Returns what the original leaves in EAX */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[0x30 / 4]; } Tmp_518E30;
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C int __thiscall sub_0057C660(void *self, const char *key);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C int __thiscall sub_00509DA0(void *self);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C int __thiscall sub_0046CF30(void *self);
DECOMP_C int __thiscall sub_00420960(void *self);
DECOMP_C char d_0060AD08[], d_00611AA0[], d_006139A4[], d_0060AB58[], d_00613FD0[], d_0060AB6C[], d_00613FC4[],
    d_006C8C10[], d_008D1230[], d_006CAAE8[];
typedef int (__thiscall *vf_518E30)(void *self);
typedef int (__thiscall *del_518E30)(void *self, int del);
typedef int (__stdcall *dev_518E30)(void *dev);

#define VT(o) (*(void ***)(o))

static int current_518E30(char *s)
{
    char *o;
    *(char **)d_008D1230 = s;
    *(char **)d_006CAAE8 = s;
    o = *(char **)(s + 0x130) + 4;
    return ((vf_518E30)VT(o)[0x18 / 4])(o);
}

static int close_518E30(char *s)
{
    char *dev = *(char **)d_006C8C10, *o, *g;
    unsigned int t[3];
    Tmp_518E30 fn, res;
    ((dev_518E30)VT(dev)[0xa4 / 4])(dev);
    o = *(char **)(s + 0x21c);
    ((vf_518E30)VT(o)[0x18 / 4])(o);
    dev = *(char **)d_006C8C10;
    ((dev_518E30)VT(dev)[0xa8 / 4])(dev);
    o = *(char **)(s + 0x21c);
    if (o) {
        ((del_518E30)VT(o)[0])(o, 1);
        *(void **)(s + 0x21c) = 0;
    }
    *(int *)(s + 0x110) = 0;
    sub_0057A180(sub_0057B770(sub_004323E0(t, d_0060AB58), &fn, d_00613FD0), &res, 0);
    sub_00427820(&res);
    sub_004378D0(&fn);
    sub_004220A0(t);
    g = *(char **)(s + 0x38);
    o = (char *)(size_t)sub_0046CF30(*(void **)(g + 0x80));
    *(int *)(g + 0xac) = 6;
    return (int)(size_t)o;
}

DECOMP(00518E30)
int __thiscall f_00518E30(void *this)
{
    char *s = (char *)this, *o;
    unsigned int st;
    sub_004AD530(*(void **)(s + 0x84), 0);
    st = *(unsigned int *)(s + 0x110) - 1;
    switch (st) {
    case 0: {
        unsigned int t[3], b[3];
        int sel;
        sel = sub_0057C660(sub_0057B4E0(sub_004323E0(t, d_0060AD08), b, d_00611AA0), d_006139A4) == 4;
        sub_004220A0(b);
        sub_004220A0(t);
        if (sel)
            sub_00509DA0(*(void **)(s + 0xbc));
        o = *(char **)(s + 0x114);
        if (o && !(*(int *)(o + 8) -= 1))
            ((del_518E30)VT(o + 4)[0])(o + 4, 1);
        *(void **)(s + 0x114) = 0;
        return current_518E30(s);
    }
    case 1:
    case 2:
        return close_518E30(s);
    case 3: {
        unsigned int t[3];
        int r, ok;
        o = *(char **)(s + 0x21c);
        if (o)
            ((del_518E30)VT(o)[0])(o, 1);
        current_518E30(s);
        sub_0046CF30(*(void **)(s + 0x8c));
        ok = sub_0057C660(sub_004323E0(t, d_0060AB6C), d_00613FC4) == 6;
        r = sub_004220A0(t);
        if (!ok)
            return r;
        *(int *)(s + 0x110) = 0;
        return sub_00420960(*(void **)(s + 0x38));
    }
    }
    return (int)st;
}
