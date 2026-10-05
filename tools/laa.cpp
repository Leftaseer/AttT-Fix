// AttTFix_LAA: sets (or with /undo clears) the Large Address Aware flag in ATThrone.exe.
// A 32-bit game with this flag gets 4 GB of address space on 64-bit Windows instead of 2 GB.
// The original file is backed up once as ATThrone.exe.noLAA.bak. The PE checksum is recalculated.
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <stdlib.h>

static DWORD PeChecksum(const BYTE* d, DWORD n, DWORD csOff) {
    unsigned long long s = 0;
    for (DWORD i = 0; i + 1 < n; i += 2) {
        if (i == csOff || i == csOff + 2) continue;
        s += (DWORD)d[i] | ((DWORD)d[i + 1] << 8);
        s = (s & 0xffff) + (s >> 16);
    }
    if (n & 1) { s += d[n - 1]; s = (s & 0xffff) + (s >> 16); }
    s = (s & 0xffff) + (s >> 16);
    return (DWORD)(s + n);
}

static int Finish(int code) {
    printf("\nPress Enter / Нажмите Enter...");
    getchar();
    return code;
}

int main(int argc, char** argv) {
    SetConsoleOutputCP(CP_UTF8);
    bool undo = false; const char* path = nullptr;
    for (int i = 1; i < argc; ++i) {
        if (!_stricmp(argv[i], "/undo") || !_stricmp(argv[i], "-undo") || !_stricmp(argv[i], "--undo")) undo = true;
        else path = argv[i];
    }
    char exe[MAX_PATH];
    if (path) snprintf(exe, sizeof exe, "%s", path);
    else {
        GetModuleFileNameA(nullptr, exe, MAX_PATH);
        char* s = strrchr(exe, '\\'); if (s) s[1] = 0; else exe[0] = 0;
        strncat(exe, "ATThrone.exe", sizeof exe - strlen(exe) - 1);
    }
    printf("AttTFix LAA tool\nFile / Файл: %s\n\n", exe);

    FILE* f = fopen(exe, "rb");
    if (!f) { printf("ATThrone.exe not found. Put this tool into the game folder.\n"
                    "ATThrone.exe не найден. Положите утилиту в папку игры.\n"); return Finish(1); }
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    BYTE* d = (BYTE*)malloc(n);
    if (!d || fread(d, 1, n, f) != (size_t)n) { fclose(f); printf("Read error / Ошибка чтения\n"); return Finish(1); }
    fclose(f);

    if (n < 0x200 || d[0] != 'M' || d[1] != 'Z') { printf("Not an executable / Это не exe-файл\n"); return Finish(1); }
    DWORD pe = *(DWORD*)(d + 0x3C);
    if (pe + 0x60 > (DWORD)n || memcmp(d + pe, "PE\0\0", 4)) { printf("Not a PE file / Это не PE-файл\n"); return Finish(1); }
    IMAGE_FILE_HEADER* fh = (IMAGE_FILE_HEADER*)(d + pe + 4);
    if (fh->Machine != IMAGE_FILE_MACHINE_I386) { printf("Not a 32-bit exe / Это не 32-битный exe\n"); return Finish(1); }
    DWORD csOff = pe + 4 + sizeof(IMAGE_FILE_HEADER) + offsetof(IMAGE_OPTIONAL_HEADER32, CheckSum);

    bool laa = (fh->Characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE) != 0;
    if (!undo && laa) { printf("Already enabled: the game can use 4 GB.\nУже включено: игре доступно 4 ГБ.\n"); return Finish(0); }
    if (undo && !laa) { printf("Already disabled (original 2 GB).\nУже выключено (оригинальные 2 ГБ).\n"); return Finish(0); }

    if (!undo) {
        char bak[MAX_PATH]; snprintf(bak, sizeof bak, "%s.noLAA.bak", exe);
        if (GetFileAttributesA(bak) == INVALID_FILE_ATTRIBUTES) {
            if (!CopyFileA(exe, bak, TRUE)) { printf("Could not create the backup %s (error %lu)\nНе удалось создать копию\n", bak, GetLastError()); return Finish(1); }
            printf("Backup / Копия: %s\n", bak);
        }
        fh->Characteristics |= IMAGE_FILE_LARGE_ADDRESS_AWARE;
    } else {
        fh->Characteristics &= ~IMAGE_FILE_LARGE_ADDRESS_AWARE;
    }
    *(DWORD*)(d + csOff) = PeChecksum(d, (DWORD)n, csOff);

    f = fopen(exe, "r+b");
    if (!f) { printf("Cannot write ATThrone.exe — close the game and try again.\n"
                    "Не удаётся записать ATThrone.exe — закройте игру и попробуйте снова.\n"); return Finish(1); }
    fseek(f, pe + 4, SEEK_SET); fwrite(fh, sizeof(IMAGE_FILE_HEADER), 1, f);
    fseek(f, csOff, SEEK_SET); fwrite(d + csOff, 4, 1, f);
    fclose(f);
    if (!undo) printf("Done: Large Address Aware enabled, the game can now use 4 GB of memory.\n"
                      "Готово: флаг LAA включён, игре теперь доступно 4 ГБ памяти.\n"
                      "Undo / Отменить: AttTFix_LAA.exe /undo\n");
    else printf("Done: LAA disabled (original 2 GB).\nГотово: флаг LAA выключен (оригинальные 2 ГБ).\n");
    return Finish(0);
}
