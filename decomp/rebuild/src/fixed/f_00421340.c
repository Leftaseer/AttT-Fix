/* 0x00421340: C2DScene vf: the cursor point comes from the scene's +0x90 object (vtable 0x88).  Every entry of the
 * +0x8C object's +0x66C table that is 0 while the cursor lies outside the scene's rectangle (+0xA0, of the size the
 * +0x80 object holds at +0x74/+0x78) resets the scene's input (0x0046CF30 of its +0x38 object's input, state
 * +0xAC = 6); +0xB4 clear makes every such entry count without the test.  Every entry of the +0x664 table whose
 * second byte is set and whose first is 1 resets the input too.  The scene's +0x88 object (also when +0xB4 is clear
 * or the cursor is outside) or else its +0x84 object is then handed to the +0x90 object's vtable 0xE8, whose
 * result is returned. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0046CF30(void *self);

typedef void *(__thiscall *vf_88_421340)(void *self);
typedef void *(__thiscall *vf_e8_421340)(void *self, void *arg);

#define VT(o) (*(void ***)(o))

static int outside_421340(char *s, float x, float y)
{
    char *bounds;
    float left, top;
    if (*(unsigned char *)(s + 0xb4) == 0)
        return 1;
    bounds = *(char **)(s + 0x80);
    left = *(float *)(s + 0xa0);
    top = *(float *)(s + 0xa4);
    return x < left || left + *(float *)(bounds + 0x74) < x
        || y < top || top + *(float *)(bounds + 0x78) < y;
}

static void reset_421340(char *s)
{
    char *scene = *(char **)(s + 0x38);
    sub_0046CF30(*(void **)(scene + 0x80));
    *(int *)(scene + 0xac) = 6;
}

DECOMP(00421340)
void *__thiscall f_00421340(void *self)
{
    char *s = (char *)self;
    void *owner = *(void **)(s + 0x90);
    float *pos = (float *)((vf_88_421340)VT(owner)[0x22])(owner);
    float x = pos[0], y = pos[1];
    char *tables = *(char **)(s + 0x8c);
    int *flags = *(int **)(tables + 0x66c);
    unsigned i, n = *(unsigned *)(tables + 0x670);

    for (i = 0; i < n; i++)
        if (flags[i] == 0 && outside_421340(s, x, y))
            reset_421340(s);

    tables = *(char **)(s + 0x8c);
    {
        char *pairs = *(char **)(tables + 0x660);
        n = *(unsigned *)(tables + 0x664);
        for (i = 0; i < n; i++)
            if (pairs[2 * i + 1] != 0 && pairs[2 * i] == 1)
                reset_421340(s);
    }

    return ((vf_e8_421340)VT(owner)[0x3a])(owner,
                                           outside_421340(s, x, y) ? *(void **)(s + 0x88)
                                                                   : *(void **)(s + 0x84));
}
