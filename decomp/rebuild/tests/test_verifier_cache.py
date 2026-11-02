"""Negative control for the original/replacement instruction-cache regression."""


def test_rewritten_entry_executes_new_code(h):
    # STOP is mapped by Harness. Without invalidation, Unicorn can execute the
    # cached first body again and make differential comparisons pass vacuously.
    entry = h.alloc(16, b'\xb8\x01\x00\x00\x00\xc3')
    first = h.call(entry)
    h.uc.mem_write(entry, b'\xb8\x02\x00\x00\x00\xc3')
    second = h.call(entry)
    if first['fault'] or second['fault']:
        return ['cache control faulted: %r / %r' % (first['fault'], second['fault'])]
    if (first['eax'], second['eax']) != (1, 2):
        return ['rewritten entry returned %r, expected (1, 2)' % ((first['eax'], second['eax']),)]
    return []
