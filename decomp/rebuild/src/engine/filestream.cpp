/* The file system's file objects (0x450A80 .. 0x450D00): the base file, a section of a pak and a file on disk.
 * CArchFile::Read kept its own readable file (src/fixed/f_004508C0.c). */
#include "game/common.h"
#include "game/filestream.h"
#include "msvc8/fstream.h"

ORIG_DATA(0060B148); /* CBaseFile::vftable */
ORIG_DATA(0060B160); /* CArchFile::vftable */
ORIG_DATA(0060B174); /* "Файл не найден: " */
ORIG_DATA(0060B18C); /* CFstreamFile::vftable */

DECOMP_C void *(__thiscall *imp_006072D4)(void *, void *) __asm__(
    "__imp_?tellg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAE?AV?$fpos@H@2@XZ");
DECOMP_C void *(__cdecl *imp_006071D8)(void *, const char *, const void *) __asm__(
    "__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBDABV10@@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__(
    "__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__(
    "__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

inline void *operator new(unsigned int, void *p) { return p; }

/* the constructor announces a missing file by building "Файл не найден: " + path and discarding it */
static void AnnounceMissingFile(const std::string &path)
{
    alignas(4) unsigned char message[0x1C], copy[0x1C];
    imp_006071D8(message, ORIG_STR(0060B174), &path);
    imp_00607334(copy, message);
    imp_00607330(copy);
    imp_00607330(message);
}

DECOMP(00450A80)
CBaseFile::CBaseFile()
{
    owner = nullptr;
    vftable = d_0060B148;
    size = 0;
}

DECOMP(00450AA0)
CBaseFile::~CBaseFile()
{
    vftable = d_0060B148;
}

DECOMP(00450AB0)
void *CBaseFile::Destroy(int flags)
{
    this->~CBaseFile();
    if (flags & 1)
        operator delete(this);
    return this;
}

DECOMP(00450AE0)
CArchFile::CArchFile(void *pakStream, unsigned fileSize, unsigned fileOffset, bool isEncrypted)
{
    owner = nullptr;
    position = 0;
    stream = pakStream;
    offset = fileOffset;
    vftable = d_0060B160;
    encrypted = isEncrypted;
    size = fileSize;
}

DECOMP(0042B630)
unsigned CArchFile::Seek(unsigned pos)
{
    position = pos;
    return pos;
}

DECOMP(00450B10)
unsigned CArchFile::Advance(unsigned delta)
{
    position += delta;
    return delta;
}

DECOMP(005B42C0)
unsigned CArchFile::Tell()
{
    return position;
}

DECOMP(00450B20)
CFstreamFile::CFstreamFile(const std::string &path)
{
    owner = nullptr;
    size = 0;
    vftable = d_0060B18C;

    std::ifstream &in =
        *new (stream) std::ifstream(path.c_str(), std::ios_base::_In | std::ios_base::_Binary,
                                    std::ios_base::_Openprot);
    if (in.fail())
        AnnounceMissingFile(path);

    in.seekg(0, 2); /* end */
    alignas(4) unsigned char pos[0x18];
    imp_006072D4(stream, pos); /* tellg returns the fpos through this buffer */
    size = *(unsigned *)(pos + 8) + *(unsigned *)(pos + 0);
    in.seekg(0, 0); /* begin */
}

DECOMP(00450C90)
CFstreamFile::~CFstreamFile()
{
    vftable = d_0060B18C;
    std::ifstream &in = *(std::ifstream *)stream;
    in.close();
    in.~basic_ifstream();
}

DECOMP(00450C20)
void *CFstreamFile::Read(void *buf, unsigned n)
{
    std::ifstream &in = *(std::ifstream *)stream;
    in.read((char *)buf, (int)n);
    return &in;
}

DECOMP(00450C30)
void *CFstreamFile::Seek(long pos)
{
    std::ifstream &in = *(std::ifstream *)stream;
    in.seekg(pos, 0);
    return &in;
}

DECOMP(00450C50)
void *CFstreamFile::Advance(long delta)
{
    std::ifstream &in = *(std::ifstream *)stream;
    in.seekg(delta, 1);
    return &in;
}

DECOMP(00450C70)
int CFstreamFile::Tell()
{
    alignas(4) unsigned char pos[0x18];
    imp_006072D4(stream, pos);
    return *(int *)(pos + 8) + *(int *)(pos + 0);
}

DECOMP(00450D00)
void *CFstreamFile::Destroy(int flags)
{
    this->~CFstreamFile();
    if (flags & 1)
        operator delete(this);
    return this;
}
