/* What the Lua sources need from the C runtime that the game's MSVCR80 does not export as such.
 * - The math functions: MSVC compiled them to its x87 intrinsics (_CIsin, ...: the arguments on the FPU stack), as
 *   the original Lua does; rebuild/rt_support.c calls those (decomp_CIsin, ...).
 * - strtod: the headers name mingw's own (__strtod); the original calls MSVCR80's.
 * - stdin/stdout/stderr: the mingw-w64 headers ask __acrt_iob_func (the newer runtimes); MSVCR80 has __iob_func,
 *   the array of its FILEs (the same layout).
 * - The vftable of type_info, which the C++ exception tables point to: the runtime matches a thrown type by the
 *   name in its descriptor, never through this table. */
#include <stdio.h>
#include <stdlib.h>

extern "C" {
double decomp_CIsin(double), decomp_CIcos(double), decomp_CItan(double), decomp_CIasin(double),
       decomp_CIacos(double), decomp_CIatan(double), decomp_CIsinh(double), decomp_CIcosh(double),
       decomp_CItanh(double), decomp_CIexp(double), decomp_CIlog(double), decomp_CIlog10(double),
       decomp_CIsqrt(double), decomp_CIatan2(double, double), decomp_CIfmod(double, double),
       decomp_CIpow(double, double);

double sin(double x) { return decomp_CIsin(x); }
double cos(double x) { return decomp_CIcos(x); }
double tan(double x) { return decomp_CItan(x); }
double asin(double x) { return decomp_CIasin(x); }
double acos(double x) { return decomp_CIacos(x); }
double atan(double x) { return decomp_CIatan(x); }
double sinh(double x) { return decomp_CIsinh(x); }
double cosh(double x) { return decomp_CIcosh(x); }
double tanh(double x) { return decomp_CItanh(x); }
double exp(double x) { return decomp_CIexp(x); }
double log(double x) { return decomp_CIlog(x); }
double log10(double x) { return decomp_CIlog10(x); }
double sqrt(double x) { return decomp_CIsqrt(x); }
double atan2(double y, double x) { return decomp_CIatan2(y, x); }
double fmod(double x, double y) { return decomp_CIfmod(x, y); }
double hypot(double x, double y) { return decomp_CIsqrt(x * x + y * y); }
int abs(int x) { return x < 0 ? -x : x; }

#undef strtod                         /* (stdlib.h makes it mingw's own __strtod: MSVCR80's, as the game) */
double __cdecl strtod(const char *, char **);
double __cdecl __strtod(const char *s, char **end) { return strtod(s, end); }

#undef __iob_func                     /* (stdio.h makes it the _iob variable of the old msvcrt) */
FILE *__cdecl __iob_func(void);
FILE *__cdecl __acrt_iob_func(unsigned index) { return &__iob_func()[index]; }

extern const void *const decomp_type_info_vftable[2] __asm__("??_7type_info@@6B@");
const void *const decomp_type_info_vftable[2] = {0, 0};
}
