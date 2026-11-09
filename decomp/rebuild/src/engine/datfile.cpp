/* CDatFile: the keyword database and its lifetime (0x444D50 / 0x445130 / 0x445DB0), the tokenizer
 * (0x445240 / 0x445C60 / 0x445CD0) and the number parser of the token reader (0x4452A0). */
#include "game/common.h"
#include "game/datfile.h"
#include "game/delcom.h"

ORIG_DATA(0060A560); /* CDatFile::vftable */
ORIG_DATA(0060A4C4); /* CSingleton<CDatFile>::vftable */
ORIG_DATA(0060A4B0); /* int[2]: the keyword count of each format set (3 and 8) */
ORIG_DATA(0060A5A8); /* ".\\DatFile.cpp" */
ORIG_DATA(0060A600); /* "Error in file '" */
ORIG_DATA(0060A5EC); /* "' after keyword '" */
ORIG_DATA(0060A5E4); /* "' - '" */
ORIG_DATA(0060A5D4); /* " is not number" */
ORIG_DATA(0060A610); /* "Invalid paramenter after keyword '" */
ORIG_DATA(0060A634); /* "Don't find a '}' after keyword '" */
ORIG_DATA(0060A660); /* "' in file '" */
ORIG_DATA(0060A66C); /* "Can't find keyword '" */
ORIG_DATA(0060A684); /* "Can't load file '" */
ORIG_DATA(0069916C); /* CGameException _ThrowInfo */

ORIG_FN(005E3B10, void *, (unsigned int size)); /* operator new[] */

extern "C" __declspec(dllimport) int __cdecl msvc_tolower(int c) __asm__("_tolower");
extern "C" __declspec(dllimport) int __cdecl msvc_isdigit(int c) __asm__("_isdigit");

inline void *operator new(unsigned int, void *p) { return p; }

static void ThrowDatError(const std::string &msg, int line)
{
    CGameException e(msg, ORIG_STR(0060A5A8), line);
    _CxxThrowException(&e, d_0069916C);
    __builtin_unreachable();
}

/* a counted array of keyword pairs: the count sits in the word before the first element */
static DatPair *AllocatePairs(int count)
{
    unsigned char *block = (unsigned char *)operator new(4 + count * sizeof(DatPair));
    *(unsigned *)block = count;
    DatPair *pairs = (DatPair *)(block + 4);
    for (int i = 0; i < count; i++)
        new (pairs + i) DatPair;
    return pairs;
}

DECOMP(00444D50)
CDatFile::CDatFile()
{
    vftable = d_0060A560;

    for (int i = 0; i < 10; i++)
        sources[i].pos = 0;
    sourceCount = 0;
    currentSource = 0;

    formatSets[0] = AllocatePairs(3);
    formatSets[1] = AllocatePairs(8);

    DatPair *set0 = formatSets[0];
    set0[0].keyword = "fullscreen";
    set0[0].format = "n";
    set0[1].keyword = "resolution";
    set0[1].format = "nn";
    set0[2].keyword = "texturequality";
    set0[2].format = "n";

    DatPair *set1 = formatSets[1];
    set1[0].keyword = "cameraforward";
    set1[1].keyword = "cameraback";
    set1[2].keyword = "cameraleft";
    set1[3].keyword = "cameraright";
    set1[4].keyword = "cameraup";
    set1[5].keyword = "cameradown";
    set1[6].keyword = "gamepause";
    set1[7].keyword = "cameratoggle";
    for (int i = 0; i < 8; i++)
        set1[i].format = "w";

    sourcePos = 0;
    token = 0;
    for (int i = 0; i < 300; i++) {
        records[i].words = nullptr;
        records[i].numbers = nullptr;
    }
    recordCount = 0;
}

/* the ten sources and tokenText are destroyed by the compiler-generated part of this destructor after the body;
 * the original destroys them right after the tables and the record arrays, which is unobservable */
DECOMP(00445130)
CDatFile::~CDatFile()
{
    vftable = d_0060A560;

    for (int i = 0; i < 300; i++) {
        DatRecord &record = records[i];
        if (record.words) {
            unsigned count = ((unsigned *)record.words)[-1];
            for (unsigned j = 0; j < count; j++)
                record.words[j].~basic_string();
            operator delete[]((unsigned *)record.words - 1);
        }
        if (record.numbers)
            operator delete[](record.numbers);
    }

    for (int set = 0; set < 2; set++) {
        DatPair *pairs = formatSets[set];
        if (!pairs)
            continue;
        unsigned count = ((unsigned *)pairs)[-1];
        for (unsigned j = 0; j < count; j++)
            pairs[j].~DatPair();
        operator delete[]((unsigned *)pairs - 1);
    }

    vftable = d_0060A4C4;
}

/* the ten sources are a cache keyed by the file name: a hit just makes it current, a miss reads the file through
 * the reader (0x444AD0-0x444B40) and appends it (the table stops at 9). The original also catches the reader's
 * CGameException and rethrows it with " in file '<name>')" and DatFile.cpp:443; without exceptions the reader's
 * own error propagates instead. Returns true in both paths. */
DECOMP(00445AB0)
bool CDatFile::LoadSource(const std::string &file)
{
    sourcePos = 0;
    tokenText = "";

    for (int i = 0; i < sourceCount; i++)
        if (sources[i].name == file) {
            currentSource = i;
            return true;
        }

    CDelCom reader;
    sources[sourceCount].name = file;
    sources[sourceCount].text = reader.ReadFile(file);
    currentSource = sourceCount;
    if (sourceCount < 9)
        sourceCount++;
    return true;
}

/* the character at sourcePos; the position stops on the last character rather than running past the text */
DECOMP(00445240)
void CDatFile::ReadChar()
{
    const std::string &text = sources[currentSource].text;
    token = text.c_str()[sourcePos];
    if (text.size() <= ++sourcePos)
        sourcePos--;
}

/* spaces before a token (the original's state machine never re-reads there, so it would spin on one), then the
 * token up to the next space, line break or the end of the text */
DECOMP(00445C60)
void CDatFile::ReadToken()
{
    tokenText = "";
    do
        ReadChar();
    while (token == ' ');
    if (token == '\0' || token == '\n')
        return;
    do {
        tokenText += token;
        ReadChar();
    } while (token != ' ' && token != '\n' && token != '\0');
}

/* finds the keyword in the current format set, then reads tokens up to the "#keyword" line */
DECOMP(00445CD0)
bool CDatFile::SelectKeyword(const std::string &keyword)
{
    const int count = ((const int *)d_0060A4B0)[formatSet];
    DatPair *const pairs = formatSets[formatSet];
    int i = 0;

    if (count <= 0)
        return false;
    while (!(pairs[i].keyword == keyword))
        if (++i >= count)
            return false;

    keywordIndex = i;
    ReadToken();
    while (!tokenText.empty()) {
        if (tokenText.c_str()[0] == '#') {
            tokenText.erase(0, 1);
            if (tokenText == keyword)
                return true;
        }
        ReadToken();
    }
    return false;
}

static void ThrowKeywordError(const char *what, const std::string &keyword, const std::string &file, int line)
{
    ThrowDatError(std::string(what) + keyword + ORIG_STR(0060A660) + file + '\'', line);
}

static void ThrowNumberError(const std::string &file, const std::string &keyword, const std::string &token, int line)
{
    ThrowDatError(std::string(ORIG_STR(0060A600)) + file + ORIG_STR(0060A5EC) + keyword +
                      ORIG_STR(0060A5E4) + token + ORIG_STR(0060A5D4), line);
}

/* releases the counted word arrays and the number arrays of the first count records */
static void FreeRecords(CDatFile &dat, unsigned count)
{
    for (unsigned i = 0; i < count; i++) {
        DatRecord &record = dat.records[i];
        if (record.words) {
            unsigned n = ((unsigned *)record.words)[-1];
            for (unsigned j = 0; j < n; j++)
                record.words[j].~basic_string();
            operator delete[]((unsigned *)record.words - 1);
            record.words = nullptr;
        }
        if (record.numbers) {
            operator delete[](record.numbers);
            record.numbers = nullptr;
        }
    }
}

/* the arrays of one record: the words are a counted array of strings (the count before the first one), the
 * numbers a plain float array; a zero size leaves that array as it was, as the original does */
static void AllocateRecord(CDatFile &dat, unsigned words, unsigned numbers)
{
    DatRecord &record = dat.records[dat.recordCount];
    if (words) {
        unsigned char *block = (unsigned char *)sub_005E3B10(4 + words * sizeof(std::string));
        *(unsigned *)block = words;
        std::string *strings = (std::string *)(block + 4);
        for (unsigned i = 0; i < words; i++)
            new (strings + i) std::string;
        record.words = strings;
    }
    if (numbers)
        record.numbers = (float *)sub_005E3B10(numbers * sizeof(float));
}

/* The by-value std::string of 0x4452A0's argument: the original takes the token copy on the stack (seven
 * dwords), parses it and destroys it.  Keeping that layout lets the original callers jump straight into the
 * replacement. */
typedef struct { unsigned words[7]; } DatTokenText;

/* 0x4452A0: a whole token as a decimal number - an optional sign, digits and an optional fraction, and nothing
 * else.  The original appends a NUL to its copy of the token so the state machine can stop on the end; the
 * products and the fraction accumulate in x87 precision, so the value rounds exactly like the original's. */
static bool ParseTokenNumberText(std::string &text, float *out)
{
    text += '\0';

    unsigned pos = 0, divisor = 1;
    int state = 0;
    bool negative = false;
    float value = 0.0f;

    for (;;) {
        const char c = text[pos];
        switch (state) {
        case 0: /* before anything: empty fails, a digit, a point or a sign start the number */
            if (c == '\0')
                return false;
            if (msvc_isdigit(c)) {
                value = (float)(c - '0');
                pos++;
                state = 2;
            } else if (c == '.') {
                pos++;
                state = 5;
            } else if (c == '-' || c == '+') {
                negative = c == '-';
                state = 1;
                pos++;
            } else {
                return false;
            }
            break;
        case 1: /* after a sign: a digit or a point */
            if (msvc_isdigit(c))
                state = 2;
            else if (c == '.') {
                state = 4;
                pos++;
            } else {
                return false;
            }
            break;
        case 2: /* integer digits */
            if (msvc_isdigit(c)) {
                const int digit = c - '0';
                pos++;
                value = (float)((long double)value * 10.0L + digit);
            } else if (c == '.') {
                pos++;
                state = 4;
            } else if (c == '\0') {
                goto done;
            } else {
                return false;
            }
            break;
        case 3: /* fraction digits, each one over the growing divisor */
            if (msvc_isdigit(c)) {
                const int digit = c - '0';
                divisor *= 10;
                pos++;
                value = (float)((long double)digit / (long double)divisor + (long double)value);
            } else if (c == '\0') {
                goto done;
            } else {
                return false;
            }
            break;
        case 4: /* after the point: a digit starts the fraction, the end leaves a whole number ("12.") */
            if (msvc_isdigit(c))
                state = 3;
            else if (c == '\0')
                goto done;
            else
                return false;
            break;
        default: /* 5: after a leading point ("+.5") */
            if (msvc_isdigit(c))
                state = 3;
            else
                return false;
            break;
        }
    }
done:
    /* the original negates with the constant at 0x608088: -0.0 - value, which keeps "-0" negative */
    *out = negative ? -0.0f - value : value;
    return true;
}

/* The original's entry: the copy of the token arrives in its argument area and the function owns it, so it is
 * destroyed here at both exits. */
DECOMP(004452A0)
bool __stdcall ParseTokenNumber(DatTokenText text, float *out)
{
    std::string &copy = *(std::string *)(void *)&text;
    const bool ok = ParseTokenNumberText(copy, out);
    copy.~basic_string();
    return ok;
}

/* one format character of the current record: a word is the token, a number is the token parsed (a token that is
 * not a number returns false) */
static bool ReadField(CDatFile &dat, char format, unsigned &wordIndex, unsigned &numberIndex)
{
    DatRecord &record = dat.records[dat.recordCount];
    if (format == 'w') {
        record.words[wordIndex] = dat.tokenText;
        wordIndex++;
    } else if (format == 'n') {
        float value;
        std::string token(dat.tokenText);
        if (!ParseTokenNumberText(token, &value))
            return false;
        record.numbers[numberIndex] = value;
        numberIndex++;
    }
    return true;
}

/* The records of a keyword.  The format of the entry ("w" a word, "n" a number) is either followed by
 * "{ record record ... }" or by records that end at the line break; a token that is not a number, a missing
 * keyword and a missing terminator throw (from DatFile.cpp). */
static bool ReadKeywordRecords(CDatFile &dat, const std::string &file, std::string &keyword,
                               DatRecord **table, unsigned *count, int set)
{
    dat.formatSet = set;

    FreeRecords(dat, dat.recordCount);
    dat.recordCount = 0;

    if (!dat.LoadSource(file))
        ThrowDatError(std::string(ORIG_STR(0060A684)) + file + '\'', 0x124);

    for (unsigned i = 0; i < keyword.size(); i++)
        keyword[i] = (char)msvc_tolower(keyword[i]);

    if (!dat.SelectKeyword(keyword) && (set == 0 || set == 1))
        ThrowKeywordError(ORIG_STR(0060A66C), keyword, file, 0x12E);

    std::string &format = dat.formatSets[dat.formatSet][dat.keywordIndex].format;
    unsigned wordsPerRecord = 0, numbersPerRecord = 0;
    for (unsigned i = 0; i < format.size(); i++) {
        if (format[i] == 'w')
            wordsPerRecord++;
        else if (format[i] == 'n')
            numbersPerRecord++;
    }

    bool multiline = false;
    dat.ReadToken();
    if (dat.token == '\n')
        multiline = true;

    if (dat.tokenText == "{") {
        dat.ReadToken();
        while (dat.tokenText != "}") {
            if (dat.tokenText.empty())
                ThrowKeywordError(ORIG_STR(0060A634), keyword, file, 0x147);
            AllocateRecord(dat, wordsPerRecord, numbersPerRecord);
            unsigned wordIndex = 0, numberIndex = 0;
            for (unsigned i = 0; i < format.size(); i++) {
                if (dat.tokenText.empty())
                    ThrowKeywordError(ORIG_STR(0060A610), keyword, file, 0x154);
                if (!ReadField(dat, format[i], wordIndex, numberIndex))
                    ThrowNumberError(file, keyword, dat.tokenText, 0x15E);
                dat.ReadToken();
            }
            dat.recordCount++;
        }
    } else {
        bool done = false;
        while (!done) {
            AllocateRecord(dat, wordsPerRecord, numbersPerRecord);
            unsigned wordIndex = 0, numberIndex = 0;
            for (unsigned i = 0; i < format.size(); i++) {
                if (dat.tokenText.empty())
                    ThrowKeywordError(ORIG_STR(0060A610), keyword, file, 0x180);
                if (!ReadField(dat, format[i], wordIndex, numberIndex))
                    ThrowNumberError(file, keyword, dat.tokenText, 0x18A);
                if (multiline) {
                    done = true;
                    break;
                }
                dat.ReadToken();
                if (dat.token == '\n')
                    multiline = true;
            }
            dat.recordCount++;
        }
    }

    *table = dat.records;
    *count = dat.recordCount;
    return true;
}

/* The keyword object came by value in the seven dwords kw0..kw6, which the original callee destroys; the shim
 * forwards to the readable reader.  A throw leaves the string for the caller's unhandled exception, as the rest
 * of the rebuilt reader does. */
DECOMP(00445DB0)
bool CDatFile::ReadKeywords(const std::string *file, unsigned kw0, unsigned kw1, unsigned kw2, unsigned kw3,
                            unsigned kw4, unsigned kw5, unsigned kw6, DatRecord **table, unsigned *count, int set)
{
    std::string &keyword = *(std::string *)(void *)&kw0;
    bool ok = ReadKeywordRecords(*this, *file, keyword, table, count, set);
    keyword.~basic_string();
    return ok;
}
