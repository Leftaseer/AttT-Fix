/* CDatFile: the keyword database and its lifetime (0x444D50 / 0x445130). */
#include "game/common.h"
#include "game/datfile.h"

ORIG_DATA(0060A560); /* CDatFile::vftable */
ORIG_DATA(0060A4C4); /* CSingleton<CDatFile>::vftable */
ORIG_DATA(0060A4B0); /* int[2]: the keyword count of each format set (3 and 8) */

/* the dat reader of LoadSource (CDelCom, 0xB0 bytes: vftable, the current character, an ifstream, the text) */
ORIG_THISCALL(00444AD0, void *, (void *self));                                     /* constructor */
ORIG_THISCALL(00444B40, void, (void *self));                                       /* destructor */
ORIG_THISCALL(00445630, void *, (void *self, void *result, const std::string *name)); /* reads the file into result */

inline void *operator new(unsigned int, void *p) { return p; }

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

/* the stack reader LoadSource constructs: only its address crosses the calls to 0x444AD0 / 0x445630 / 0x444B40 */
struct DatReader {
    alignas(4) unsigned char storage[0xB0];
};

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

    DatReader reader;
    sub_00444AD0(&reader);
    sources[sourceCount].name = file;
    /* the reader returns its text through the hidden result of a copy constructor into uninitialised storage */
    alignas(std::string) unsigned char textStorage[sizeof(std::string)];
    sub_00445630(&reader, textStorage, &file);
    std::string &text = *reinterpret_cast<std::string *>(textStorage);
    sources[sourceCount].text = text;
    text.~basic_string();
    currentSource = sourceCount;
    if (sourceCount < 9)
        sourceCount++;
    sub_00444B40(&reader);
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
