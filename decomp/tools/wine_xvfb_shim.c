/* Xvfb alone loads this shim. Wine and test programs do not load it.
 * The extracted Ubuntu Xvfb hardcodes /usr/bin/xkbcomp; redirect that helper
 * into XKB_BINDIR without changing host files. Xvfb runs with TCP and normal
 * Unix listeners disabled, retaining its authenticated abstract Unix socket. */
extern void *dlsym(void *, const char *);
extern char *getenv(const char *);
extern char *strstr(const char *, const char *);
extern unsigned long strlen(const char *);
extern void *memcpy(void *, const void *, unsigned long);

int execl(const char *file, const char *first, ...)
{
    typedef int (*execv_fn)(const char *, char *const *);
    execv_fn original = (execv_fn)dlsym((void *)-1L, "execv");
    char *args[32];
    char command[4096];
    __builtin_va_list ap;
    __builtin_va_start(ap, first);
    args[0] = (char *)first;
    unsigned n = 1;
    while (n < 31 && (args[n] = __builtin_va_arg(ap, char *))) n++;
    args[n] = 0;
    __builtin_va_end(ap);
    const char *directory = getenv("XKB_BINDIR");
    if (directory) for (unsigned i = 0; i < n; i++) {
        const char *match = strstr(args[i], "/usr/bin/xkbcomp");
        if (match) {
            unsigned long before = match - args[i], length = strlen(directory), rest = strlen(match + 8);
            if (before + length + rest + 1 < sizeof(command)) {
                memcpy(command, args[i], before);
                memcpy(command + before, directory, length);
                memcpy(command + before + length, match + 8, rest + 1);
                args[i] = command;
            }
            break;
        }
    }
    return original(file, args);
}
