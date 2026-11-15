/* 0x004281D0: numbers the grid cells inside the circle of the radius +0x74 around (+0x80, +0x84): every cell (the
 * negative coordinates clamped to 0) is mapped to a key by the functor at +0x44 (its function pointer at +0x4C), the
 * map at +0x88 counts a weight at +0x14 on the node of that key, and count the total; the second pass walks the map in
 * order and stores weight/total at +0x10, remembers at +0x1C whether the cell was hit and clears the weight. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00427DD0(void *self, void **out, unsigned int *key);
DECOMP_C void __thiscall sub_00427720(void *self);
DECOMP_C unsigned int __thiscall sub_00427530(void *self, float t);
typedef int *(__thiscall *cell_key_4281D0)(void *self, unsigned int *slot, int x, int y);

DECOMP(004281D0)
void __thiscall f_004281D0(void *this)
{
    char *s = (char *)this;
    int radius = *(int *)(s + 0x74);
    char *head = *(char **)(s + 0x8c);
    float total = 0.0f;
    int x, y;

    for (y = -radius; y < radius; y++) {
        for (x = -radius; x < radius; x++) {
            if (x * x + y * y <= radius * radius) {
                unsigned int slot[2] = {0, 0};
                int cx = *(int *)(s + 0x80) + x;
                int cy = *(int *)(s + 0x84) + y;
                int *found;
                unsigned int key;
                void *node;

                if (cx < 0)
                    cx = 0;
                if (cy < 0)
                    cy = 0;
                found = ((cell_key_4281D0)*(void **)(s + 0x4c))(s + 0x44, slot, cx, cy);
                key = (unsigned int)*found;
                sub_00427DD0(s + 0x88, &node, &key);
                total += 1.0f;
                if (node != head)
                    *(float *)((char *)node + 0x14) += 1.0f;
            }
        }
    }
    {
        char *node = *(char **)head;

        while (node != head) {
            sub_00427530(node + 0x10, *(float *)(node + 0x14) / total);
            *(char *)(node + 0x1c) = *(float *)(node + 0x14) != 0.0f;
            *(float *)(node + 0x14) = 0.0f;
            sub_00427720(&node);
        }
    }
}
