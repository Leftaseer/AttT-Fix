# AttT-Fix

Unofficial technical update for **Ascension to the Throne / Восхождение на Трон** (Steam version 1.1.128):
native modern resolutions, widescreen menus, smooth movement and animation, crash fixes, a language switch and more.

The whole mod is a single proxy `dinput8.dll` placed next to `ATThrone.exe`. No game files are modified.

[Русская версия ниже](#русский)

---

## What it changes

**Display and interface**
- Any resolution the monitor supports (Full HD, 1440p, 4K, …) without stretching; the Options list comes from the monitor and the choice no longer resets.
- Menus are laid out on a centered 4:3 canvas with black bars; the in-game HUD keeps the original full-screen layout.
- Fix for an original layout bug in the (Russian) battle victory window.

**Smoothness**
- The game updates the world at 30 Hz and never interpolated rendering. The mod blends positions of the hero, armies, battle units and the camera between logic steps (also removes the hero jitter while the camera turns).
- Character animations are blended between their 30 fps key frames (per bone, quaternion slerp for large changes).
- VSync in windowed mode, locked to the refresh rate of the monitor the window is on; FPS limit in Options.

**Stability and convenience**
- Uses all CPU cores (the original pins itself to core 0).
- Fixed crashes: Alt-Tab / lost device in fullscreen, returning to the main menu.
- Cursor and camera sensitivity in Options.
- "Intro videos" checkbox (skips 1C logo, logo and intro at start).
- Language switch Russian / English in Options (the English localization ships with the game as `Localization.pak`).
- Fullscreen checkbox restored in the English build.
- Optional: start from Steam without the Fulqrum launcher (`launcher.ini` with `skip=true`).
- On-screen FPS / frame-time overlay (F11), optional performance log and sampling profiler.

**Hotkeys:** F11 — FPS overlay, F10 — movement/camera smoothing on/off, F9 — animation smoothing on/off.

## Installing a release

1. Download `AttTFix-1.0.zip` from [Releases](../../releases).
2. Copy `dinput8.dll` into the game folder (Steam → right click the game → Manage → Browse local files).
3. Optional: back up your `launcher.ini` and replace it with the one from the archive to skip the launcher.
4. Start the game. Settings are created in `AttTFix.ini`; details are in `dist/README_EN.txt`.

To uninstall, delete `dinput8.dll` and `AttTFix.ini`.

## Building from source

Requirements: a 32-bit MinGW-w64 C++ compiler and Python 3 (`luac` 5.1 is optional, used only as a syntax check).

**Linux or WSL (Ubuntu / Debian):**
```sh
sudo apt install g++-mingw-w64-i686 python3 lua5.1
cd src
sh build.sh
```

**Windows with MSYS2:** open the *MSYS2 MINGW32* shell, then
```sh
pacman -S mingw-w64-i686-gcc python
cd src
CXX=g++ sh build.sh
```

The result is `src/dinput8.dll`. Copy it next to `ATThrone.exe`.
`build.sh` converts `attfix.lua` (UTF-8) into `attfix_lua.h` (cp1251, the game's encoding), which is embedded into the DLL.

### What next (development)

- Logs: `AttTFix.log` (always), `AttTFix_perf.log` with `[Perf] Log=1` (+ `Sampler=1` for the profiler, `TraceSeconds=N` for a per-frame trace, F8 for an animation trace).
- Every patch checks the original bytes first; on a different game build it is skipped and noted in the log.
- Ideas that are not done yet: smoothing for trees / town animations, LAA flag, render optimizations (trees and effect switching dominate the frame), optional DXVK renderer (`[Video] Renderer=dxvk` loads `dxvk\d3d9.dll` from the game folder).

## How it works (short)

- **Proxy DLL.** The game imports `dinput8.dll`; ours forwards `DirectInput8Create` to the system DLL and patches the game in memory at load time.
- **Hooks.** IAT hooks (Direct3D 9 creation, exception/exit handling, affinity, file opening), small detours and full rewrites of the frame (`0x44A9C0`) and render (`0x44E480`) functions, the fixed-step updater (`0x424D90`) and the skinned mesh draw calls.
- **Lua bridge.** The game logic and GUI are Lua 5.1 scripts inside `.pak` archives. The DLL registers C functions in the game's Lua state and runs the embedded `attfix.lua`, which patches the Options screen, the widescreen layout and a few original layout bugs.
- **Smoothing.** World matrices of moving objects and skeletal key frames are replaced with interpolated values only for the duration of rendering and restored afterwards, so the game logic is untouched.
- `funcs_table.h` is a list of function start addresses of `ATThrone.exe` (from Ghidra), used by the sampling profiler.

No game code or assets are included in this repository.

---

## Русский

Неофициальное техническое обновление для **«Восхождение на Трон»** (Steam-версия 1.1.128). Весь мод — один файл `dinput8.dll` рядом с `ATThrone.exe`, файлы игры не изменяются.

### Что меняется

**Экран и интерфейс**
- Любые разрешения монитора (Full HD, 1440p, 4K…) без растягивания; список в «Опциях» берётся с монитора, выбор больше не сбрасывается.
- Меню по центру в пропорциях 4:3 с чёрными полями, игровой интерфейс — как в оригинале.
- Исправлено окно победы: строки «Золото» и «Опыт» больше не уезжают за край.

**Плавность**
- Игра считает мир 30 раз в секунду и не сглаживала картинку. Мод плавно ведёт героя, армии, юнитов в бою и камеру между шагами логики (заодно убрано дрожание героя при повороте камеры).
- Анимации персонажей сглаживаются между ключевыми кадрами (30 к/с в оригинале).
- VSync в оконном режиме по частоте монитора, на котором окно; ограничение FPS в «Опциях».

**Стабильность и удобство**
- Используются все ядра процессора (оригинал привязывал себя к одному).
- Исправлены вылеты: Alt-Tab в полноэкранном режиме, выход в главное меню.
- Чувствительность курсора и камеры в «Опциях».
- Галочка «Заставки при запуске».
- Переключение языка: русский / английский (английская локализация уже лежит в игре как `Localization.pak`).
- Галочка полноэкранного режима возвращена в английскую версию.
- Необязательно: запуск из Steam без лаунчера (`launcher.ini` со строкой `skip=true`).
- Счётчик FPS (F11), журнал производительности и профайлер по желанию.

**Клавиши:** F11 — счётчик FPS, F10 — сглаживание движения и камеры, F9 — сглаживание анимаций.

### Установка

1. Скачайте `AttTFix-1.0.zip` в разделе [Releases](../../releases).
2. Скопируйте `dinput8.dll` в папку игры (Steam → правой кнопкой по игре → «Управление» → «Просмотреть локальные файлы»).
3. Необязательно: сохраните свой `launcher.ini` и замените его файлом из архива, чтобы игра запускалась без лаунчера.
4. Запустите игру. Настройки появятся в `AttTFix.ini`, подробности — в `dist/README_RU.txt`.

Удаление: удалите `dinput8.dll` и `AttTFix.ini`.

### Сборка из исходников

Нужны 32-битный компилятор MinGW-w64 и Python 3 (`luac` 5.1 — по желанию, только для проверки синтаксиса).

**Linux или WSL (Ubuntu / Debian):**
```sh
sudo apt install g++-mingw-w64-i686 python3 lua5.1
cd src
sh build.sh
```

**Windows с MSYS2:** откройте оболочку *MSYS2 MINGW32* и выполните
```sh
pacman -S mingw-w64-i686-gcc python
cd src
CXX=g++ sh build.sh
```

Готовый файл — `src/dinput8.dll`, его нужно положить рядом с `ATThrone.exe`.
`build.sh` переводит `attfix.lua` (UTF-8) в `attfix_lua.h` (cp1251, кодировка игры), который встраивается в DLL.

### Что дальше

- Журналы: `AttTFix.log` (всегда), `AttTFix_perf.log` при `[Perf] Log=1` (`Sampler=1` — профайлер, `TraceSeconds=N` — покадровый след, F8 — запись анимации).
- Каждая правка сначала сверяет исходные байты игры; на другой сборке игры она пропускается с записью в журнал.
- Не сделано: сглаживание деревьев и городских анимаций, флаг LAA, оптимизация рендера, DXVK как опция (`[Video] Renderer=dxvk` загружает `dxvk\d3d9.dll` из папки игры).

Код и ресурсы игры в репозитории не содержатся.
