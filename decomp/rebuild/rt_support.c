/* Bits of the MSVC runtime that clang-compiled code expects and the original exe does not export. */
int _fltused = 0x9875;

/* 64-bit unsigned division helpers of the MSVC runtime that the original exe does not contain (AttT links only
 * _alldiv/_allrem).  Arguments on the stack, the callee pops them, the result in EDX:EAX. */
static unsigned long long udivmod64(unsigned long long n, unsigned long long d, unsigned long long *rem)
{
    unsigned long long q = 0, r = 0;
    for (int i = 63; i >= 0; i--) {
        r = (r << 1) | ((n >> i) & 1);
        if (r >= d) {
            r -= d;
            q |= 1ULL << i;
        }
    }
    if (rem)
        *rem = r;
    return q;
}
unsigned long long __stdcall rt_aulldiv(unsigned long long n, unsigned long long d) { return udivmod64(n, d, 0); }
unsigned long long __stdcall rt_aullrem(unsigned long long n, unsigned long long d)
{
    unsigned long long r;
    udivmod64(n, d, &r);
    return r;
}
__asm__(".globl __aulldiv\n__aulldiv:\n\tjmp _rt_aulldiv@16\n"
        ".globl __aullrem\n__aullrem:\n\tjmp _rt_aullrem@16\n");
