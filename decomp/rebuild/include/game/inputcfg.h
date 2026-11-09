/* CReadInputCfg: the key/value list of input.cfg - the record (CfgPair), the std::vector<CfgPair> the loader
 * fills (0x4A0BA0 ... 0x4A17A0), the loader object and its singleton (0x4A1650 / 0x4A1690 / 0x4A1840 /
 * 0x46EA50).
 *
 * Every token of the file makes one pair: a word becomes the key, the token after it becomes the value, and
 * both are plain texts (the scanner returns them in 0x6C9068).  The file ends with token 0. */
#pragma once
#include "game/common.h"

/* one key/value record of the file */
struct CfgPair {
    std::string key;   /* +00 */
    std::string value; /* +1C */
};
static_assert(sizeof(CfgPair) == 0x38, "CfgPair is 0x38 bytes");
static_assert(__builtin_offsetof(CfgPair, value) == 0x1C, "CfgPair::value");

/* std::vector<CfgPair> as the original lays it out: the empty allocator, then the three pointers.  The code
 * only ever touches the pointers, so the allocator keeps whatever the owner's memory held. */
struct CfgPairVector {
    unsigned allocator; /* +00 */
    CfgPair *begin;     /* +04 */
    CfgPair *end;       /* +08 */
    CfgPair *limit;     /* +0C */
};
static_assert(sizeof(CfgPairVector) == 0x10, "CfgPairVector is 0x10 bytes");

/* the record's lifetime: the default and copy constructors, the assignment (both texts) and the destructor */
CfgPair *__fastcall ConstructCfgPair(CfgPair *pair);                                    /* 0x4A0BA0 */
CfgPair *__thiscall CopyConstructCfgPair(CfgPair *pair, const CfgPair *other);          /* 0x4A0C90 */
CfgPair *__thiscall AssignCfgPair(CfgPair *pair, const CfgPair *other);                 /* 0x4A0D10 */
void __cdecl DestroyCfgPairs(CfgPair *first, CfgPair *last);                            /* 0x4A1130 */

/* vector's size and spare capacity (0 when the vector owns nothing) */
int __fastcall CfgPairCapacity(const CfgPairVector *vector);                            /* 0x4A0C30 */
int __fastcall CfgPairCount(const CfgPairVector *vector);                               /* 0x4A0C60 */

/* the element loops: copy construct [first, last), fill construct/fill assign count copies, copy backward,
 * destroy, and the two wrappers that report the end position (the fill one, 0x4A1230, already lives in
 * src/fixed as the containers' allocator template) */
CfgPair *__cdecl AllocateCfgPairs(unsigned count);                                      /* 0x4A0E10 */
CfgPair *__cdecl CopyConstructCfgPairs(const CfgPair *first, const CfgPair *last,
                                       CfgPair *dst);                                   /* 0x4A0F80 */
CfgPair *__stdcall CopyConstructCfgPairsEnd(const CfgPair *first, const CfgPair *last,
                                            CfgPair *dst);                              /* 0x4A1300 */
void __cdecl FillConstructCfgPairs(CfgPair *dst, unsigned count, const CfgPair *value); /* 0x4A1080 */
void __cdecl FillAssignCfgPairs(CfgPair *first, CfgPair *last, const CfgPair *value);   /* 0x4A0E80 */
CfgPair *__cdecl CopyBackwardCfgPairs(CfgPair *first, CfgPair *last, CfgPair *dst);    /* 0x4A0D40 */

/* vector's block: _Buy allocates count empty slots (false for an empty request), _Tidy frees them */
bool __thiscall BuyCfgPairs(CfgPairVector *vector, unsigned count);                     /* 0x4A1020 */
void __fastcall DestroyCfgPairVector(CfgPairVector *vector);                            /* 0x4A12C0 */

/* vector::_Insert_n and push_back */
void __thiscall InsertCfgPairs(CfgPairVector *vector, CfgPair *position, unsigned count,
                               const CfgPair *value);                                   /* 0x4A1330 */
void __thiscall InsertCfgPairAt(CfgPairVector *vector, CfgPair **result, CfgPair *position,
                                const CfgPair *value);                                  /* 0x4A1710 */
void __thiscall PushCfgPair(CfgPairVector *vector, const CfgPair *value);               /* 0x4A17A0 */

/* the singleton the game keeps: the pairs behind the class vtable */
struct CReadInputCfg {
    void *vftable;         /* +00 CSingleton<CReadInputCfg>, 0x610078 while the class is alive */
    CfgPairVector entries; /* +04 */

    CReadInputCfg();                          /* 0x4A1650 */
    ~CReadInputCfg();                         /* 0x4A1690 */
    void Load(const std::string &name);       /* 0x4A1840 */
    static CReadInputCfg *__stdcall Instance(); /* 0x46EA50 */
};
static_assert(sizeof(CReadInputCfg) == 0x14, "CReadInputCfg is 0x14 bytes");
static_assert(__builtin_offsetof(CReadInputCfg, entries) == 0x04, "CReadInputCfg::entries");

/* the deleting destructor behind the class vtable slot 0 */
CReadInputCfg *__thiscall DeleteCReadInputCfg(CReadInputCfg *object, unsigned char flags); /* 0x4A1780 */
