/* 0x00450700: copy-constructs the std::string at the argument from the one in ECX, returns it (a function
 * returning a string by value through its hidden result pointer) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C undefined4 (__thiscall *imp_00607334)(_Demangler_std_basic_string_char_struct_std__char_traits_char__class_std__allocator_char___ *, _Demangler_std_basic_string_char_struct_std__char_traits_char__class_std__allocator_char___ *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");

DECOMP(00450700)
void * __thiscall f_00450700(void *src, void *result)
{
    imp_00607334(result, src);
    return result;
}
