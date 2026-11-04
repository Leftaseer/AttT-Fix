#include <stddef.h>
#include <stdint.h>

// Resolve libc calls from the Python process when it loads this Linux shared object.
void *calloc(size_t count, size_t size);
void free(void *pointer);
void *memset(void *destination, int value, size_t size);

struct coverage {
    uint64_t lo;
    uint64_t hi;
    uint64_t *table;
    size_t capacity;
    size_t count;
    int failed;
};

static size_t slot_for(uint64_t key, const uint64_t *table, size_t capacity)
{
    size_t slot = (size_t)((key ^ (key >> 32)) * UINT64_C(0x9e3779b97f4a7c15)) & (capacity - 1);
    while (table[slot] && table[slot] != key)
        slot = (slot + 1) & (capacity - 1);
    return slot;
}

static int grow(struct coverage *coverage)
{
    size_t capacity = coverage->capacity ? 2 * coverage->capacity : 128;
    uint64_t *table = calloc(capacity, sizeof(*table));
    if (!table)
        return 0;
    for (size_t i = 0; i < coverage->capacity; ++i) {
        uint64_t key = coverage->table[i];
        if (key)
            table[slot_for(key, table, capacity)] = key;
    }
    free(coverage->table);
    coverage->table = table;
    coverage->capacity = capacity;
    return 1;
}

struct coverage *coverage_new(void)
{
    struct coverage *coverage = calloc(1, sizeof(*coverage));
    if (coverage && !grow(coverage)) {
        free(coverage);
        return NULL;
    }
    return coverage;
}

void coverage_free(struct coverage *coverage)
{
    free(coverage->table);
    free(coverage);
}

void coverage_begin(struct coverage *coverage, uint64_t lo, uint64_t hi)
{
    coverage->lo = lo;
    coverage->hi = hi;
    coverage->count = 0;
    coverage->failed = 0;
    memset(coverage->table, 0, coverage->capacity * sizeof(*coverage->table));
}

void coverage_block(void *engine, uint64_t address, uint32_t size, void *user)
{
    (void)engine;
    struct coverage *coverage = user;
    if (address < coverage->lo || address >= coverage->hi || coverage->failed)
        return;
    // Use one key per (offset, size) pair, even when a block is translated at two sizes.
    uint64_t key = ((address - coverage->lo) << 32) + size + 1;
    size_t slot = slot_for(key, coverage->table, coverage->capacity);
    if (coverage->table[slot])
        return;
    if (coverage->count == coverage->capacity / 2) {
        if (!grow(coverage)) {
            coverage->failed = 1;
            return;
        }
        slot = slot_for(key, coverage->table, coverage->capacity);
    }
    coverage->table[slot] = key;
    ++coverage->count;
}

// Freeze collection before the replacement call. SIZE_MAX signals allocation failure.
size_t coverage_end(struct coverage *coverage)
{
    coverage->hi = 0;
    return coverage->failed ? SIZE_MAX : coverage->count;
}

void coverage_copy(const struct coverage *coverage, uint64_t *keys)
{
    for (size_t i = 0; i < coverage->capacity; ++i)
        if (coverage->table[i])
            *keys++ = coverage->table[i] - 1;
}
