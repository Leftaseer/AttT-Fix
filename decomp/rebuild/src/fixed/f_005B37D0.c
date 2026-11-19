/* 0x005B37D0: hover highlight of the world map tool (ECX, no arguments): the cursor position from the input
 * object's slot 0x88 is unprojected with the camera's matrices (view +0x88, projection +0xC8, viewport +0x22C,
 * world 0x006C8478, 0x005B80F2) and handed to the object at +0xC0 (0x004258C0).  The highlight of the previous
 * nearest object (+0x80 vector, 8-byte {distance, object} entries, end at +0x88) is cleared (0x00591B80) and the
 * vector emptied; every object of the list at +0x48 whose type (+0x354) is 2 when the tool's own (+0x68 +0x354) is 1
 * (or 1 otherwise) is tested under the cursor in screen space (0x00591640, the tool's type in EAX) and pushed with
 * distance 0.  If anything was pushed, the two reference points (0x005AD280) and every object's distance
 * (0x0058EBE0, a float) fill the vector, which is sorted (0x005B2E50) and whose nearest entry is activated
 * (0x00591AF0); the tool's own stream (+0x68) is activated last.  The original's element-copy loop before the list
 * walk never runs (its source and destination start equal), so only the end pointer is rewound. */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef float *(__thiscall *cursor_5B37D0)(void *self);
typedef struct { float dist; void *obj; } Entry_5B37D0;

DECOMP_C char d_006C8478[];
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C void *__cdecl sub_00424E70(void);
DECOMP_C void *__stdcall sub_005B80F2(void *out, void *v, void *viewport, void *proj, void *view, void *world);
DECOMP_C int __thiscall sub_004258C0(void *self, unsigned int x, unsigned int y, unsigned int z);
DECOMP_C void __thiscall sub_00591B80(void *self, int resume);
DECOMP_C unsigned char __cdecl sub_00591640(void *self, unsigned int eax, void *pt);
DECOMP_C void __thiscall sub_0043E2D0(void *self, void *pair);
DECOMP_C void __stdcall sub_005AD280(void *out1, void *out2);
DECOMP_C float __thiscall sub_0058EBE0(void *self, void *a, void *b);
DECOMP_C void __cdecl sub_005B2E50(void *begin, void *end, unsigned int count);
DECOMP_C void *__thiscall sub_00591AF0(void *self, int start);

DECOMP(005B37D0)
void __thiscall f_005B37D0(void *this)
{
    char *c = (char *)this, *vec = c + 0x80;
    Entry_5B37D0 **begin = (Entry_5B37D0 **)(vec + 4), **end = (Entry_5B37D0 **)(vec + 8);
    void *input = sub_00421680(), *camera;
    float *cursor = ((cursor_5B37D0)(*(void ***)input)[0x88 / 4])(input);
    float mx = cursor[0], my = cursor[1], world[3];
    char *head = *(char **)(c + 0x48), *node;

    camera = sub_00424E70();
    world[0] = mx;
    world[1] = my;
    world[2] = 0.0f;
    sub_005B80F2(world, world, camera + 0x22c, camera + 0xc8, camera + 0x88, d_006C8478);
    sub_004258C0(*(void **)(c + 0xc0), *(unsigned int *)(world + 0), *(unsigned int *)(world + 1),
                 *(unsigned int *)(world + 2));
    if (*begin && (char *)*end - (char *)*begin >= 8)
        sub_00591B80((*end - 1)->obj, 0);
    *end = *begin;
    for (node = *(char **)head; node != head; node = *(char **)node) {
        unsigned int mode = *(unsigned int *)(*(char **)(c + 0x68) + 0x354);
        char *obj = *(char **)(node + 8);
        if (mode == 1 ? *(unsigned int *)(obj + 0x354) == 2 : *(unsigned int *)(obj + 0x354) == 1) {
            float pt[3];
            pt[0] = mx;
            pt[1] = my;
            pt[2] = 0.0f;
            if (sub_00591640(obj, mode, pt)) {
                Entry_5B37D0 e;
                e.dist = 0.0f;
                e.obj = obj;
                sub_0043E2D0(vec, &e);
            }
        }
    }
    if (*begin && (char *)*end - (char *)*begin >= 8) {
        float a[3], b[3];
        Entry_5B37D0 *e;
        sub_005AD280(a, b);
        for (e = *begin; e != *end; e++)
            e->dist = sub_0058EBE0(e->obj, a, b);
        sub_005B2E50(*begin, *end, (unsigned int)((char *)*end - (char *)*begin) >> 3);
        sub_00591AF0((*end - 1)->obj, 0);
    }
    sub_00591AF0(*(void **)(c + 0x68), 0);
}
