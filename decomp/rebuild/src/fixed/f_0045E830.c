/* 0x0045E830: places a gizmo from its script table (arg; EBX passes on to 0x0045BA50): in the editor (0x006C88D8's
 * +0x40) as a new 0x1F8-byte object (0x005AC790) attached (0x0045E230) and registered (0x005AD210); otherwise as a
 * floating label: the name of field 1 (0x0045BA50), the position of field 2 (0x0045CE60: x = [1], z = [3]) through
 * this one's world matrix (0x004ACE00, D3DXVec3TransformCoord) at the height of this (+0x78) and of its owner
 * (+0x1BC's +0x78) plus field 3, handed with the name to the labels 0x006C8E44 (0x00555160, which takes the label
 * object by value: vtable 0x0060B914, x, 0, z, a flag, the height). The flag (0x00555160: nonzero puts the label
 * on the ground, 0x00473110, instead of at its y of 0) is a byte the original never writes (its frame's +0x4C, left
 * over from earlier calls, nonzero in practice: its trees stand on the ground); 1 here (0 put the trees of save 241
 * at height 0, in front of Ogantar's houses) (the original destroys the temporaries if one throws; this C does
 * not) */
/* @conv ECX,EBX 4 */
/* @func 0045E830 custom */
#include "auto_pre.h"
typedef struct { void *vt; float x, y, z; unsigned char flag, pad[3]; float h; } Label_0045E830;
DECOMP_C void *__thiscall sub_005AC790(void *self, void *tbl);
DECOMP_C void __thiscall sub_0045E230(void *self, void *obj);
DECOMP_C void __thiscall sub_005AD210(void *self, void *obj);
DECOMP_C void __thiscall sub_004ACE00(void *self, void *m);
DECOMP_C void *__cdecl sub_0045BA50(void *self, unsigned int ebx, void *out);
DECOMP_C void __thiscall sub_0045CE60(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void __thiscall sub_00555160(void *self, void *name, Label_0045E830 l);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_006C88D8[], d_006C8E44[], d_0060B914[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0045E830)
void __cdecl f_0045E830(void *this, unsigned int ebx, void *tbl)
{
    char *s = (char *)this;
    struct { void *tbl; int i; } p;
    unsigned int m[16], s1[7], name[7], t0[3], t[3];
    float v[3], a, b, c, x, z, h;
    Label_0045E830 l;
    void *o;
    if ((*(char **)d_006C88D8)[0x40]) {
        o = sub_005E3EAE(0x1f8);
        o = o ? sub_005AC790(o, tbl) : 0;
        sub_0045E230(this, o);
        sub_005AD210(*(void **)d_006C88D8, o);
        return;
    }
    sub_004ACE00(this, m);
    p.tbl = tbl;
    p.i = 1;
    sub_0045BA50(&p, ebx, s1);
    imp_00607334(name, s1);
    imp_00607330(s1);
    p.tbl = tbl;
    p.i = 2;
    sub_0045CE60(&p, t0);
    sub_00435D90(t, t0);
    sub_004220A0(t0);
    a = sub_0057AC90(t, 3);
    b = sub_0057AC90(t, 1);
    v[0] = b;
    v[1] = 0.0f;
    v[2] = a;
    sub_005B8026(v, v, m);
    x = v[0];
    z = v[2];
    c = sub_0057AC90(tbl, 3);
    h = *(float *)(*(char **)(s + 0x1bc) + 0x78) + *(float *)(s + 0x78) + c;
    if (*(void **)d_006C8E44) {
        l.vt = d_0060B914;
        l.x = x;
        l.y = 0.0f;
        l.z = z;
        l.flag = 1;
        l.h = h;
        sub_00555160(*(void **)d_006C8E44, name, l);
    }
    sub_004220A0(t);
    imp_00607330(name);
}
