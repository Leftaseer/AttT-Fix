/* The scanner of the dat files: flex 2.5's yylex (0x470410) and the input machinery it generates (the buffer
 * 0x470020 / 0x46FEE0 / 0x46FD30, yyrestart 0x4700B0, yy_get_next_buffer 0x470150, yyinput 0x4702C0 and the
 * helpers 0x46FB90 / 0x46FC60), plus the game's own pieces: the read through the shared CGameFile (0x493140) and
 * the yywrap stub (0x493130).
 *
 * The scanner keeps its state in fixed globals (0x6C9060 is the number of the last token, 0x6C9068 its text,
 * 0x6CA07C/84 the hold character and the current position, 0x6CA080 the buffer) and returns the token numbers
 * the dat parsers switch on: 0x102 and 0x103 delimit a block, 0x104 is a word or a quoted string (its text in
 * 0x6C9068), 0x105 a number (its value in 0x6C9060), 0x106 and up are keywords, and 0 is the end of the file. */
#pragma once
#include "game/common.h"

/* token numbers of yylex (the keywords the interface record parser uses start at 0x106) */
enum {
    DAT_TOKEN_EOF = 0,
    DAT_TOKEN_BLOCK_OPEN = 0x102,
    DAT_TOKEN_BLOCK_CLOSE = 0x103,
    DAT_TOKEN_WORD = 0x104,
    DAT_TOKEN_NUMBER = 0x105,
};

/* the scanner's input buffer (yy_buffer_state, 0x28 bytes) */
struct DatScannerBuffer {
    FILE *input;     /* +00 the stream the buffer was made for (the reads themselves go through CGameFile) */
    char *chBuf;     /* +04 the characters, ending with two NULs */
    char *bufPos;    /* +08 */
    int bufSize;     /* +0C */
    int nChars;      /* +10 valid characters in chBuf */
    int ownBuffer;   /* +14 free chBuf with the buffer */
    int interactive; /* +18 _isatty(_fileno(input)) */
    int atBol;       /* +1C */
    int fillBuffer;  /* +20 0 when there is nothing more to read */
    int status;      /* +24 0 new, 1 normal, 2 end of file pending */
};
static_assert(sizeof(DatScannerBuffer) == 0x28, "DatScannerBuffer is 0x28 bytes");

DatScannerBuffer *DatLexerCreateBuffer(FILE *file, int size);       /* 0x470020 */
void DatLexerInitBuffer(DatScannerBuffer *buf, FILE *file);          /* 0x46FEE0 */
void DatLexerFlushBuffer(DatScannerBuffer *buf);                     /* 0x46FD30 */
char *DatLexerRestart(FILE *file);                                   /* 0x4700B0 */
int DatLexerGetNextBuffer();                                         /* 0x470150 */
unsigned DatLexerInput();                                            /* 0x4702C0 */
void DatLexerSkipComment();                                          /* 0x470390 */
unsigned DatLexerGetPreviousState();                                 /* 0x46FB90 */
unsigned DatLexerTryNulTransition(unsigned state);                   /* 0x46FC60 */
[[noreturn]] void DatLexerFatalError(const char *message);           /* 0x46FD90 */
int DatLexerWrap();                                                  /* 0x493130 */
unsigned DatLexerReadGameFile(char *buf, unsigned n);                /* 0x493140 */
int DatLexerNextToken();                                             /* 0x470410 */
