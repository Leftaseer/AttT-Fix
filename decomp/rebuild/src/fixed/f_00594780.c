/* 0x00594780: CDXUTDialog::OnCycleFocus(forward): from the focused control (0x8D1244) of this dialog, the next (or
 * previous: 0x00594640 / 0x00594690) control of an enabled dialog (+0x59 of its dialog +0x18) that can take the focus
 * (vf1C) gets it (vf24 OnFocusOut of the old, vf20 OnFocusIn of the new); at most 0xFFFF steps; EAX comes back as it
 * came when nothing changes */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 00594780 custom */
DECOMP_C void *__cdecl sub_00594640(void *control);
DECOMP_C void *__cdecl sub_00594690(void *control);
DECOMP_C char d_008D1244[];
typedef unsigned int (__thiscall *vf_594780)(void *self);

#define FOCUS (*(char **)d_008D1244)

DECOMP(00594780)
unsigned int __cdecl f_00594780(void *this, unsigned int eax, char forward)
{
    char *start = FOCUS, *c;
    int i;
    if (!start || *(void **)(start + 0x18) != this)
        return eax;
    c = start;
    for (i = 0; i < 0xffff; i++) {
        c = forward ? sub_00594640(c) : sub_00594690(c);
        eax = (unsigned int)c;
        if (c == start)
            return eax;
        if (*(*(char **)(c + 0x18) + 0x59)) {
            eax = ((vf_594780)(*(void ***)c)[0x1c / 4])(c);
            if ((char)eax) {
                ((vf_594780)(*(void ***)FOCUS)[0x24 / 4])(FOCUS);
                FOCUS = c;
                return ((vf_594780)(*(void ***)c)[0x20 / 4])(c);
            }
            start = FOCUS;
        }
    }
    return eax;
}
