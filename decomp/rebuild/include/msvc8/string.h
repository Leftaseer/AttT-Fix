/* std::basic_string<char> of Visual C++ 2005 (MSVCP80.dll), the one the game's objects contain.
 * Same layout (28 bytes) and the member functions imported from MSVCP80.dll, so a std::string made here can be
 * handed to original code and back.  Only what the decompiled code needs is declared; add more members as
 * they come up (they must exist in MSVCP80.dll - see its export list).
 *
 *   +0x00 allocator (empty, padded)   +0x04 union { char buf[16]; char *ptr; }   +0x14 size   +0x18 capacity
 */
#pragma once
#include <stddef.h>

#define MSVCP80_IMPORT __declspec(dllimport)

namespace std {

template <class E> struct char_traits;
template <class T> class allocator;
template <class E, class Tr, class A> class basic_ostream;
template <class E, class Tr, class A> class _String_iterator;
template <class E, class Tr, class A> class _String_const_iterator;

template <class E, class Tr = char_traits<E>, class A = allocator<E>>
class basic_string {
public:
    typedef unsigned int size_type;
    MSVCP80_IMPORT static const size_type npos;

    MSVCP80_IMPORT basic_string();
    MSVCP80_IMPORT basic_string(const E *s);
    MSVCP80_IMPORT basic_string(const basic_string &s);
    MSVCP80_IMPORT ~basic_string();

    MSVCP80_IMPORT basic_string &operator=(const E *s);
    MSVCP80_IMPORT basic_string &operator=(const basic_string &s);
    MSVCP80_IMPORT basic_string &operator+=(const E *s);
    MSVCP80_IMPORT basic_string &operator+=(const basic_string &s);
    MSVCP80_IMPORT basic_string &operator+=(E c);
    MSVCP80_IMPORT basic_string &append(const E *s, size_type n);
    MSVCP80_IMPORT basic_string &erase(size_type off, size_type count);
    MSVCP80_IMPORT void clear();
    MSVCP80_IMPORT void swap(basic_string &s);

    MSVCP80_IMPORT const E *c_str() const;
    MSVCP80_IMPORT const E *data() const;
    MSVCP80_IMPORT size_type size() const;
    MSVCP80_IMPORT E &at(size_type i);
    MSVCP80_IMPORT size_type find(const E *s, size_type off) const;
    MSVCP80_IMPORT size_type find(E c, size_type off) const;
    MSVCP80_IMPORT size_type rfind(const E *s, size_type off) const;
    MSVCP80_IMPORT size_type rfind(E c, size_type off) const;
    MSVCP80_IMPORT size_type find_last_of(const E *s, size_type off) const;
    MSVCP80_IMPORT basic_string substr(size_type off, size_type count) const;

    /* inline in the original headers (no export): */
    bool empty() const { return mysize == 0; }
    size_type length() const { return mysize; }
    size_type capacity() const { return myres; }
    const E *raw() const { return myres < 16 / sizeof(E) ? bx.buf : bx.ptr; }

private:
    unsigned char alval[4];          /* allocator<char> (empty) */
    union { E buf[16 / sizeof(E)]; E *ptr; } bx;
    size_type mysize;
    size_type myres;
};

typedef basic_string<char> string;

template <class E, class Tr, class A>
MSVCP80_IMPORT basic_string<E, Tr, A> operator+(const basic_string<E, Tr, A> &a, const basic_string<E, Tr, A> &b);
template <class E, class Tr, class A>
MSVCP80_IMPORT basic_string<E, Tr, A> operator+(const E *a, const basic_string<E, Tr, A> &b);
template <class E, class Tr, class A>
MSVCP80_IMPORT basic_string<E, Tr, A> operator+(const basic_string<E, Tr, A> &a, const E *b);
template <class E, class Tr, class A>
MSVCP80_IMPORT basic_string<E, Tr, A> operator+(const basic_string<E, Tr, A> &a, E b);
template <class E, class Tr, class A>
MSVCP80_IMPORT bool operator==(const basic_string<E, Tr, A> &a, const E *b);
template <class E, class Tr, class A>
MSVCP80_IMPORT bool operator==(const basic_string<E, Tr, A> &a, const basic_string<E, Tr, A> &b);
template <class E, class Tr, class A>
MSVCP80_IMPORT bool operator!=(const basic_string<E, Tr, A> &a, const E *b);
template <class E, class Tr, class A>
MSVCP80_IMPORT bool operator!=(const basic_string<E, Tr, A> &a, const basic_string<E, Tr, A> &b);
template <class E, class Tr, class A>
MSVCP80_IMPORT bool operator<(const basic_string<E, Tr, A> &a, const basic_string<E, Tr, A> &b);

/* the instantiation that lives in MSVCP80.dll */
extern template class basic_string<char>;

static_assert(sizeof(string) == 28, "MSVC 2005 std::string is 28 bytes");

} // namespace std
