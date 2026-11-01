#include "auto_pre.h"
DECOMP(004DD0C0)
uint __stdcall f_004DD0C0(char param_1)
{
  int idx = (int)param_1 - 0x41;
  if ((unsigned)idx > 0x19) {
    return (uint)idx & 0xFFFFFF00u;
  }
  switch(param_1) {
  case 'A':
    return 0x1e;
  case 'D':
    return 0x20;
  case 'Q':
    return 0x10;
  case 'S':
    return 0x1f;
  case 'T':
    return 0x14;
  case 'W':
    return 0x11;
  case 'Z':
    return 0x2c;
  default:
    return 0;
  }
}
