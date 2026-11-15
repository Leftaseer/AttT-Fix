/* 0x0042EEF0: the crash-dump dialog: the ATThrone__<day>_<month>_<year>__<hour>_<minute>_<second>_exp.dmp
 * name from the local time, a notice box, 0x0047C4F0(2, name) writing the dump and a second box reporting the
 * outcome; 0x006C88AD marks the dialog as up */
/* @conv EBX,EDI 0 */
/* @func 0042EEF0 custom */
#include "auto_pre.h"
typedef struct {
    unsigned short year, month, day_of_week, day, hour, minute, second, milliseconds;
} _SYSTEMTIME_42EEF0;

DECOMP_C void (__stdcall *imp_00607154)(_SYSTEMTIME_42EEF0 *st) __asm__("__imp__GetLocalTime");
DECOMP_C int (__stdcall *imp_006076C8)(void *hwnd, const char *text, const char *caption, unsigned int type)
    __asm__("__imp__MessageBoxA");
DECOMP_C void *(__stdcall *imp_006076AC)(void *hwnd) __asm__("__imp__SetActiveWindow");
DECOMP_C unsigned int __cdecl sub_0042EEC0(char *dst, unsigned int size, const char *format, ...);
typedef unsigned int (__cdecl *writer_42EEF0)(int mode, const char *file);
DECOMP_C void *d_006C889C;                                             /* the window the boxes are owned by */
DECOMP_C unsigned char d_006C88AD;                                     /* set while the dialog is up */
DECOMP_C char d_00608CEC[], d_00608CF4[], d_00608D1C[], d_00608D38[], d_00608D54[], d_00608D74[],
    d_00608D80[];

DECOMP(0042EEF0)
void __cdecl f_0042EEF0(unsigned int ebx, unsigned int edi)
{
    char name[260];
    char text[1024];
    _SYSTEMTIME_42EEF0 st;

    imp_00607154(&st);
    sub_0042EEC0(name, 0x104, d_00608D80, st.day, st.month, st.year, st.hour, st.minute, st.second);
    d_006C88AD = 1;
    imp_006076C8(d_006C889C, d_00608D54, d_00608D74, 0x40);
    /* 0x0047C4F0 takes two stack arguments; the registers the convention file lists hold the caller's leftovers */
    if (((writer_42EEF0)0x0047C4F0)(2, name) == 0) {
        sub_0042EEC0(text, 0x400, d_00608CF4, d_00608D38);
        imp_006076C8(d_006C889C, text, d_00608CEC, 0x40);
    } else {
        sub_0042EEC0(text, 0x400, d_00608CF4, d_00608D1C);
        imp_006076C8(d_006C889C, text, d_00608D74, 0x10);
    }
    imp_006076AC(d_006C889C);
    d_006C88AD = 0;
    (void)ebx;
    (void)edi;
}
