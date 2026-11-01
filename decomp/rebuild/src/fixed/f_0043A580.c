/* 0x0043A580: packs (days, hours, minutes, seconds, ms) into milliseconds; the x87 code accumulates
 * seconds, minutes, hours, then days, which the decompiler emitted in the reverse order (1 ulp apart) */
#include "auto_pre.h"

DECOMP_C char d_00607EB8[], d_00609E10[], d_00609E18[], d_0068AE10[];

DECOMP(0043A580)
double __cdecl f_0043A580(int param_1, int param_2, undefined4 param_3, int param_4, int param_5, int param_6, int param_7)
{
    double days = (double)(unsigned)param_1;
    double hours = (double)(unsigned)param_4;
    double minutes = (double)(unsigned)param_5;
    double seconds = (double)(unsigned)param_6;
    double millis = (double)(unsigned)param_7;
    double r;

    r = seconds * *(double *)d_0068AE10 + millis;
    r = r + minutes * *(double *)d_00607EB8 * *(double *)d_0068AE10;
    r = r + hours * *(double *)d_00607EB8 * *(double *)d_00607EB8 * *(double *)d_0068AE10;
    r = r + days * *(double *)d_00609E10 * *(double *)d_00607EB8 * *(double *)d_00607EB8 * *(double *)d_0068AE10;
    return r;
}
