/* The dat-file scanner: flex 2.5's yylex (0x470410) with the input machinery the skeleton generates.  The
 * original reads through CGameFile (the custom fread 0x493140) instead of stdio, so the loaders open the file
 * with CGameFile::Open(name, 1), set 0x6CA278 to its size and let the scanner pull it in. */
#include <stdint.h>
#include "game/common.h"
#include "game/datlexer.h"
#include "game/gamefile.h"

/* the flex tables: yy_accept (short), yy_ec / yy_meta (a byte every four), yy_base / yy_def / yy_nxt / yy_chk
 * (short).  They are read-only data of the original. */
ORIG_DATA(0060CCF0); /* yy_accept */
ORIG_DATA(0060D078); /* yy_ec */
ORIG_DATA(0060D478); /* yy_meta */
ORIG_DATA(0060D518); /* yy_base */
ORIG_DATA(0060D8A8); /* yy_def */
ORIG_DATA(0060DC38); /* yy_nxt */
ORIG_DATA(0060E038); /* yy_chk */

/* the scanner globals */
ORIG_DATA(006C0F94); /* first-call initialisation flag */
ORIG_DATA(006C9060); /* the number of the last number token (a float) */
ORIG_DATA(006C9064); /* the start of the last token's text */
ORIG_DATA(006C9068); /* the text buffer of the word tokens (0x1000 bytes) */
ORIG_DATA(006CA068); /* the end of the last accepting match */
ORIG_DATA(006CA06C); /* the state of the last accepting match */
ORIG_DATA(006CA070); /* a buffer switch happened on end of file */
ORIG_DATA(006CA074); /* the length of the last token */
ORIG_DATA(006CA078); /* characters in the buffer */
ORIG_DATA(006CA07C); /* the character replaced by the end-of-token NUL */
ORIG_DATA(006CA080); /* the current buffer */
ORIG_DATA(006CA084); /* the current position in the buffer */
ORIG_DATA(006CA088); /* the start state (1) */
ORIG_DATA(006CA08C); /* yyin */
ORIG_DATA(006CA090); /* yyout */
ORIG_DATA(006CA278); /* bytes of the game file the scanner has not read */
ORIG_DATA(006CA280); /* the CGameFile the scanner reads */

/* messages and the fprintf format of the original */
ORIG_DATA(0060E438); /* "%s\n" */
ORIG_DATA(0060E4B4); /* out of dynamic memory in yy_create_buffer() */
ORIG_DATA(0060E4E0); /* fatal error - scanner input buffer overflow */
ORIG_DATA(0060E50C); /* fatal flex scanner internal error--end of buffer missed */
ORIG_DATA(0060E544); /* unexpected last match in yyinput() */
ORIG_DATA(0060E568); /* ERROR! */
ORIG_DATA(0060E570); /* fatal flex scanner internal error--no action found */

extern "C" __declspec(dllimport) void *__cdecl malloc(size_t size);
extern "C" __declspec(dllimport) void *__cdecl realloc(void *p, size_t size);
extern "C" __declspec(dllimport) double __cdecl atof(const char *s);
extern "C" __declspec(dllimport) void __cdecl exit(int code);
extern "C" __declspec(dllimport) int __cdecl printf(const char *format, ...);
extern "C" __declspec(dllimport) int __cdecl fprintf(FILE *f, const char *format, ...);
extern "C" __declspec(dllimport) FILE *__cdecl __iob_func(void);
extern "C" __declspec(dllimport) int __cdecl _fileno(FILE *f);
extern "C" __declspec(dllimport) int __cdecl _isatty(int fd);
extern "C" __declspec(dllimport) int __cdecl isalpha(int c);
extern "C" __declspec(dllimport) int __cdecl tolower(int c);

#define YY_ACCEPT ((const short *)d_0060CCF0)
#define YY_BASE ((const short *)d_0060D518)
#define YY_DEF ((const short *)d_0060D8A8)
#define YY_NXT ((const short *)d_0060DC38)
#define YY_CHK ((const short *)d_0060E038)
#define YY_JAMSTATE 0x1d9

/* yy_ec and yy_meta keep one class byte every four */
static inline unsigned char TableByte(const char *table, unsigned index)
{
    return ((const unsigned char *)table)[index * 4];
}

static DatScannerBuffer *&CurrentBuffer() { return ORIG_VAR(006CA080, DatScannerBuffer *); }
static char *&CurrentPosition() { return ORIG_VAR(006CA084, char *); }
static char *&TokenText() { return ORIG_VAR(006C9064, char *); }
static int &CharactersRead() { return ORIG_VAR(006CA078, int); }
static unsigned char &HoldCharacter() { return ORIG_VAR(006CA07C, unsigned char); }
static char *&LastAcceptingPosition() { return ORIG_VAR(006CA068, char *); }
static unsigned &LastAcceptingState() { return ORIG_VAR(006CA06C, unsigned); }
static unsigned &StartState() { return ORIG_VAR(006CA088, unsigned); }
static int &DidSwitchOnEof() { return ORIG_VAR(006CA070, int); }
static int &TokenLength() { return ORIG_VAR(006CA074, int); }
static float &TokenValue() { return ORIG_VAR(006C9060, float); }
static FILE *&InputFile() { return ORIG_VAR(006CA08C, FILE *); }
static FILE *&OutputFile() { return ORIG_VAR(006CA090, FILE *); }
static int &FirstCall() { return ORIG_VAR(006C0F94, int); }

/* The original jumps here with the message in EAX, hence the single parameter; the replacement is a cdecl
 * function (build.py's adapter feeds it the register). */
DECOMP(0046FD90)
void DatLexerFatalError(const char *message)
{
    fprintf((FILE *)((char *)__iob_func() + 0x40), ORIG_STR(0060E438), message);
    exit(2);
    __builtin_unreachable();
}

/* 0x493130: the yywrap stub - the scanner has only one input source */
DECOMP(00493130)
int DatLexerWrap()
{
    return 1;
}

/* 0x493140: the scanner's fread - the bytes come from the shared CGameFile (0x6CA280), of which 0x6CA278 are
 * left.  A word that follows '#' is lowercased in place, as the game's text files write keywords that way. */
DECOMP(00493140)
unsigned DatLexerReadGameFile(char *buf, unsigned n)
{
    if (ORIG_VAR(006CA278, unsigned) == 0)
        return 0;
    if ((int)ORIG_VAR(006CA278, unsigned) < (int)n)
        n = ORIG_VAR(006CA278, unsigned);
    ORIG_VAR(006CA278, unsigned) -= n;
    ((CGameFile *)d_006CA280)->Read(buf, n);
    buf[n] = 0;

    for (char *p = buf; *p;) {
        if (*p == '#') {
            while (isalpha(p[1])) {
                p++;
                *p = (char)tolower(*p);
            }
        }
        p++;
    }
    return n;
}

DECOMP(0046FD30)
void DatLexerFlushBuffer(DatScannerBuffer *buf)
{
    buf->nChars = 0;
    buf->chBuf[0] = 0;
    buf->chBuf[1] = 0;
    buf->status = 0;
    buf->bufPos = buf->chBuf;
    buf->atBol = 1;
    if (buf == CurrentBuffer()) {
        CharactersRead() = buf->nChars;
        TokenText() = buf->bufPos;
        InputFile() = buf->input;
        HoldCharacter() = (unsigned char)*TokenText();
        CurrentPosition() = TokenText();
    }
}

DECOMP(0046FEE0)
void DatLexerInitBuffer(DatScannerBuffer *buf, FILE *file)
{
    DatLexerFlushBuffer(buf);
    buf->input = file;
    buf->fillBuffer = 1;
    if (file != nullptr)
        buf->interactive = _isatty(_fileno(file)) > 0;
    else
        buf->interactive = 0;
}

DECOMP(00470020)
DatScannerBuffer *DatLexerCreateBuffer(FILE *file, int size)
{
    DatScannerBuffer *buf = (DatScannerBuffer *)malloc(sizeof(DatScannerBuffer));
    if (buf == nullptr)
        DatLexerFatalError(ORIG_STR(0060E4B4));
    buf->bufSize = size;
    buf->chBuf = (char *)malloc((unsigned)size + 2);
    if (buf->chBuf == nullptr)
        DatLexerFatalError(ORIG_STR(0060E4B4));
    buf->ownBuffer = 1;
    DatLexerInitBuffer(buf, file);
    return buf;
}

DECOMP(004700B0)
char *DatLexerRestart(FILE *file)
{
    if (CurrentBuffer() == nullptr)
        CurrentBuffer() = DatLexerCreateBuffer(InputFile(), 0x4000);
    DatScannerBuffer *buf = CurrentBuffer();
    DatLexerFlushBuffer(buf);
    buf->input = file;
    buf->fillBuffer = 1;
    if (file == nullptr) {
        buf->interactive = 0;
    } else {
        buf->interactive = _isatty(_fileno(file)) > 0;
        buf = CurrentBuffer();
    }
    TokenText() = buf->bufPos;
    CharactersRead() = buf->nChars;
    InputFile() = buf->input;
    CurrentPosition() = TokenText();
    HoldCharacter() = (unsigned char)*TokenText();
    return TokenText();
}

/* Refills the buffer: the matched text is moved to its start, more characters are read through the game file
 * (the buffer grows when it is full) and the two closing NULs are written.  Returns 0 to continue scanning,
 * 1 at the end of the file and 2 when the last match has to be taken first. */
DECOMP(00470150)
int DatLexerGetNextBuffer()
{
    char *position = CurrentPosition();
    DatScannerBuffer *buf = CurrentBuffer();
    if ((uintptr_t)position > (uintptr_t)(buf->chBuf + 1 + CharactersRead()))
        DatLexerFatalError(ORIG_STR(0060E50C));
    if (buf->fillBuffer == 0)
        return (CurrentPosition() - TokenText() != 1) + 1;

    int matched = (int)(position - TokenText()) - 1;
    for (int i = 0; i < matched; i++)
        buf->chBuf[i] = TokenText()[i];

    int result;
    if (buf->status == 2) {
        CharactersRead() = 0;
    } else {
        int size = buf->bufSize;
        int available = size - matched;
        while (available - 1 < 1) {
            char *memory = buf->chBuf;
            if (buf->ownBuffer == 0) {
                buf->chBuf = nullptr;
                DatLexerFatalError(ORIG_STR(0060E4E0));
            }
            int newSize = (int)((unsigned)size * 2u);
            if (newSize < 1)
                newSize = (int)(((unsigned)size >> 3) + (unsigned)size);
            buf->bufSize = newSize;
            int offset = (int)(position - memory);
            char *newMemory = (char *)realloc(memory, (unsigned)newSize + 2);
            buf->chBuf = newMemory;
            if (newMemory == nullptr)
                DatLexerFatalError(ORIG_STR(0060E4E0));
            size = buf->bufSize;
            position = newMemory + offset;
            CurrentPosition() = position;
            available = size - matched;
        }
        unsigned toRead = (unsigned)(available - 1);
        if ((int)toRead > 0x2000)
            toRead = 0x2000;
        CharactersRead() = (int)DatLexerReadGameFile(matched + buf->chBuf, toRead);
        buf = CurrentBuffer();
        if (CharactersRead() != 0) {
            result = 0;
            goto done;
        }
    }

    if (matched == 0) {
        result = 1;
        DatLexerRestart(InputFile());
        buf = CurrentBuffer();
    } else {
        result = 2;
        buf->status = 2;
    }

done:
    CharactersRead() = CharactersRead() + matched;
    buf->chBuf[CharactersRead()] = 0;
    buf->chBuf[CharactersRead() + 1] = 0;
    TokenText() = buf->chBuf;
    return result;
}

DECOMP(004702C0)
unsigned DatLexerInput()
{
    bool wasNul = (HoldCharacter() == 0);
    *CurrentPosition() = (char)HoldCharacter();
    char *p = CurrentPosition();
    if (wasNul) {
        do {
            if (CurrentPosition() < CurrentBuffer()->chBuf + CharactersRead()) {
                *CurrentPosition() = 0;
                p = CurrentPosition();
                break;
            }
            TokenText() = CurrentPosition();
            CurrentPosition()++;
            int result = DatLexerGetNextBuffer();
            p = TokenText();
            if (result == 0)
                break;
            if (result != 1) {
                p = CurrentPosition();
                if (result == 2)
                    DatLexerFatalError(ORIG_STR(0060E544));
                break;
            }
            if (DatLexerWrap() != 0) {
                CurrentPosition() = TokenText();
                return 0xffffffff;
            }
            if (DidSwitchOnEof() == 0)
                DatLexerRestart(InputFile());
            wasNul = (HoldCharacter() == 0);
            *CurrentPosition() = (char)HoldCharacter();
            p = CurrentPosition();
        } while (wasNul);
    }
    unsigned char result = (unsigned char)*p;
    *p = 0;
    HoldCharacter() = (unsigned char)p[1];
    CurrentPosition() = p + 1;
    return result;
}

DECOMP(00470390)
void DatLexerSkipComment()
{
    unsigned ch = DatLexerInput();
    for (;;) {
        char c = (char)ch;
        if (c == 0 || (ch & 0xff) == 0xffffffff) {
            printf(ORIG_STR(0060E568));
            return;
        }
        if (c == '*' && (ch = DatLexerInput(), (char)ch == '/'))
            break;
        ch = DatLexerInput();
    }
}

/* The DFA state reached by the text from yytext to c_buf_p, recording the last accepting state on the way. */
DECOMP(0046FB90)
unsigned DatLexerGetPreviousState()
{
    unsigned state = StartState();
    char *p = TokenText();
    if (p < CurrentPosition()) {
        do {
            unsigned char c = (*p == 0) ? 1 : TableByte(d_0060D078, (unsigned char)*p);
            if (YY_ACCEPT[state] != 0) {
                LastAcceptingPosition() = p;
                LastAcceptingState() = state;
            }
            if ((unsigned)YY_CHK[YY_BASE[state] + c] != state) {
                do {
                    state = (unsigned)(int)YY_DEF[state];
                    if (state > 0x1c3)
                        c = TableByte(d_0060D478, c);
                } while ((unsigned)YY_CHK[YY_BASE[state] + c] != state);
            }
            state = (unsigned)(int)YY_NXT[YY_BASE[state] + c];
            p++;
        } while (p < CurrentPosition());
    }
    return state;
}

/* The state after the NUL at c_buf_p, or 0 when the scanner jams there. */
DECOMP(0046FC60)
unsigned DatLexerTryNulTransition(unsigned state)
{
    unsigned char c = 1;
    if (YY_ACCEPT[state] != 0) {
        LastAcceptingPosition() = CurrentPosition();
        LastAcceptingState() = state;
    }
    if ((unsigned)YY_CHK[YY_BASE[state] + c] != state) {
        do {
            state = (unsigned)(int)YY_DEF[state];
            if (state > 0x1c3)
                c = TableByte(d_0060D478, c);
        } while ((unsigned)YY_CHK[YY_BASE[state] + c] != state);
    }
    int next = YY_NXT[YY_BASE[state] + c];
    return next != 0x1c3 ? (unsigned)next : 0;
}

DECOMP(00470410)
int DatLexerNextToken()
{
    unsigned state;
    unsigned lastState = 0;
    unsigned nextState;
    unsigned char character;
    char *cp;
    char *tokenStart;
    char *actionCp;
    int action;

    if (FirstCall() != 0) {
        FirstCall() = 0;
        if (StartState() == 0)
            StartState() = 1;
        if (InputFile() == nullptr)
            InputFile() = __iob_func();
        if (OutputFile() == nullptr)
            OutputFile() = (FILE *)((char *)__iob_func() + 0x20);
        if (CurrentBuffer() == nullptr)
            CurrentBuffer() = DatLexerCreateBuffer(InputFile(), 0x4000);
        CharactersRead() = CurrentBuffer()->nChars;
        InputFile() = CurrentBuffer()->input;
        HoldCharacter() = (unsigned char)*CurrentBuffer()->bufPos;
        CurrentPosition() = CurrentBuffer()->bufPos;
    }

restart:
    state = StartState();
    *CurrentPosition() = (char)HoldCharacter();
    cp = CurrentPosition();
    tokenStart = cp;

match:
    do {
        character = TableByte(d_0060D078, (unsigned char)*cp);
        if (YY_ACCEPT[state] != 0) {
            LastAcceptingPosition() = cp;
            LastAcceptingState() = state;
        }
        if ((unsigned)YY_CHK[YY_BASE[state] + character] != state) {
            do {
                state = (unsigned)(int)YY_DEF[state];
                if (state > 0x1c3)
                    character = TableByte(d_0060D478, character);
            } while ((unsigned)YY_CHK[YY_BASE[state] + character] != state);
        }
        state = (unsigned)(int)YY_NXT[YY_BASE[state] + character];
        cp++;
        lastState = LastAcceptingState();
        nextState = state;
    } while (YY_BASE[state] != YY_JAMSTATE);

find_action:
    action = YY_ACCEPT[nextState];
    if (action == 0) {
        action = YY_ACCEPT[lastState];
        cp = LastAcceptingPosition();
    }
    TokenLength() = (int)(cp - tokenStart);
    TokenText() = tokenStart;
    HoldCharacter() = (unsigned char)*cp;
    *cp = 0;
    actionCp = cp;

    for (;;) {
        lastState = LastAcceptingState();
        CurrentPosition() = actionCp;
        switch (action) {
        case 0:
            /* the match did not end in an accepting state: take the last one */
            *cp = (char)HoldCharacter();
            nextState = lastState;
            cp = LastAcceptingPosition();
            goto find_action;
        case 1:
            return 0x102;
        case 2:
            return 0x103;
        case 3: {
            char *src = TokenText();
            char *dst = d_006C9068;
            for (;;) {
                char c = *src++;
                *dst++ = c;
                if (c == 0)
                    break;
            }
            return 0x104;
        }
        case 4:
            TokenValue() = (float)atof(TokenText());
            return 0x105;
        case 5: {
            /* a quoted string: its characters up to the closing quote, without whitespace */
            char *dst = d_006C9068;
            for (;;) {
                unsigned u = DatLexerInput();
                char c = (char)u;
                if (c == 0 || (u & 0xff) == 0xffffffff || c == '"')
                    break;
                if (c != '\n' && c != '\r' && c != '\t')
                    *dst++ = c;
            }
            *dst = 0;
            return 0x104;
        }
        case 6:
        case 0x57:
        case 0x58:
        case 0x59:
            goto restart;
        case 7:
            DatLexerSkipComment();
            goto restart;
        case 8:
            return 0x106;
        case 9:
            return 0x107;
        case 10:
            return 0x116;
        case 0xb:
            return 0x108;
        case 0xc:
            return 0x109;
        case 0xd:
            return 0x10a;
        case 0xe:
            return 0x10b;
        case 0xf:
            return 0x10c;
        case 0x10:
            return 0x10d;
        case 0x11:
            return 0x10e;
        case 0x12:
            return 0x10f;
        case 0x13:
            return 0x110;
        case 0x14:
            return 0x111;
        case 0x15:
            return 0x112;
        case 0x16:
            return 0x113;
        case 0x17:
            return 0x114;
        case 0x18:
            return 0x115;
        case 0x19:
            return 0x117;
        case 0x1a:
            return 0x118;
        case 0x1b:
            return 0x119;
        case 0x1c:
            return 0x11a;
        case 0x1d:
            return 0x11b;
        case 0x1e:
            return 0x11c;
        case 0x1f:
            return 0x11d;
        case 0x20:
            return 0x11e;
        case 0x21:
            return 0x11f;
        case 0x22:
            return 0x120;
        case 0x23:
            return 0x121;
        case 0x24:
            return 0x122;
        case 0x25:
            return 0x123;
        case 0x26:
            return 0x124;
        case 0x27:
            return 0x125;
        case 0x28:
            return 0x126;
        case 0x29:
            return 0x127;
        case 0x2a:
            return 0x128;
        case 0x2b:
            return 0x129;
        case 0x2c:
            return 0x12a;
        case 0x2d:
            return 299;
        case 0x2e:
            return 300;
        case 0x2f:
            return 0x12d;
        case 0x30:
            return 0x12e;
        case 0x31:
            return 0x12f;
        case 0x32:
            return 0x130;
        case 0x33:
            return 0x131;
        case 0x34:
            return 0x132;
        case 0x35:
            return 0x133;
        case 0x36:
            return 0x135;
        case 0x37:
            return 0x134;
        case 0x38:
            return 0x136;
        case 0x39:
            return 0x138;
        case 0x3a:
            return 0x13a;
        case 0x3b:
            return 0x13c;
        case 0x3c:
            return 0x137;
        case 0x3d:
            return 0x139;
        case 0x3e:
            return 0x13b;
        case 0x3f:
            return 0x13d;
        case 0x40:
            return 0x13e;
        case 0x41:
            return 0x13f;
        case 0x42:
            return 0x140;
        case 0x43:
            return 0x141;
        case 0x44:
            return 0x142;
        case 0x45:
            return 0x143;
        case 0x46:
            return 0x144;
        case 0x47:
            return 0x145;
        case 0x48:
            return 0x146;
        case 0x49:
            return 0x147;
        case 0x4a:
            return 0x148;
        case 0x4b:
            return 0x149;
        case 0x4c:
            return 0x14a;
        case 0x4d:
            return 0x14b;
        case 0x4e:
            return 0x14c;
        case 0x4f:
            return 0x14d;
        case 0x50:
            return 0x14e;
        case 0x51:
            return 0x14f;
        case 0x52:
            return 0x150;
        case 0x53:
            return 0x151;
        case 0x54:
            return 0x152;
        case 0x55:
            return 0x153;
        case 0x56:
            return 0x154;
        case 0x5a:
            /* ECHO: the unmatched text goes to yyout */
            fwrite(TokenText(), (size_t)TokenLength(), 1, OutputFile());
            goto restart;
        case 0x5b: {
            /* the end-of-buffer rule: either a real NUL inside the buffer, or a refill */
            int offset = (int)(actionCp - TokenText()) - 1;
            *cp = (char)HoldCharacter();
            DatScannerBuffer *buf = CurrentBuffer();
            if (buf->status == 0) {
                CharactersRead() = buf->nChars;
                buf->input = InputFile();
                buf->status = 1;
            }
            char *savedStart = TokenText();
            if (actionCp <= buf->chBuf + CharactersRead()) {
                cp = TokenText() + offset;
                CurrentPosition() = cp;
                state = DatLexerGetPreviousState();
                unsigned nulState = DatLexerTryNulTransition(state);
                tokenStart = savedStart;
                lastState = LastAcceptingState();
                if (nulState == 0) {
                    nextState = state;
                    goto find_action;
                }
                state = nulState;
                cp++;
                goto match;
            }
            int result = DatLexerGetNextBuffer();
            buf = CurrentBuffer();
            actionCp = TokenText();
            if (result == 0) {
                cp = TokenText() + offset;
                CurrentPosition() = cp;
                state = DatLexerGetPreviousState();
                tokenStart = actionCp;
                goto match;
            }
            if (result != 1) {
                if (result != 2)
                    goto restart;
                cp = buf->chBuf + CharactersRead();
                CurrentPosition() = cp;
                nextState = DatLexerGetPreviousState();
                tokenStart = TokenText();
                lastState = LastAcceptingState();
                goto find_action;
            }
            /* end of the file: yywrap decides between a new file and the EOF action */
            DidSwitchOnEof() = 0;
            if (DatLexerWrap() == 0) {
                if (DidSwitchOnEof() == 0)
                    DatLexerRestart(InputFile());
                goto restart;
            }
            action = (int)(StartState() - 1) / 2 + 0x5c;
            actionCp = TokenText();
            break;
        }
        case 0x5c:
            return 0;
        default:
            DatLexerFatalError(ORIG_STR(0060E570));
        }
    }
}
