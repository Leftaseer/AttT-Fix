/* CDelCom: the DatFile text reader and its lifetime (0x444AD0 / 0x444B40 / 0x444BA0 / 0x444BD0 / 0x445630). */
#include "game/common.h"
#include "game/delcom.h"

ORIG_DATA(0060A4BC); /* CDelCom::vftable */
ORIG_DATA(006C8974); /* the text ends with a pending space */
ORIG_DATA(006C0036); /* the text ends with a pending newline */
ORIG_DATA(0060A5B8); /* " don't be open" */
ORIG_DATA(0060A5A8); /* ".\\DatFile.cpp" */
ORIG_DATA(0060A58C); /* "Comment(//) is not ended" */
ORIG_DATA(0060A570); /* "Comment( slash-star ) is not ended" */
ORIG_DATA(0069916C); /* CGameException _ThrowInfo */

extern "C" __declspec(dllimport) int __cdecl msvc_tolower(int c) __asm__("_tolower");

static void ThrowDatError(const std::string &msg, int line)
{
    CGameException e(msg, ORIG_STR(0060A5A8), line);
    _CxxThrowException(&e, d_0069916C);
    __builtin_unreachable();
}

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

/* A character of the text: runs of spaces collapse to one and a newline right after a space replaces it.  The
 * separators ',' ';' and tabs reach here as a space and the other characters lower-cased (see ReadFile). */
DECOMP(00444BD0)
void CDelCom::PutChar(char c)
{
    char &afterSpace = ORIG_VAR(006C8974, char);
    char &afterNewline = ORIG_VAR(006C0036, char);

    if (c == ' ') {
        if (afterSpace || afterNewline)
            return;
        afterSpace = 1;
        afterNewline = 0;
    } else if (c == '\n') {
        if (afterSpace) {
            afterSpace = 0;
            afterNewline = 1;
            text.erase(text.size() - 1, 1);
        } else {
            if (afterNewline)
                return;
            afterNewline = 1;
        }
    } else {
        afterSpace = 0;
        afterNewline = 0;
    }
    text += c;
}

/* Reads the whole file into text, which becomes its normalised contents: ',' ';' and tabs become one space,
 * characters are lower-cased, line comments run to the line end and block comments are dropped whole (an
 * unfinished one throws); the text ends with a line break and a NUL.  Throws if the file cannot be opened.
 * Returns a copy of the text. */
DECOMP(00445630)
std::string CDelCom::ReadFile(const std::string &name)
{
    char &afterSpace = ORIG_VAR(006C8974, char);
    char &afterNewline = ORIG_VAR(006C0036, char);
    enum { Normal, Slash, LineComment, BlockComment, BlockStar } state = Normal;

    file.open(name.c_str(), std::ios_base::_In, std::ios_base::_Openprot);
    if (file.fail())
        ThrowDatError(name + ORIG_STR(0060A5B8), 0x1C);

    /* a separator only adds a space when the text does not already end with one (or with a line break) */
    auto addSpace = [&] {
        if (!afterSpace && !afterNewline) {
            afterSpace = 1;
            afterNewline = 0;
            text += ' ';
        }
    };

    ReadChar();
    for (;;) {
        switch (state) {
        case Normal:
            if (!ch)
                goto finished;
            if (ch == ',' || ch == ';' || ch == '\t') {
                addSpace();
                ReadChar();
            } else if (ch == '/') {
                ReadChar();
                state = Slash;
            } else {
                PutChar((char)msvc_tolower(ch));
                ReadChar();
            }
            break;
        case Slash:
            if (ch == '/') {
                addSpace();
                ReadChar();
                state = LineComment;
            } else if (ch == '*') {
                addSpace();
                ReadChar();
                state = BlockComment;
            } else {
                if (!ch)
                    ThrowDatError(ORIG_STR(0060A58C), 0x51);
                afterNewline = 0;
                afterSpace = 0;
                text += '/';
                state = Normal;
            }
            break;
        case LineComment:
            if (!ch || ch == '\n')
                state = Normal;
            else
                ReadChar();
            break;
        case BlockComment:
            if (!ch)
                ThrowDatError(ORIG_STR(0060A570), 0x68);
            ReadChar();
            if (ch == '*')
                state = BlockStar;
            break;
        case BlockStar:
            if (!ch)
                ThrowDatError(ORIG_STR(0060A570), 0x79);
            ReadChar();
            state = ch == '/' ? Normal : BlockComment;
            break;
        }
    }
finished:
    if (afterSpace) {
        afterSpace = 0;
        afterNewline = 1;
        text.erase(text.size() - 1, 1);
        text += '\n';
    } else if (!afterNewline) {
        afterNewline = 1;
        text += '\n';
    }
    afterNewline = 0;
    afterSpace = 0;
    text += '\0';
    file.close();
    return text;
}
