/* 0x0045DAA0: a gizmo's update after the base (0x005B4100, its EAX input only passed through, approximated): when
 * shown (+0x258) with a range level (+0x1F0 above 0) reads its two ranges from the script table "GizmoRanges" by the
 * level's keys (+0x1E8: the key of field 2 through 0x0045D240 and 0x0045BBE0, field 6 through 0x0045BB70, those two
 * taking 3 and 6 in EBX; 0x0045C740 takes the key string by value), each a number (0x0057AD40) scaled by 0x0045C3E0
 * and squared into +0x260 and +0x264; with none, places its two parts (0x0045D330 on +0x288, 0x0045CA40 on +0x2A4).
 * Returns what the original leaves in EAX */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_0045DAA0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_0045DAA0;                 /* nScript::Table */
typedef struct { void *tbl; Str_0045DAA0 key; } Ref_0045DAA0;
DECOMP_C int __cdecl sub_005B4100(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_0045D240(void *self, void *out, int a);
DECOMP_C void *__cdecl sub_0045BBE0(void *self, unsigned int ebx, Str_0045DAA0 *out);
DECOMP_C void *__cdecl sub_0045BB70(void *self, unsigned int ebx, Str_0045DAA0 *out);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_0045DAA0 *__thiscall sub_0045C740(void *self, Ref_0045DAA0 *out, Str_0045DAA0 key);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C float __thiscall sub_0045C3E0(void *self, float v);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_0045D330(void *self, void *part);
DECOMP_C int __thiscall sub_0045CA40(void *self, void *part);
DECOMP_C char d_0060B9B4[];
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

static float range_0045DAA0(char *s, Str_0045DAA0 key, Tbl_0045DAA0 *t)
{
    Ref_0045DAA0 r, *p;
    float v;
    p = sub_0045C740(sub_004323E0(t, d_0060B9B4), &r, key);
    v = sub_0057AD40(p->tbl, imp_0060732C(&p->key));
    v = sub_0045C3E0(s, v);
    imp_00607330(&r.key);
    return v;
}

DECOMP(0045DAA0)
int __thiscall f_0045DAA0(void *this)
{
    char *s = (char *)this;
    struct { void *f; int i; } k;
    struct { Tbl_0045DAA0 t; unsigned int x; } t1;
    Tbl_0045DAA0 t2;
    Str_0045DAA0 key;
    int r = sub_005B4100(this, 0);
    if (!*(int *)(s + 0x258))
        return r;
    if (*(int *)(s + 0x1f0) <= 0) {
        sub_0045D330(this, s + 0x288);
        return sub_0045CA40(this, s + 0x2a4);
    }
    k.f = s + 0x1e8;
    k.i = 2;
    sub_0045BBE0(sub_0045D240(&k, &t1, 3), 3, &key);
    *(float *)(s + 0x260) = range_0045DAA0(s, key, &t2);
    sub_004220A0(&t2);
    sub_004220A0(&t1);
    *(float *)(s + 0x260) = *(float *)(s + 0x260) * *(float *)(s + 0x260);
    k.f = s + 0x1e8;
    k.i = 6;
    sub_0045BB70(&k, 6, &key);
    *(float *)(s + 0x264) = range_0045DAA0(s, key, &t2);
    r = sub_004220A0(&t2);
    *(float *)(s + 0x264) = *(float *)(s + 0x264) * *(float *)(s + 0x264);
    return r;
}
