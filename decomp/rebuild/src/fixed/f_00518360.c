#include "auto_pre.h"
DECOMP(00518360)
uint __stdcall f_00518360(char param_1)
{
  int idx = (int)param_1 - 0x61;
  if ((unsigned)idx > 0x19) {
    return (uint)idx & 0xFFFFFF00u;
  }
  switch(param_1) {
  case 'a':
    return 0x1e;
  case 'd':
    return 0x20;
  case 'q':
    return 0x10;
  case 's':
    return 0x1f;
  case 't':
    return 0x14;
  case 'w':
    return 0x11;
  case 'z':
    return 0x2c;
  default:
    return 0;
  }
}
