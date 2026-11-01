/* 0x00547760: squared 2D distance from param_1 (x at +0, y at +8) to this+0x68 / this+0x6c.  MSVC rounds both
 * differences and both squares to float (fstp dword) and only then adds them in extended precision; the
 * generated expression kept the squares in x87 registers, which moves the result by 1 ulp. */
#include "auto_pre.h"
/* @func 00547760 */

DECOMP(00547760)
float __thiscall f_00547760(void *this, float *param_1)
{
  volatile float dx = param_1[0] - *(float *)((int)this + 0x68);
  volatile float dy = param_1[2] - *(float *)((int)this + 0x6c);
  volatile float sx = dx * dx;
  volatile float sy = dy * dy;
  { volatile float gh_ret = sx + sy; return gh_ret; }
}
