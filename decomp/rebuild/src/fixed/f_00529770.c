/* 0x00529770: updates the world map's cell geometry and hover state (ECX, no arguments).  When the active
 * object's test (0x004D9A40, ECX = [this+0x1E4]) reports 1, the map's vertex copy is refreshed: the buffer
 * chosen between +0x208 and +0x20C (the one not already current at +0x210) is locked (vtable +0x2C, whole
 * buffer), the 0x20-byte records between +0x1EC and +0x1F0 (rounded down to a whole record) are copied into it
 * and it is unlocked (vtable +0x30); the row table (+0x2C4) takes the active object's copy from +0x50 and its
 * record count goes to +0x1C8.  The hovered cell is then derived from the camera (+0x44/+0x4C) and the cell
 * object ([[this+0x218]+8], its origin +0x70/+0x78 and size +0x5C/+0x60): x = ftol((camera.x - origin.x) /
 * width), y = ftol((origin.y - camera.y) / height).  Three passes walk the row table (+0x2C8/+0x2CC, 0x10-byte
 * rows whose +4/+8 point at 0x10-byte cells; each cell's +4/+8 point at 6-byte items) and keep the cells the
 * map object's visibility test (0x00528A40) accepts: the first sums every item count and locks that many items
 * (6 bytes each) of the mesh buffer at +0x214; the second copies the cells within one cell of the hover (both
 * coordinates at most 1 away); after +0x1D0 = +0x1CC, the third copies the remaining cells (either coordinate
 * more than 1 away); both copying passes append the items to the locked buffer and add their count to +0x1CC.  The mesh buffer is unlocked last.  The float-to-int
 * conversions go through the 64-bit _ftol2 (0x005E3FA0), hence the long long casts. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP_C int __thiscall sub_004D9A40(void *self);
DECOMP_C void __thiscall sub_00529520(void *self, void *src);
DECOMP_C unsigned char __thiscall sub_00528A40(void *self, int row, int col);
DECOMP_C void __cdecl sub_005E4232(void *dst, const void *src, unsigned int len);
DECOMP_C void *__cdecl sub_00424E70(void);

typedef unsigned int (__stdcall *lock_529770)(void *buf, unsigned int off, unsigned int len, void **data,
                                              unsigned int flags);
typedef unsigned int (__stdcall *unlock_529770)(void *buf);

/* rows of the row table at +0x2C8 / +0x2CC (a null table has none) */
#define ROWS(c) (*(unsigned char **)((c) + 0x2c8) ? \
                 (int)(*(unsigned char **)((c) + 0x2cc) - *(unsigned char **)((c) + 0x2c8)) >> 4 : 0)
/* 6-byte item count of cell `col` in the 0x10-byte cells at `cells` (its +4/+8 bound the items) */
static float abs_529770(float v)
{
    return v < 0.0f ? -v : v;
}

#define ITEMS(cells, col) (*(unsigned char **)((cells) + (col) * 0x10 + 4) ? \
                           (int)(*(unsigned char **)((cells) + (col) * 0x10 + 8) - \
                                 *(unsigned char **)((cells) + (col) * 0x10 + 4)) / 6 : 0)

DECOMP(00529770)
void __thiscall f_00529770(void *this)
{
    char *c = (char *)this, *dst;
    int x, y;

    if (sub_004D9A40(*(void **)(c + 0x1e4)) == 1) {
        void *buf = *(void **)(c + 0x208), *data;
        unsigned int size = (unsigned int)(*(char **)(c + 0x1f0) - *(char **)(c + 0x1ec));
        if (*(void **)(c + 0x210) == buf)
            buf = *(void **)(c + 0x20c);
        *(void **)(c + 0x210) = buf;
        ((lock_529770)(*(void ***)buf)[0x2c / 4])(buf, 0, 0, &data, 0x2000);
        sub_005E4232(data, *(void **)(c + 0x1ec), (size >> 5) << 5);
        ((unlock_529770)(*(void ***)buf)[0x30 / 4])(buf);
        sub_00529520(c + 0x2c4, (char *)*(void **)(c + 0x1e4) + 0x50);
        *(unsigned int *)(c + 0x1c8) = (unsigned int)(*(char **)(c + 0x1f0) - *(char **)(c + 0x1ec)) >> 5;
    }

    {
        char *camera = sub_00424E70();
        char *o = *(char **)(*(char **)(c + 0x218) + 8);
        x = (int)(long long)((*(float *)(camera + 0x44) - *(float *)(o + 0x70)) / *(float *)(o + 0x5c));
        y = (int)(long long)((*(float *)(o + 0x78) - *(float *)(camera + 0x4c)) / *(float *)(o + 0x60));
    }

    {
        int total = 0, r;

        for (r = 0; r < ROWS(c); r++) {
            int b;
            for (b = 0;; b++) {
                unsigned char *row = *(unsigned char **)(c + 0x2c8) + r * 0x10;
                unsigned char *cells = *(unsigned char **)(row + 4), *end = *(unsigned char **)(row + 8);
                if (!cells || b >= (int)(end - cells) >> 4)
                    break;
                if (!sub_00528A40(*(void **)(*(char **)(c + 0x218) + 8), r, b))
                    continue;
                row = *(unsigned char **)(c + 0x2c8) + r * 0x10;
                total += ITEMS(*(unsigned char **)(row + 4), b);
            }
        }

        {
            void *vb = *(void **)(c + 0x214);
            void *data;
            ((lock_529770)(*(void ***)vb)[0x2c / 4])(vb, 0, (unsigned int)(6 * total), &data, 0x2000);
            *(int *)(c + 0x1cc) = 0;
            dst = (char *)data;

            for (r = 0; r < ROWS(c); r++) {
                int b;
                for (b = 0;; b++) {
                    unsigned char *row = *(unsigned char **)(c + 0x2c8) + r * 0x10;
                    unsigned char *cells = *(unsigned char **)(row + 4), *end = *(unsigned char **)(row + 8);
                    unsigned char *item;
                    int n;
                    if (!cells || b >= (int)(end - cells) >> 4)
                        break;
                    if (!sub_00528A40(*(void **)(*(char **)(c + 0x218) + 8), r, b))
                        continue;
                    if (abs_529770((float)r - (float)x) > 1.0f)
                        continue;
                    if (abs_529770((float)b - (float)y) > 1.0f)
                        continue;
                    row = *(unsigned char **)(c + 0x2c8) + r * 0x10;
                    cells = *(unsigned char **)(row + 4);
                    item = cells + b * 0x10;
                    n = ITEMS(cells, b);
                    sub_005E4232(dst, *(void **)(item + 4), (unsigned int)(6 * n));
                    dst += 6 * n;
                    *(int *)(c + 0x1cc) += n;
                }
            }

            *(int *)(c + 0x1d0) = *(int *)(c + 0x1cc);

            for (r = 0; r < ROWS(c); r++) {
                int b;
                for (b = 0;; b++) {
                    unsigned char *row = *(unsigned char **)(c + 0x2c8) + r * 0x10;
                    unsigned char *cells = *(unsigned char **)(row + 4), *end = *(unsigned char **)(row + 8);
                    unsigned char *item;
                    int n;
                    float dr;
                    if (!cells || b >= (int)(end - cells) >> 4)
                        break;
                    if (!sub_00528A40(*(void **)(*(char **)(c + 0x218) + 8), r, b))
                        continue;
                    dr = abs_529770((float)r - (float)x);
                    if (!(dr > 1.0f) && !(abs_529770((float)b - (float)y) > 1.0f))
                        continue;
                    row = *(unsigned char **)(c + 0x2c8) + r * 0x10;
                    cells = *(unsigned char **)(row + 4);
                    item = cells + b * 0x10;
                    n = ITEMS(cells, b);
                    sub_005E4232(dst, *(void **)(item + 4), (unsigned int)(6 * n));
                    dst += 6 * n;
                    *(int *)(c + 0x1cc) += n;
                }
            }

            ((unlock_529770)(*(void ***)vb)[0x30 / 4])(vb);
        }
    }
}
