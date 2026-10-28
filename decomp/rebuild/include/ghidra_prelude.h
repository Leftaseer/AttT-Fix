/* ghidra_prelude.h - types and helper macros of Ghidra's C output, so decompiled functions compile again
 * (tools/autodecomp.py).  C11, clang, i686-pc-windows-msvc. */
#pragma once

typedef unsigned char undefined;
typedef unsigned char undefined1;
typedef unsigned short undefined2;
typedef unsigned int undefined3;
typedef unsigned int undefined4;
typedef unsigned long long undefined5;
typedef unsigned long long undefined6;
typedef unsigned long long undefined7;
typedef unsigned long long undefined8;
typedef unsigned char bool;
typedef unsigned char byte;
typedef signed char sbyte;
typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned short word;
typedef unsigned int uint;
typedef unsigned int dword;
typedef unsigned long ulong;
typedef long long longlong;
typedef unsigned long long ulonglong;
typedef unsigned long long qword;
typedef unsigned short wchar16;
typedef unsigned short wchar_t;
typedef double float10;          /* x87 extended precision; the MSVC ABI has no long double */
typedef unsigned int uint3;
typedef int int3;
typedef void *pointer;
typedef unsigned int pointer32;
typedef unsigned int ImageBaseOffset32;
typedef void code;

#define true 1
#define false 0
#define NULL ((void *)0)

/* CONCATxy(a, b): a (x bytes) in the high part, b (y bytes) in the low part */
#define GH_MASK(n) ((n) >= 8 ? ~0ULL : ((1ULL << ((n) * 8)) - 1))
/* (a float operand gives its bits, as the register or stack slot held them: 0x42DEE0 passes a float pair by value
 * as CONCAT44(uVar1, fStack_8)) */
static inline unsigned long long gh_fbits(const void *p, unsigned n)
{
    if (n == 4) { unsigned int r; __builtin_memcpy(&r, p, 4); return r; }
    double d = n == 8 ? *(const double *)p : (double)*(const long double *)p;
    unsigned long long r; __builtin_memcpy(&r, &d, 8); return r;
}
#define GH_U(x) ({ __typeof__(x) gh_u_v = (x); \
    __builtin_classify_type(gh_u_v) == 8 ? gh_fbits(&gh_u_v, sizeof gh_u_v) : (unsigned long long)gh_u_v; })
#define GH_CONCAT(x, y, a, b) (((GH_U(a) & GH_MASK(x)) << ((y) * 8)) | (GH_U(b) & GH_MASK(y)))
#define CONCAT11(a, b) ((unsigned short)GH_CONCAT(1, 1, a, b))
#define CONCAT12(a, b) ((unsigned int)GH_CONCAT(1, 2, a, b))
#define CONCAT13(a, b) ((unsigned int)GH_CONCAT(1, 3, a, b))
#define CONCAT14(a, b) GH_CONCAT(1, 4, a, b)
#define CONCAT21(a, b) ((unsigned int)GH_CONCAT(2, 1, a, b))
#define CONCAT22(a, b) ((unsigned int)GH_CONCAT(2, 2, a, b))
#define CONCAT24(a, b) GH_CONCAT(2, 4, a, b)
#define CONCAT26(a, b) GH_CONCAT(2, 6, a, b)
#define CONCAT31(a, b) ((unsigned int)GH_CONCAT(3, 1, a, b))
#define CONCAT32(a, b) GH_CONCAT(3, 2, a, b)
#define CONCAT35(a, b) GH_CONCAT(3, 5, a, b)
#define CONCAT41(a, b) GH_CONCAT(4, 1, a, b)
#define CONCAT42(a, b) GH_CONCAT(4, 2, a, b)
#define CONCAT43(a, b) GH_CONCAT(4, 3, a, b)
#define CONCAT44(a, b) GH_CONCAT(4, 4, a, b)
#define CONCAT51(a, b) GH_CONCAT(5, 1, a, b)
#define CONCAT62(a, b) GH_CONCAT(6, 2, a, b)
#define CONCAT71(a, b) GH_CONCAT(7, 1, a, b)
/* SUBxy(v, off): y bytes of v starting at byte off */
#define GH_SUB(v, off, y) (GH_U(v) >> ((off) * 8) & GH_MASK(y))
#define SUB21(v, o) ((unsigned char)GH_SUB(v, o, 1))
#define SUB41(v, o) ((unsigned char)GH_SUB(v, o, 1))
#define SUB42(v, o) ((unsigned short)GH_SUB(v, o, 2))
#define SUB43(v, o) ((unsigned int)GH_SUB(v, o, 3))
#define SUB81(v, o) ((unsigned char)GH_SUB(v, o, 1))
#define SUB82(v, o) ((unsigned short)GH_SUB(v, o, 2))
#define SUB84(v, o) ((unsigned int)GH_SUB(v, o, 4))
#define SUB101(v, o) ((unsigned char)0)
#define SUB104(v, o) ((unsigned int)(v))
#define SUB108(v, o) ((unsigned long long)(v))
#define ZEXT12(v) ((unsigned short)(unsigned char)(v))
#define ZEXT14(v) ((unsigned int)(unsigned char)(v))
#define ZEXT18(v) ((unsigned long long)(unsigned char)(v))
#define ZEXT24(v) ((unsigned int)(unsigned short)(v))
#define ZEXT28(v) ((unsigned long long)(unsigned short)(v))
#define ZEXT48(v) ((unsigned long long)(unsigned int)(v))
#define ZEXT816(v) ((unsigned long long)(v))
#define SEXT14(v) ((int)(signed char)(v))
#define SEXT24(v) ((int)(short)(v))
#define SEXT48(v) ((long long)(int)(v))
#define CARRY1(a, b) ((unsigned char)((unsigned char)(a) + (unsigned char)(b)) < (unsigned char)(a))
#define CARRY2(a, b) ((unsigned short)((unsigned short)(a) + (unsigned short)(b)) < (unsigned short)(a))
#define CARRY4(a, b) ((unsigned int)((unsigned int)(a) + (unsigned int)(b)) < (unsigned int)(a))
#define SCARRY4(a, b) ((((int)(a) + (int)(b)) ^ (int)(a)) & (((int)(a) + (int)(b)) ^ (int)(b))) < 0
#define SBORROW4(a, b) ((((int)(a) ^ (int)(b)) & ((int)(a) ^ (int)((int)(a) - (int)(b)))) < 0)
#define SBORROW1(a, b) ((((signed char)(a) ^ (signed char)(b)) & ((signed char)(a) ^ (signed char)((signed char)(a) - (signed char)(b)))) < 0)
#define SBORROW2(a, b) ((((short)(a) ^ (short)(b)) & ((short)(a) ^ (short)((short)(a) - (short)(b)))) < 0)
#define NAN_CHECK(x) ((x) != (x))
/* the x87 control word (fnstcw), the decompiler's in_FPUControlWord */
#define GH_FNSTCW ({ unsigned short gh_cw; __asm__ volatile("fnstcw %0" : "=m"(gh_cw)); gh_cw; })
/* the head of the SEH chain, fs:[0] (generated code drops the function's own registration; a value read from it
 * stays: tools/autodecomp.py) */
#define GH_FS0 ({ void *gh_fs0; __asm__ volatile("movl %%fs:0, %0" : "=r"(gh_fs0)); gh_fs0; })
/* (of the operand's size, as the decompiler's: ABS of a float is a float, stored back in 4 bytes, 0x438D70) */
#define ABS(x) __builtin_choose_expr(sizeof(x) == 4, __builtin_fabsf(x), __builtin_fabs(x))
#define SQRT(x) __builtin_choose_expr(sizeof(x) == 4, __builtin_sqrtf(x), __builtin_sqrt(x))
static inline double gh_rint(double x) { double r; __asm__("frndint" : "=t"(r) : "0"(x)); return r; }
#define ROUND(x) gh_rint(x)
/* float to integer, towards zero (the decompiler's TRUNC; also MSVC's fistp after its truncating fldcw) */
#define TRUNC(x) ((long long)(x))
/* the decompiler's CAST between a float and an integer type of one size keeps the bits (AutoExport.java) */
/* (a double where the decompiler had a float, 'f - 1.0' with the constant a double in C, 0x5352E0, or a long
 * long for a 4-byte integer, 0x5234B0: of 4 bytes first, as the decompiler's value is) */
#define GH_BC_SRC(T, x) __typeof__(__builtin_choose_expr(sizeof(x) == 8 && sizeof(T) == 4, \
    __builtin_choose_expr(__builtin_classify_type(x) == 8, (float)0, (unsigned int)0), (x)))
#define BITCAST(T, x) ({ GH_BC_SRC(T, x) gh_bc_v = (x); T gh_bc_r; \
    _Static_assert(sizeof gh_bc_v == sizeof gh_bc_r, "BITCAST of different sizes"); \
    __builtin_memcpy(&gh_bc_r, &gh_bc_v, sizeof gh_bc_r); gh_bc_r; })
/* a value stored to a piece of a variable (v._4_4_ = x): the bits of a float, the value of anything else (the
 * functions, not casts, keep the other branches valid for pointers) */
static inline unsigned int gh_f2u4(float x) { unsigned int r; __builtin_memcpy(&r, &x, 4); return r; }
static inline unsigned int gh_d2u4(double x) { float f = (float)x; unsigned int r; __builtin_memcpy(&r, &f, 4); return r; }
static inline unsigned int gh_u4(unsigned int x) { return x; }
static inline unsigned long long gh_d2u8(double x) { unsigned long long r; __builtin_memcpy(&r, &x, 8); return r; }
static inline unsigned long long gh_u8(unsigned long long x) { return x; }
#define GH_BITS4(x) _Generic((x), float: gh_f2u4, double: gh_d2u4, long double: gh_d2u4, default: gh_u4)(x)
/* an indirect call whose callee pop is unknown, ESP restored after it (rt_support.c; tools/autodecomp.py) */
unsigned long long __cdecl gh_call_any(void *fn, void *ecx, unsigned int n, const unsigned int *args);
double __cdecl gh_call_any_f(void *fn, void *ecx, unsigned int n, const unsigned int *args);
#define GH_BITS8(x) _Generic((x), float: gh_d2u8, double: gh_d2u8, long double: gh_d2u8, default: gh_u8)(x)
#define FLOOR(x) __builtin_floor(x)
#define CEIL(x) __builtin_ceil(x)
#define POPCOUNT(x) __builtin_popcount(x)
#define LZCOUNT(x) ((x) ? __builtin_clz(x) : 32)

#define DECOMP_C extern
#ifdef DECOMP_SCAN
#define DECOMP(addr) __decomp_marker__(addr)
#else
#define DECOMP(addr)
#endif
