/* 0x004EF580: plays a 3D sound for a unit (arg 2) heard by another (arg 1), when within the range (+0xE0, squared)
 * of the camera (0x00424E70): looks up arg 1's sound set (vfC0) in the map at +0xA8 (0x00422D80, find) and in that
 * the sound named by arg 2 (vfC4); a new Sound3D (0x6C bytes, 0x004C4BC0) on the entry's file (0x004ED4F0) with the
 * entry's two distances (0x004C1B10), at arg 2's position (vf68, 0x004C2E10), the volume +0xB0 (vf18), played (vf0C)
 * and appended to the list at +0x48 (0x005AD6C0, 0x004E0EF0) (the original frees nothing if one throws) */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void __thiscall sub_00422D80(void *map, char **out, void *key);
DECOMP_C void *__thiscall sub_004ED4F0(void *entry);
DECOMP_C void *__thiscall sub_004C4BC0(void *self, void *file);
DECOMP_C void __thiscall sub_004C1B10(void *self, float a, float b, int c);
DECOMP_C void __thiscall sub_004C2E10(void *self, void *pos, int a);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
typedef void *(__thiscall *vf_4EF580)(void *self);
typedef void (__thiscall *vfv_4EF580)(void *self, float v, int a);
typedef void (__thiscall *vfp_4EF580)(void *self, int a, int b);

DECOMP(004EF580)
void __thiscall f_004EF580(void *this, void *hearer, void *unit)
{
    char *s = (char *)this;
    unsigned int pos[3];
    unsigned int *p;
    char *cam, *map, *node, **head, **nn;
    void *key1, *key2;
    float dx, dy, dz, d;
    float *e;
    void **snd;
    p = (unsigned int *)((vf_4EF580)(*(void ***)unit)[0x68 / 4])(unit);
    pos[0] = p[0];
    pos[1] = p[1];
    pos[2] = p[2];
    cam = sub_00424E70();
    dx = *(float *)&pos[0] - *(float *)(cam + 0x44);
    dy = *(float *)&pos[1] - *(float *)(cam + 0x48);
    dz = *(float *)&pos[2] - *(float *)(cam + 0x4c);
    d = dx * dx + dy * dy + dz * dz;
    if (d > *(float *)(s + 0xe0))
        return;
    key2 = ((vf_4EF580)(*(void ***)unit)[0xc4 / 4])(unit);
    key1 = ((vf_4EF580)(*(void ***)hearer)[0xc0 / 4])(hearer);
    map = *(char **)(s + 0xa8);
    sub_00422D80(map, &node, key1);
    if (node == *(char **)(map + 8))
        return;
    map = node + 0x24;
    sub_00422D80(map, &node, key2);
    if (node == *(char **)(map + 8))
        return;
    e = (float *)(node + 0x24);
    if (!e)
        return;
    snd = (void **)sub_005E3EAE(0x6c);
    if (snd)
        snd = (void **)sub_004C4BC0(snd, sub_004ED4F0(e));
    sub_004C1B10(snd, e[0], e[1], 0);
    sub_004C2E10(snd, pos, 0);
    ((vfv_4EF580)(*(void ***)snd)[0x18 / 4])(snd, *(float *)(s + 0xb0), 0);
    ((vfp_4EF580)(*(void ***)snd)[0xc / 4])(snd, 1, 0);
    head = *(char ***)(s + 0x4c);
    nn = sub_005AD6C0(head, (char **)head[1], &snd);
    sub_004E0EF0(s + 0x48, 1);
    head[1] = (char *)nn;
    *(char ***)nn[1] = nn;
}
