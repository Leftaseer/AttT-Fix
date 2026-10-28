/* 0x005B1190: drops the dragged item (+0x68): ends its drag (0x00591B80(1)), refreshes the cursor (0x006C8E70,
 * 0x005A2410(1, 0)), takes it from the list +0x44 (0x004485F0) and by its kind (+0x354): 2 hands it back to the
 * world's owner (0x0042F160's +0x5C, 0x0053B530 with its unit 0x0058F1E0); 1 takes its stack (0x0058F240) from the
 * unit's list (+0x1B0) and deletes it; 8 forgets its army in the script table ArmyPos by the army's Name (0x0057C220)
 * and calls the army script's "delete" (0x0057B770, 0x0057A180); the rest take its object (+0x1BC) from the stack's
 * list and delete it. +0x68 cleared; returns what the original leaves in EAX */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[6]; } Tmp_5B1190;
DECOMP_C void __thiscall sub_00591B80(void *self, int a);
DECOMP_C void __thiscall sub_005A2410(void *self, int a, int b);
DECOMP_C void __thiscall sub_004485F0(void *self, void *item);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C char *__thiscall sub_0058F1E0(void *self);
DECOMP_C int __thiscall sub_0053B530(void *self, void *unit);
DECOMP_C char *__thiscall sub_0058F240(void *self);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__cdecl sub_00463B40(void *self, unsigned int ebx, void *out);
DECOMP_C void __thiscall sub_0057C220(void *self, const char *key);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C char d_006C8E70[], d_00620908[], d_0061AFC8[], d_0060CA4C[];
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef int (__thiscall *del_5B1190)(void *self, int flags);

DECOMP(005B1190)
int __thiscall f_005B1190(void *this)
{
    char *s = (char *)this;
    char *it = *(char **)(s + 0x68), *a, *b, *c, *scr;
    void *tmp;
    int r;
    sub_00591B80(it, 1);
    sub_005A2410(*(void **)d_006C8E70, 1, 0);
    tmp = *(void **)(s + 0x68);
    sub_004485F0(s + 0x44, &tmp);
    it = *(char **)(s + 0x68);
    r = *(int *)(it + 0x354);
    switch (r) {
    case 2:
        a = *(char **)(sub_0042F160() + 0x5c);
        r = sub_0053B530(a, sub_0058F1E0(*(void **)(s + 0x68)));
        break;
    case 1:
        a = sub_0058F1E0(it);
        b = sub_0058F240(*(void **)(s + 0x68));
        tmp = b;
        sub_004485F0(a + 0x1b0, &tmp);
        *(void **)(b + 0x1bc) = 0;
        c = sub_0058F240(*(void **)(s + 0x68));
        r = c ? ((del_5B1190)(*(void ***)c)[0])(c, 1) : 0;
        break;
    case 0: case 3: case 4: case 5: case 6: case 7:
        b = sub_0058F240(it);
        c = *(char **)(*(char **)(s + 0x68) + 0x1bc);
        tmp = c;
        sub_004485F0(b + 0x1b0, &tmp);
        *(void **)(c + 0x1bc) = 0;
        it = *(char **)(s + 0x68);
        c = *(char **)(it + 0x1bc);
        r = c ? ((del_5B1190)(*(void ***)c)[0])(c, 1) : (int)(size_t)it;
        break;
    case 8: {
        unsigned int t[3], name[7];
        struct { void *obj; const char *key; } p;
        Tmp_5B1190 x, y;
        scr = *(char **)(it + 0x1bc) + 0x1f8;
        sub_004323E0(t, d_00620908);
        p.obj = scr;
        p.key = d_0061AFC8;
        sub_0057C220(t, imp_0060732C(sub_00463B40(&p, 0, name)));
        imp_00607330(name);
        sub_0057A180(sub_0057B770(scr, &x, d_0060CA4C), &y, 0);
        sub_00427820(&y);
        sub_004378D0(&x);
        r = sub_004220A0(t);
        break;
    }
    }
    *(void **)(s + 0x68) = 0;
    return r;
}
