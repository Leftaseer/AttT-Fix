/* CDatFile: the keyword database and its lifetime (0x444D50 / 0x445130). */
#include "game/common.h"
#include "game/datfile.h"

ORIG_DATA(0060A560); /* CDatFile::vftable */
ORIG_DATA(0060A4C4); /* CSingleton<CDatFile>::vftable */

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
