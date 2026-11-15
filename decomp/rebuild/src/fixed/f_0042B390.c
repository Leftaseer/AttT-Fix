/* 0x0042B390: fills an int buffer with the key indices a loop animation passes through over `time` seconds.
 * For a time past one cycle (`0x210`+`0x214` is the cycle height, `0x218` the height of one key step) the whole
 * loop is repeated as often as needed; in either case the front (first..loop start-1) and the tail (loop end+1..
 * last) of the key list are appended so that the caller sees the animation from its first to its last key.
 * `*scale` receives the factor the caller multiplies its speed with to make the run last `time` seconds. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042B1F0(char *this, unsigned int count);

static void push_key(char *vec, unsigned int key)
{
    *(unsigned int *)(*(char **)(vec + 4) + *(int *)(vec + 8) * 4) = key;
    *(int *)(vec + 8) += 1;
}

DECOMP(0042B390)
unsigned int __thiscall f_0042B390(char *this, char *vec, float time, float *scale)
{
    int first = *(int *)(this + 0x1d0);
    int last = *(int *)(this + 0x1d4);
    int start = *(int *)(this + 0x204);
    int end = *(int *)(this + 0x208);
    float total = *(float *)(this + 0x214) + *(float *)(this + 0x210);
    float step = *(float *)(this + 0x218);
    unsigned int i;

    if (total < time) {
        int laps = (int)((time - total) / step);
        float rem = (float)(unsigned int)laps * step + total;
        float below = rem <= time ? time - rem : rem - time;
        float next = (float)(unsigned int)(laps + 1) * step + total;
        float above = next <= time ? time - next : next - time;
        if (above < below)
            laps += 1;
        *scale = time / ((float)(unsigned int)laps * step + total);
        sub_0042B1F0(vec, (end - start + 1) * laps - end + start + last);
        for (i = first; i < (unsigned int)start; i++)
            push_key(vec, i);
        for (; laps != 0; laps--) {
            for (i = start; i <= (unsigned int)end; i++)
                push_key(vec, i);
        }
        for (i = end + 1; i <= (unsigned int)last; i++)
            push_key(vec, i);
        return i;
    }
    *scale = time / total;
    sub_0042B1F0(vec, start - end + last);
    for (i = first; i < (unsigned int)start; i++)
        push_key(vec, i);
    for (i = end + 1; i <= (unsigned int)last; i++)
        push_key(vec, i);
    return i;
}
