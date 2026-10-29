/* 0x005B1FA0: moves the selected house (this +0x68, a two-state holder: active part 0x0058F1E0, placed part
 * 0x0058F240) to another owner (arg 1). In state 1 (+0x354): the house's entry (its +8 name, its table +0x1E8) leaves
 * the old owner's Houses table (0x0057C220) and joins the new owner's under the name, numbered (%s%u) while taken
 * (0x0057C660, 0x00449340 -> 0x0057BF50); the placed part keeps its world position in the new owner's frame (its
 * matrix 0x004ACD60, the owner's inverse) and turns by the old minus the new owner's heading, leaves the old owner's
 * list (+0x1B0, 0x004485F0; its +0x1BC cleared) and is attached to the new owner (0x0045E230). Otherwise the moved
 * part (+0x1BC) is re-parented likewise by 0x005B0ED0 (EBX given the new owner's placed part), the old holder leaves
 * this list (+0x44) and the old link is deleted (vf0(1)) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_5B1FA0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_5B1FA0;                 /* nScript::Table */
DECOMP_C char *__thiscall sub_0058F1E0(void *self);
DECOMP_C char *__thiscall sub_0058F240(void *self);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, Tbl_5B1FA0 *out, const char *key);
DECOMP_C void __thiscall sub_0057C220(void *self, const char *key);
DECOMP_C int __thiscall sub_0057C660(void *self, const char *key);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_00449340(void *self, void *out, Str_5B1FA0 name);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, void *val);
DECOMP_C void __thiscall sub_004491A0(void *self);
DECOMP_C float *__thiscall sub_004ACD60(void *self, float *out);
DECOMP_C void *__stdcall sub_005B801A(void *out, float *det, const void *m);         /* D3DXMatrixInverse */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C void __thiscall sub_004485F0(void *self, void *item);
DECOMP_C void __thiscall sub_0045E230(void *self, void *obj);
DECOMP_C void __cdecl sub_005B0ED0(void *self, void *ebx, void *owner);
DECOMP_C char d_00611ED0[], d_00620910[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");
typedef void (__thiscall *del_5B1FA0)(void *self, int del);

#define F(p, o) (*(float *)((char *)(p) + (o)))

static void place_5B1FA0(char *q, const float *v)
{
    *(unsigned int *)(q + 0x58) = *(unsigned int *)(q + 0x64);
    *(unsigned int *)(q + 0x5c) = *(unsigned int *)(q + 0x68);
    *(unsigned int *)(q + 0x60) = *(unsigned int *)(q + 0x6c);
    F(q, 0x64) = v[0];
    F(q, 0x68) = v[1];
    F(q, 0x6c) = v[2];
}

DECOMP(005B1FA0)
void __thiscall f_005B1FA0(void *this, char *owner)
{
    char *s = (char *)this, *m = *(char **)(s + 0x68), *a, *b, *p;
    float mtx[16], v[3];
    if (*(int *)(m + 0x354) == 1) {
        Str_5B1FA0 name, k;
        Tbl_5B1FA0 t1, t2, t3, h;
        unsigned int pair[10];
        struct { void *t; const char *k; } key;
        char buf[0x80];
        float f;
        a = sub_0058F1E0(m);
        imp_00607334(&name, sub_0058F240(*(void **)(s + 0x68)) + 8);
        sub_00435D90(&t1, sub_0058F240(*(void **)(s + 0x68)) + 0x1e8);
        sub_00435D90(&t2, a + 0x1e8);
        sub_0057C220(sub_0057B4E0(&t2, &h, d_00611ED0), imp_0060732C(&name));
        sub_004220A0(&h);
        b = sub_0058F1E0(owner);
        sub_00435D90(&t3, b + 0x1e8);
        if (sub_0057C660(&t3, imp_0060732C(&name))) {
            unsigned int i = 0;
            do {
                i++;
                imp_006073D0(buf, d_00620910, imp_0060732C(&name), i);
            } while (sub_0057C660(&t3, buf));
            imp_006072F8(&name, buf);
        }
        imp_00607334(&k, &name);
        key.t = &t3;
        key.k = d_00611ED0;
        p = (char *)sub_00449340(&key, pair, k);
        sub_0057BF50(p, imp_0060732C(p + 0xc), &t1);
        sub_004491A0(pair);
        sub_004ACD60(sub_0058F240(*(void **)(s + 0x68)), mtx);
        v[0] = mtx[12];
        v[1] = 0.0f;
        v[2] = mtx[14];
        {
            float m2[16];
            __builtin_memcpy(mtx, sub_004ACD60(b, m2), sizeof mtx);
        }
        sub_005B801A(mtx, 0, mtx);
        sub_005B8026(v, v, mtx);
        f = F(a, 0x78);
        p = sub_0058F240(*(void **)(s + 0x68));
        p[0x80] = 1;
        F(p, 0x78) = F(p, 0x78) + f;
        f = F(b, 0x78);
        p = sub_0058F240(*(void **)(s + 0x68));
        p[0x80] = 1;
        F(p, 0x78) = F(p, 0x78) - f;
        p = sub_0058F240(*(void **)(s + 0x68));
        place_5B1FA0(p, v);
        p[0x70] = 1;
        p = sub_0058F240(*(void **)(s + 0x68));
        sub_004485F0(a + 0x1b0, &p);
        *(void **)(p + 0x1bc) = 0;
        sub_0045E230(b, sub_0058F240(*(void **)(s + 0x68)));
        sub_004220A0(&t3);
        sub_004220A0(&t2);
        sub_004220A0(&t1);
        imp_00607330(&name);
    } else {
        char *q, *old;
        float f1, f2, t, r;
        b = sub_0058F240(owner);
        sub_004ACD60(*(void **)(m + 0x1bc), mtx);
        v[0] = mtx[12];
        v[1] = mtx[13];
        v[2] = mtx[14];
        p = sub_0058F240(m);
        f1 = F(p, 0x78);
        f2 = F(*(char **)(p + 0x1bc), 0x78);
        sub_005B0ED0(this, b, b);
        q = *(char **)(*(char **)(s + 0x68) + 0x1bc);
        sub_004ACD60(b, mtx);
        sub_005B801A(mtx, 0, mtx);
        sub_005B8026(v, v, mtx);
        t = f2 + f1;
        place_5B1FA0(q, v);
        t = t + F(q, 0x78);
        F(q, 0x78) = t;
        q[0x80] = 1;
        q[0x70] = 1;
        r = F(*(char **)(b + 0x1bc), 0x78) + F(b, 0x78);
        F(q, 0x78) = t - r;
        old = m;
        sub_004485F0(s + 0x44, &old);
        old = *(char **)(m + 0x1bc);
        sub_004485F0(sub_0058F240(m) + 0x1b0, &old);
        *(void **)(old + 0x1bc) = 0;
        old = *(char **)(m + 0x1bc);
        if (old)
            ((del_5B1FA0)**(void ***)old)(old, 1);
    }
}
