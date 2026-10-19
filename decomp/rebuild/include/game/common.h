/* Common declarations of the decompiled game code: Win32/D3D9, the MSVC 2005 std::string, CGameException. */
#pragma once
#include <windows.h>
#include <d3d9.h>
#include "decomp.h"
#include "msvc8/string.h"

/* operator new / delete of the game: MSVCR80 */
void *operator new(unsigned int size);
void operator delete(void *p);

/* The engine reports errors by throwing CGameException (a std::string with the message, file and line). */
struct CGameException {
    std::string text;
    CGameException(const std::string &msg, const char *file, int line);   /* 0x421220 */
};
[[noreturn]] void ThrowGameException(const char *msg, const char *file, int line);

/* strings of the original (the game's texts are cp1251): ORIG_STR(00607BC8) */
#define ORIG_STR(addr) ((const char *)d_##addr)

/* MSVCR80 */
struct _iobuf;
typedef struct _iobuf FILE;
extern "C" __declspec(dllimport) FILE *__cdecl fopen(const char *name, const char *mode);
extern "C" __declspec(dllimport) size_t __cdecl fwrite(const void *p, size_t size, size_t n, FILE *f);
extern "C" __declspec(dllimport) int __cdecl fclose(FILE *f);
extern "C" __declspec(dllimport) char *__cdecl fgets(char *buf, int n, FILE *f);
extern "C" __declspec(dllimport) int __cdecl sscanf(const char *s, const char *fmt, ...);
extern "C" __declspec(dllimport) void __stdcall _CxxThrowException(void *object, void *throwInfo);
extern "C" __declspec(dllimport) int __cdecl sprintf(char *buf, const char *fmt, ...);
extern "C" __declspec(dllimport) size_t __cdecl strlen(const char *s);
