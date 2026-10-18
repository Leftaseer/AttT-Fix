/* decomp.h - glue between decompiled code and the original game binary.
 *
 * The rebuilt ATThrone.exe is the original code and data (relinked from the user's own exe, see exe2obj.py)
 * plus everything under rebuild/src.  Addresses below are always Ascension to the Throne (1.1.128) addresses;
 * for Valkyrie the build translates them through symbols/attt2valk.tsv and symbols/attt2valk_data.tsv.
 *
 *   DECOMP(004064D0)            put before a function definition: it replaces the original at that address.
 *                               Every call, pointer and vtable entry of the original then reaches it.
 *   ORIG_FN(00401680, float, (lua_State *L, int narg))
 *                               declares the original function sub_00401680 so new code can call it.  Original
 *                               functions with /LTCG register conventions get a generated cdecl shim: list the
 *                               register parameters first, in the order ECX, EAX, EDX, EBX, ESI, EDI.
 *   ORIG_THISCALL / ORIG_FASTCALL / ORIG_STDCALL   the same for the standard conventions.
 *   ORIG_VAR(006C8964, int)     an original global (an lvalue); the build declares d_006C8964 for it.
 *
 * Addresses are written as 8 hex digits without 0x so they can be pasted into identifiers.
 */
#pragma once

#ifdef __cplusplus
#define DECOMP_C extern "C"
#else
#define DECOMP_C extern
#endif

#define DECOMP(addr)

#define ORIG_FN(addr, ret, params)       DECOMP_C ret __cdecl sub_##addr params
#define ORIG_STDCALL(addr, ret, params)  DECOMP_C ret __stdcall sub_##addr params
#define ORIG_FASTCALL(addr, ret, params) DECOMP_C ret __fastcall sub_##addr params
#define ORIG_THISCALL(addr, ret, params) DECOMP_C ret __thiscall sub_##addr params
#define ORIG_CALL(addr) sub_##addr

#define ORIG_VAR(addr, type) (*(type *)d_##addr)

/* Lua 5.1 as configured in this engine: LUA_NUMBER is float */
typedef float lua_Number;
