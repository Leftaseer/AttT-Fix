/* 0x00490530: set the bit count of a bitset, growing or shrinking it.
 * The original keeps bit positions as an 8-byte {word pointer, bit offset} iterator that 0048B330 advances
 * by a signed bit count.  Ghidra typed both temporaries as one-byte locals, so the generated code advanced
 * uninitialised stack bytes and passed the raw {this[8], 0} pair instead of the advanced one:
 *   grow:  iter = {data, 0}; advance(iter, this->size); 0048F9D0(this, iter, new - old, param_2)
 *   shrink: end = {data, 0}; advance(end, this->size); iter = {data, 0}; advance(iter, new);
 *          0048D9D0(this, &iter, iter, end)
 * (0048D9D0 has ret 0x14 and reads all five arguments, including the end iterator in arg4/arg5.) */
#include "auto_pre.h"
/* @func 00490530 */
DECOMP_C undefined4 __thiscall sub_0048B330(void *p0, int p1);
DECOMP_C undefined4 __thiscall sub_0048D9D0(void *p0, int *p1, uint *p2, uint p3, uint *p4, uint p5);
DECOMP_C undefined4 __thiscall sub_0048F9D0(void *p0, uint *p1, uint p2, uint p3, undefined4 p4);

typedef struct { uint *ptr; int off; } bit_iter;

DECOMP(00490530)
void __thiscall f_00490530(void *this, uint param_1, undefined4 param_2)
{
  uint old = *(uint *)this;
  uint *data = *(uint **)((int)this + 8);
  bit_iter it, end;

  if (old < param_1) {
    it.ptr = data;
    it.off = 0;
    if (old != 0) {
      sub_0048B330(&it, (int)old);
    }
    sub_0048F9D0(this, it.ptr, (uint)it.off, param_1 - old, param_2);
    return;
  }
  if (param_1 < old) {
    end.ptr = data;
    end.off = 0;
    if (old != 0) {
      sub_0048B330(&end, (int)old);
    }
    it.ptr = data;
    it.off = 0;
    sub_0048B330(&it, (int)param_1);
    sub_0048D9D0(this, (int *)&it, it.ptr, (uint)it.off, end.ptr, (uint)end.off);
  }
}
