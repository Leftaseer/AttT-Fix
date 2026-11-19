/* 0x0048AFB0: compacts the 16-bit index ranges at +0x38 (count +0x3C) into maximal runs, merging
 * a range into the previous one when it starts at or before that range's end (+0x40/+0x44).  The
 * selected index runs are then copied from the source array into a buffer obtained through vf2C
 * with an accumulated count, and the buffer is released through vf30.  The range count and +0x46
 * are cleared and the copied index count is returned through out_count. */
/* @conv ECX 12 */
#include "auto_pre.h"

typedef struct {
    unsigned int start;
    unsigned int end;
} Range_48AFB0;

typedef struct {
    char pad[0x38];
    Range_48AFB0 *ranges;           /* +0x38 */
    unsigned short count;           /* +0x3c */
    unsigned short pad3e;
    Range_48AFB0 *merged;           /* +0x40 */
    unsigned short merged_count;    /* +0x44 */
    unsigned char flag;             /* +0x46 */
} Ranges_48AFB0;

typedef long (__stdcall *lock_48AFB0)(void *self, unsigned int off, unsigned int size, void **data,
                                      unsigned int fl);
typedef long (__stdcall *release_48AFB0)(void *self);

DECOMP_C void *__cdecl sub_005E4232(void *dst, const void *src, unsigned int n);      /* memcpy */

DECOMP(0048AFB0)
void __thiscall f_0048AFB0(Ranges_48AFB0 *this, void *buffer_obj, const unsigned short *indices,
                           unsigned int *out_count)
{
    unsigned int i = 0, j;
    void *data;

    this->merged_count = 0;
    if (this->count) {
        if (this->count > 1) {
            for (;;) {
                unsigned int first = this->ranges[i].start;
                while (i < this->count - 1 && this->ranges[i].end >= this->ranges[i + 1].start)
                    i++;
                this->merged[this->merged_count].start = first;
                this->merged[this->merged_count].end = this->ranges[i].end;
                this->merged_count++;
                i++;
                if (i >= this->count - 1)
                    break;
            }
        }
        if (i == this->count - 1) {
            this->merged[this->merged_count] = this->ranges[i];
            this->merged_count++;
        }
    }
    this->count = 0;
    this->flag = 0;
    *out_count = 0;
    data = 0;
    ((lock_48AFB0)(*(void ***)buffer_obj)[0x2c / 4])(buffer_obj, 0, 0, &data, 0);
    for (j = 0; j < this->merged_count; j++) {
        const Range_48AFB0 *r = &this->merged[j];
        unsigned int n = r->end - r->start;
        sub_005E4232((char *)data + *out_count * 2, indices + r->start, n * 2);
        *out_count += n;
    }
    ((release_48AFB0)(*(void ***)buffer_obj)[0x30 / 4])(buffer_obj);
}
