/* CDelCom: the DatFile text reader and its lifetime (0x444AD0 / 0x444B40 / 0x444BA0). */
#include "game/common.h"
#include "game/delcom.h"

ORIG_DATA(0060A4BC); /* CDelCom::vftable */

DECOMP(00444AD0)
CDelCom::CDelCom() : file(), text()
{
    vftable = d_0060A4BC;
    text = "";
    ch = 0;
}

/* text and file are destroyed by the compiler-generated part after the body, in that order, as in the original */
DECOMP(00444B40)
CDelCom::~CDelCom()
{
    vftable = d_0060A4BC;
}

/* a failed read (including the end of the file) leaves the character 0; returns that failure */
DECOMP(00444BA0)
bool CDelCom::ReadChar()
{
    file.read(&ch, 1);
    bool failed = file.fail();
    if (failed)
        ch = 0;
    return failed;
}
