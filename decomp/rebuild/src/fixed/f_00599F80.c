/* 0x00599F80 (ECX = the source object, args: the int (x, y) pairs, the vertex count, the vertex color; ret 0xC):
 * allocates count 28-byte vertices (operator new[] 0x005E3B10, an overflowing size asks for 0xFFFFFFFF and a null
 * result returns 0x8007000E) and fills each with x = [this+0x174] + pair.x, y = [this+0x178] + pair.y (int
 * additions rounded once), u = 0.5 (0x0060B874), v = 1.0 (0x0068AE40), the color at +0x10 and two zero floats.
 * The shared batch state 0x008D125C is then initialized once (flag 0x008D1280 bit 0, nine zeroed dwords and
 * 0x005E3F71(0x00606210)), and the global renderer 0x008D127C runs its slot 0x160 (begin, an out object), 0x164
 * (the value of 0x006C8280), four 0x10C state pairs (0,1,3) (0,4,3) (0,1,4) (0,4,4), 0x14C (a strip of count-1
 * segments, 0x1C stride) and 0x15C (end, the same out object), which is then released through its slot +8;
 * the vertices are deleted and 0 is returned.  The 0x28 slot of 0x008D1260 opens the batch.  The compiler inlined
 * the one-time guard twice, but the second copy is unreachable because the first copy sets the flag. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                             /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *block);                                    /* operator delete[] */
DECOMP_C void __cdecl sub_005E3F71(void *guard);
DECOMP_C char d_0060B874[], d_0068AE40[], d_00606210[], d_006C8280[], d_008D125C[], d_008D1280[];
DECOMP_C char d_008D1260[], d_008D127C[];

typedef void (__stdcall *vf0_599F80)(void *self);
typedef void (__stdcall *vf1_599F80)(void *self, void *a);
typedef void (__stdcall *vf3_599F80)(void *self, unsigned int a, unsigned int b, unsigned int c);
typedef void (__stdcall *draw_599F80)(void *self, unsigned int type, unsigned int count, void *verts,
                                      unsigned int stride);

#define INIT_599F80 ((unsigned int *)d_008D125C)
#define FLAG_599F80 (*(unsigned int *)d_008D1280)
#define LOCK_599F80 (*(void **)d_008D1260)
#define RENDERER_599F80 (*(void **)d_008D127C)
#define CALL_599F80(o, off, type) ((type)(*(void ***)(o))[(off) / 4])

DECOMP(00599F80)
unsigned int __thiscall f_00599F80(void *this, const int *pairs, unsigned int count, unsigned int color)
{
    char *t = (char *)this;
    unsigned long long bytes = (unsigned long long)count * 0x1c;
    float *verts = (float *)sub_005E3B10(bytes > 0xffffffffu ? 0xffffffffu : (unsigned int)bytes);
    void *renderer, *out = 0;
    unsigned int i;

    if (!verts)
        return 0x8007000e;
    for (i = 0; i < count; i++) {
        char *v = (char *)verts + i * 0x1c;
        *(float *)(v + 0x00) = (float)((double)*(int *)(t + 0x174) + (double)pairs[i * 2 + 0]);
        *(float *)(v + 0x04) = (float)((double)pairs[i * 2 + 1] + (double)*(int *)(t + 0x178));
        *(float *)(v + 0x08) = *(float *)d_0060B874;                                /* 0.5 */
        *(float *)(v + 0x0c) = *(float *)d_0068AE40;                                /* 1.0 */
        *(unsigned int *)(v + 0x10) = color;
        *(float *)(v + 0x14) = 0.0f;
        *(float *)(v + 0x18) = 0.0f;
    }
    if (!(FLAG_599F80 & 1)) {
        FLAG_599F80 |= 1;
        INIT_599F80[2] = 0;
        INIT_599F80[3] = 0;
        INIT_599F80[4] = 0;
        INIT_599F80[5] = 0;
        INIT_599F80[6] = 0;
        INIT_599F80[7] = 0;
        INIT_599F80[8] = 0;
        INIT_599F80[0] = 0;
        INIT_599F80[1] = 0;
        sub_005E3F71(d_00606210);
    }
    renderer = RENDERER_599F80;
    CALL_599F80(LOCK_599F80, 0x28, vf0_599F80)(LOCK_599F80);
    CALL_599F80(renderer, 0x160, vf1_599F80)(renderer, &out);
    CALL_599F80(renderer, 0x164, vf1_599F80)(renderer, *(void **)d_006C8280);
    CALL_599F80(renderer, 0x10c, vf3_599F80)(renderer, 0, 1, 3);
    CALL_599F80(renderer, 0x10c, vf3_599F80)(renderer, 0, 4, 3);
    CALL_599F80(renderer, 0x14c, draw_599F80)(renderer, 3, count - 1, verts, 0x1c);
    CALL_599F80(renderer, 0x10c, vf3_599F80)(renderer, 0, 1, 4);
    CALL_599F80(renderer, 0x10c, vf3_599F80)(renderer, 0, 4, 4);
    CALL_599F80(renderer, 0x15c, vf1_599F80)(renderer, out);
    CALL_599F80(out, 0x08, vf0_599F80)(out);
    sub_005E3EBA(verts);
    return 0;
}
