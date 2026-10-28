/* 0x00526580: Lua CalcVectorPos(i): (exactly two arguments, else the std::string "В CBorder::CalcVectorPos передали не правильные
 * аргументы" (wrong arguments) is thrown, Border.cpp line 0x11a) the border position i (8-byte points at +0x60) at
 * +0x74, and the rotation by the angle of the vector to the next point (0x005202B0): cos at +0x7C and +0x90, -sin at +0x80,
 * sin at +0x8C, the rest of the matrix 0 or 1 (0x68AE40); no results */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_00402A60(void *L);                            /* lua_gettop */
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);               /* lua_tonumber */
DECOMP_C double __cdecl sub_005202B0(float *v);
DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char d_00614B64[], d_00614ADC[], d_0069916C[], d_0068AE40[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");

DECOMP(00526580)
int __thiscall f_00526580(void *this, void *L)
{
    char *s = (char *)this;
    float *e, v[2], a, c, sn;
    int i;
    static const unsigned int zero[] = { 0x84, 0x88, 0x94, 0x98, 0x9c, 0xa0, 0xa8, 0xac, 0xb0, 0xb4 };
    if (sub_00402A60(L) != 2) {
        unsigned int msg[7], thrown[7];
        imp_00607324(msg, d_00614B64);
        sub_00421220(thrown, msg, d_00614ADC, 0x11a);
        sub_005E3EC0(thrown, d_0069916C);
    }
    i = (int)(long long)sub_00402DE0(L, 2);
    e = (float *)(*(char **)(s + 0x60) + i * 8);
    *(unsigned int *)(s + 0x74) = ((unsigned int *)e)[0];
    *(unsigned int *)(s + 0x78) = ((unsigned int *)e)[1];
    v[0] = e[2] - e[0];
    v[1] = e[3] - e[1];
    a = (float)sub_005202B0(v);
    for (i = 0; i < 10; i++)
        *(float *)(s + zero[i]) = 0.0f;
    *(unsigned int *)(s + 0xb8) = *(unsigned int *)d_0068AE40;
    *(unsigned int *)(s + 0xa4) = *(unsigned int *)d_0068AE40;
    c = (float)decomp_CIcos(a);
    *(float *)(s + 0x7c) = c;
    sn = (float)decomp_CIsin(a);
    *(float *)(s + 0x80) = -sn;
    *(float *)(s + 0x8c) = sn;
    *(float *)(s + 0x90) = c;
    return 0;
}
