/* 0x0048D9D0: erase [it, end) from a bitset by copying the tail down over it, then trimming.
 * The original recomputes the bitset's end iterator as an 8-byte {word pointer, bit offset} temp:
 * advance({data, 0}, this->count).  Ghidra typed that temp as one byte, so the generated code advanced
 * uninitialised stack memory and then passed the raw {data, 0} pair to 0048CFD0 as the source end.  The
 * bit-copy loop (0048C840) then walks forward from the real end towards the raw start forever.
 * The copy writes its resulting destination iterator back through arg1 (the caller's own it pair), and
 * 0048CF60 trims the bitset to that position; the returned iterator (arg1) is rebuilt at the original it
 * bit index. */
#include "auto_pre.h"
/* @func 0048D9D0 */
DECOMP_C undefined4 __thiscall sub_0048B330(void *p0, int p1);
DECOMP_C undefined4 __thiscall sub_0048CF60(void *p0, uint p1);
DECOMP_C undefined4 *__cdecl sub_0048CFD0(undefined4 *p0, uint *p1, uint p2, uint *p3, uint p4, uint *p5, uint p6);

typedef struct { uint *ptr; int off; } bit_iter;

DECOMP(0048D9D0)
void __thiscall f_0048D9D0(void *this, int *out, uint *it_ptr, uint it_off, uint *end_ptr, uint end_off)
{
  uint *data = *(uint **)((int)this + 8);
  uint count = *(uint *)this;
  int it_bits, bits;
  bit_iter it, end, pos;

  it.ptr = it_ptr;
  it.off = (int)it_off;
  it_bits = (((int)it_ptr - (int)data) >> 2) * 0x20 + (int)it_off;
  end.ptr = data;
  end.off = 0;
  if (count != 0) {
    sub_0048B330(&end, (int)count);
  }
  sub_0048CFD0((undefined4 *)&it, end_ptr, end_off, end.ptr, (uint)end.off, it.ptr, (uint)it.off);
  bits = (((int)it.ptr - (int)data) >> 2) * 0x20 + it.off;
  sub_0048CF60(this, (uint)bits);
  pos.ptr = data;
  pos.off = 0;
  sub_0048B330(&pos, it_bits);
  ((bit_iter *)out)->ptr = pos.ptr;
  ((bit_iter *)out)->off = pos.off;
}
