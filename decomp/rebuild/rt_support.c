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
/* _chkstk for frames over a page (EAX the size; it probes and lowers ESP itself): the original's (0x5E4080) */
__asm__(".globl __chkstk\n__chkstk:\n\tjmp _d_005E4080\n");

/* The x87 intrinsics of the MSVC runtime take their arguments on the FPU stack (two: the first in ST1) and return
 * in ST0; generated code calls them through these (tools/autodecomp.py, ghidra/FpuIntrinsics.java). */
#define FPU1(n) __attribute__((naked)) double decomp##n(double x) \
    { __asm__("fldl 4(%esp)\n\tjmp *__imp__" #n); }
#define FPU2(n) __attribute__((naked)) double decomp##n(double x, double y) \
    { __asm__("fldl 4(%esp)\n\tfldl 12(%esp)\n\tjmp *__imp__" #n); }
FPU1(_CIsin) FPU1(_CIcos) FPU1(_CItan) FPU1(_CIsqrt) FPU1(_CIatan) FPU1(_CIasin) FPU1(_CIacos)
FPU1(_CIexp) FPU1(_CIlog) FPU1(_CIlog10) FPU1(_CIsinh) FPU1(_CIcosh) FPU1(_CItanh)
FPU2(_CIpow) FPU2(_CIatan2) FPU2(_CIfmod)

/* gh_call_any(fn, ecx, n, args): an indirect call whose callee pop the machine code does not tell (tools/icalls.py
 * found the decompiled code independent of ESP after it): the n dwords of args pushed, ECX set, the call made,
 * then ESP restored whatever the callee popped.  EDX:EAX and ST0 come back as the callee left them (gh_call_any_f
 * is the same code declared returning a double).  tools/autodecomp.py writes the calls. */
__asm__(".globl _gh_call_any\n.globl _gh_call_any_f\n_gh_call_any:\n_gh_call_any_f:\n"
        "\tpushl %ebp\n\tmovl %esp, %ebp\n\tpushl %esi\n\tpushl %edi\n"
        "\tmovl 16(%ebp), %ecx\n\tmovl 20(%ebp), %esi\n"
        "1:\ttestl %ecx, %ecx\n\tjz 2f\n\tdecl %ecx\n\tpushl (%esi,%ecx,4)\n\tjmp 1b\n"
        "2:\tmovl 12(%ebp), %ecx\n\tcalll *8(%ebp)\n"
        "\tleal -8(%ebp), %esp\n\tpopl %edi\n\tpopl %esi\n\tpopl %ebp\n\tret\n");
