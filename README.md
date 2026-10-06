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
- Particles (smoke, fire, magic) are evaluated at the exact rendered moment instead of the 30 Hz tick (the game's own analytic particle formulas).
- Vertex-tweened objects (foliage, water, flags) are drawn at the fractional frame when such animations are present.
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

**Performance**
- Sun / lens flare visibility test without a GPU stall. The original locked the whole back buffer twice per frame
  whenever the sun was on screen (33 MB copied per lock at 4K); now one pixel is copied and read 2-3 frames later.
  Looking towards the sun on the world map: about 86 → 160+ FPS (D3D9), 200+ FPS with DXVK.
- Forest trees: no per-tree render state save/restore (exact emulation through an effect state manager).
- Obstacle point-in-polygon test without two atan2 per edge (same result): standing next to a large rock dropped to ~45 FPS, now unaffected.
- Optional Large Address Aware tool (`AttTFix_LAA.exe`, from `tools/laa.cpp`): 4 GB of address space instead of 2 GB.
  Required for the optional DXVK renderer (`[Video] Renderer=dxvk` loads `dxvk\d3d9.dll` from the game folder).

**Hotkeys:** F11 — overlay. While it is shown: Ctrl+1 movement/camera smoothing, Ctrl+2 character animation, Ctrl+3 object animation, Ctrl+4 optimizations, Ctrl+5 particles (the digits are hidden from the game while Ctrl is held). F10 / F9 / F7 still work.

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
- `src/renderopt.inc` holds the optimizations, `src/smoothanim.inc` object/particle smoothing (both included by `attfix.cpp`); `[Perf] AsyncSunCheck` / `TreeBatch` / `FastPolygonTest`, `[Smooth] Objects` / `Particles` switch them off individually.
- Ideas that are not done yet: smoothing for trees / town animations, instanced drawing of trees, fewer effect switches.

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
- Частицы (дым, огонь, магия) считаются на момент отрисовки, а не 30 раз в секунду (по собственным формулам игры).
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

**Производительность**
- Проверка видимости солнца для бликов без остановки видеокарты. Оригинал, когда солнце в кадре, дважды за кадр
  блокировал весь экранный буфер (на 4K — копия 33 МБ); теперь копируется один пиксель и читается через 2–3 кадра.
  Взгляд в сторону солнца на карте мира: примерно 86 → 160+ FPS (D3D9), 200+ FPS с DXVK.
- Деревья леса рисуются без сохранения и восстановления состояний рендера для каждого дерева (точная эмуляция).
- Проверка «точка внутри препятствия» без двух atan2 на каждое ребро (тот же результат): у большого камня FPS падал до ~45, теперь нет.
- Утилита `AttTFix_LAA.exe` (`tools/laa.cpp`): 4 ГБ адресного пространства вместо 2 ГБ. Нужна для DXVK (`[Video] Renderer=dxvk`).

**Клавиши:** F11 — оверлей. Пока он открыт: Ctrl+1 движение и камера, Ctrl+2 анимации персонажей, Ctrl+3 анимации объектов, Ctrl+4 оптимизации, Ctrl+5 частицы (цифры с Ctrl игре не передаются). F10 / F9 / F7 тоже работают.

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
- Не сделано: сглаживание деревьев и городских анимаций, отрисовка деревьев инстансингом, меньше переключений эффектов.

Код и ресурсы игры в репозитории не содержатся.
