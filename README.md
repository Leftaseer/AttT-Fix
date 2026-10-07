# AttT-Fix

Unofficial technical update for **Ascension to the Throne / Восхождение на Трон** (Steam version 1.1.128):
modern resolutions and widescreen menus, smooth movement and animation, sharper textures and shadows,
MSAA, an optional Vulkan renderer (DXVK), large performance fixes and crash fixes.

The mod is a proxy `dinput8.dll` placed next to `ATThrone.exe` (plus an optional `dxvk` folder).
No game files are modified, and `[Mod] Enabled=0` in `AttTFix.ini` switches everything off.

[Русская версия ниже](#русский)

---

## Features

**Display and interface**
- Any resolution the monitor supports (Full HD, 1440p, 4K, …) without stretching; the list in Options comes from the monitor and the choice no longer resets.
- Menus on a centered 4:3 canvas; the in-game HUD stays full-screen as in the original.
- If the monitor refuses the chosen fullscreen mode (e.g. the default 1280x960 on a 4K screen), the game starts in a window instead of quitting.
- Language switch Russian / English, intro videos checkbox, cursor and camera sensitivity, fullscreen checkbox in the English build.

**Graphics**
- Anisotropic filtering up to 16x and mip levels for world textures: no grainy, shimmering ground far away (most visible with upscaled texture packs).
- MSAA 2x/4x/8x with anti-aliased foliage edges.
- Sharper sun shadows (up to 8192 with smoothed edges), sharper hero and NPC shadows that move smoothly, building shadows that no longer vanish.
- Adjustable draw distance of props and NPCs and of 3D forest trees; optional dissolve instead of the see-through tree fade.
- **"ATTTFIX" page** in Options → video: presets Original / Recommended / Medium / High / Ultra and each setting separately, including the renderer (Direct3D 9 / DXVK).

**Smoothness**
- The game updates the world 30 times per second; the mod smooths the hero, armies, battle units and the camera between those steps.
- Smooth character and object animations (30 fps in the original) and particles.
- VSync in a window locked to the monitor; FPS limit in Options, switched at once.

**Performance**
- Sun / lens flare test without stalling the GPU (looking at the sun at 4K: about 86 → 160+ FPS).
- Faster forests (grouped drawing, fast sorting, hardware instancing with DXVK), fewer effect state changes, SSE skinning, 3D sound on a worker thread, a fast obstacle test.
- Uses all CPU cores (the original pinned itself to one).
- Optional DXVK renderer (DXVK 3.1.1 included) with `AttTFix_LAA.exe` for 4 GB of memory. Before using it the mod checks for a Vulkan 1.3 GPU and falls back to Direct3D 9 with a message.

**Stability**
- Fixed crashes on Alt-Tab / lost device and on returning to the main menu; a failed device reset is retried.
- Works on switchable-graphics laptops where the system resets Direct3D hooks.
- Fixed: Windows cursor over the game, spinning model parts, portal flicker, broken tree distances in saved settings, pale options window after an MSAA change.

**Tools**
- F11: FPS, frame time, average FPS over 5 s and 1 min; a second press adds a toggle panel (Ctrl+digits).
- `[Mod] Baseline=1`: the original game with only the FPS counter, to compare performance.
- `[Perf] Log=1`: performance log (`AttTFix_perf.log`), with `Sampler=1` a sampling profiler.

## Installation

1. Download `AttTFix-1.3.2.zip` from [Releases](../../releases).
2. Open the game folder (Steam → right click the game → Manage → Browse local files) and copy `dinput8.dll` there.
3. Optional, for the DXVK renderer: run `AttTFix_LAA.exe` once in the game folder, copy the `dxvk` folder from the archive there, then pick DXVK in Options → "ATTTFIX".
4. Optional: back up your `launcher.ini` and replace it with the one from the archive to start without the launcher.
5. Start the game. `AttTFix.ini` is created on the first start; all settings are described in `dist/README_EN.txt`.

**Uninstall:** delete `dinput8.dll`, `AttTFix.ini` and the `dxvk` folder; run `AttTFix_LAA.exe /undo` if you used it (or verify the game files in Steam).

**Slow or old computer:** choose shadow quality "Original" on the "ATTTFIX" page and, without high-resolution textures, set `[Video] Mipmaps=0` for faster loading.

**Problems:** the mod writes `AttTFix.log` (the previous run is `AttTFix.prev.log`, a crash also leaves a `.dmp` file). Set `[Mod] Enabled=0` to check whether the mod is the cause.

## Building from source

Requirements: a 32-bit MinGW-w64 C++ compiler and Python 3 (`luac` 5.1 is optional, only a syntax check).

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

The result is `src/dinput8.dll`. `build.sh` converts `attfix.lua` (UTF-8) into `attfix_lua.h` (cp1251, the game's encoding), which is embedded into the DLL. `tools/laa.cpp` is the source of `AttTFix_LAA.exe`.

## Technical notes

- **Proxy DLL.** The game imports `dinput8.dll`; ours forwards `DirectInput8Create` to the system DLL and patches the game in memory. Every patch checks the original bytes first; on a different game build it is skipped and noted in the log.
- **Hooks.** IAT hooks (Direct3D 9 / D3DX creation, exception and exit handling, affinity), small detours, device vtable hooks (re-applied when a driver resets them), and rewrites of the frame (`0x44A9C0`), render (`0x44E480`) and fixed-step update (`0x424D90`) functions.
- **Lua bridge.** The game logic and GUI are Lua 5.1 scripts inside `.pak` archives. The DLL registers C functions in the game's Lua state and runs the embedded `attfix.lua` (options pages, widescreen layout, layout fixes).
- **Smoothing.** World matrices and skeletal key frames are replaced with interpolated values only while rendering and restored afterwards; the game logic is untouched.
- **Sources** (all included by `attfix.cpp`): `renderopt.inc` render optimizations and draw distances, `effectsm.inc` effect state manager, `instance.inc` tree instancing and the quality settings API, `billboard.inc` flat trees, `cpuopt.inc` tree sort, `skin.inc` + `skin_core.h` skinning, `sound.inc` async 3D sound, `smoothanim.inc` object and particle smoothing, `msaa.inc` MSAA, `shadow.inc` shadows, `mipmap.inc` + `dxt1mip.h` mip levels. `funcs_table.h` lists function addresses of `ATThrone.exe` for the profiler.
- **Tests:** `src/tests/skintest.cpp` (skinning against a reference), `src/tests/fxtest.cpp` (deferred state restore); `tools/perfsum.py <game folder>` summarizes `AttTFix_perf.log`.

No game code or assets are included in this repository. DXVK (https://github.com/doitsujin/dxvk) is distributed in the release archive unmodified under the zlib/libpng license.

---

## Русский

Неофициальное техническое обновление для **«Восхождение на Трон»** (Steam-версия 1.1.128): современные разрешения и широкоформатные меню, плавные движение и анимации, более чёткие текстуры и тени, MSAA, рендер Vulkan (DXVK) по желанию, заметный прирост производительности и исправления вылетов.

Мод — это файл `dinput8.dll` рядом с `ATThrone.exe` (и, по желанию, папка `dxvk`). Файлы игры не изменяются, а `[Mod] Enabled=0` в `AttTFix.ini` выключает всё.

### Возможности

**Экран и интерфейс**
- Любые разрешения монитора (Full HD, 1440p, 4K…) без растягивания; список в «Опциях» берётся с монитора, выбор больше не сбрасывается.
- Меню по центру в пропорциях 4:3; игровой интерфейс — на весь экран, как в оригинале.
- Если монитор не принимает выбранный полноэкранный режим (например, 1280x960 по умолчанию на 4K), игра запускается в окне, а не вылетает.
- Переключение языка (русский / английский), галочка «Заставки», чувствительность курсора и камеры, галочка полноэкранного режима в английской версии.

**Графика**
- Анизотропная фильтрация до 16x и мип-уровни для текстур мира: земля вдали не «зернит» и не мельтешит (особенно заметно с апскейлами текстур).
- MSAA 2x/4x/8x со сглаживанием краёв листвы.
- Чёткие тени от солнца (до 8192, со сглаженными краями), чёткие и плавные тени героя и NPC, тени зданий больше не пропадают.
- Настраиваемая дальность предметов и NPC и объёмных деревьев; растворение вместо просвечивания деревьев по желанию.
- **Страница «ATTTFIX»** в «Опциях» → видео: пресеты Оригинальное / Рекомендуемое / Среднее / Высокое / Ультра и каждый параметр отдельно, включая рендер (Direct3D 9 / DXVK).

**Плавность**
- Игра считает мир 30 раз в секунду; мод плавно ведёт героя, армии, юнитов в бою и камеру между этими шагами.
- Плавные анимации персонажей и объектов (30 к/с в оригинале) и частиц.
- VSync в окне по частоте монитора; ограничение FPS в «Опциях», переключается сразу.

**Производительность**
- Проверка солнца для бликов без остановки видеокарты (взгляд на солнце в 4K: примерно 86 → 160+ FPS).
- Более быстрые леса (отрисовка группами, быстрая сортировка, инстансинг с DXVK), меньше смен состояний в эффектах, SSE-скиннинг, 3D-звук в отдельном потоке, быстрая проверка препятствий.
- Используются все ядра процессора (оригинал привязывал себя к одному).
- Рендер DXVK по желанию (DXVK 3.1.1 в комплекте) вместе с `AttTFix_LAA.exe` для 4 ГБ памяти. Перед запуском мод проверяет поддержку Vulkan 1.3 и при её отсутствии запускает Direct3D 9 с пояснением.

**Стабильность**
- Исправлены вылеты при Alt-Tab / потере устройства и при выходе в главное меню; неудачный сброс устройства повторяется.
- Работает на ноутбуках с двумя видеокартами, где система сбрасывает подключение мода к Direct3D.
- Исправлено: курсор Windows поверх игры, «крутящиеся» части моделей, мерцание порталов, испорченные дальности деревьев в настройках, блёклое окно опций после смены MSAA.

**Инструменты**
- F11: FPS, время кадра, средний FPS за 5 с и 1 мин; повторное нажатие — панель переключателей (Ctrl+цифры).
- `[Mod] Baseline=1`: оригинальная игра только со счётчиком FPS — для сравнения производительности.
- `[Perf] Log=1`: журнал производительности (`AttTFix_perf.log`), с `Sampler=1` — профайлер.

### Установка

1. Скачайте `AttTFix-1.3.2.zip` в разделе [Releases](../../releases).
2. Откройте папку игры (Steam → правой кнопкой по игре → «Управление» → «Просмотреть локальные файлы») и скопируйте туда `dinput8.dll`.
3. Необязательно, для рендера DXVK: запустите один раз `AttTFix_LAA.exe` в папке игры, скопируйте туда папку `dxvk` из архива и выберите DXVK в «Опциях» → «ATTTFIX».
4. Необязательно: сохраните свой `launcher.ini` и замените его файлом из архива, чтобы игра запускалась без лаунчера.
5. Запустите игру. `AttTFix.ini` появится при первом запуске; все настройки описаны в `dist/README_RU.txt`.

**Удаление:** удалите `dinput8.dll`, `AttTFix.ini` и папку `dxvk`; если запускали `AttTFix_LAA.exe` — выполните `AttTFix_LAA.exe /undo` (или проверьте файлы игры в Steam).

**Слабый или старый компьютер:** выберите «Качество теней» = «Оригинал» на странице «ATTTFIX» и, если не используете текстуры высокого разрешения, поставьте `[Video] Mipmaps=0` — загрузка будет быстрее.

**Если что-то не так:** мод пишет журнал `AttTFix.log` (предыдущий запуск — `AttTFix.prev.log`, при вылете рядом сохраняется `.dmp`). Чтобы проверить, виноват ли мод, поставьте `[Mod] Enabled=0`.

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

Готовый файл — `src/dinput8.dll`. `build.sh` переводит `attfix.lua` (UTF-8) в `attfix_lua.h` (cp1251, кодировка игры), который встраивается в DLL. Исходник `AttTFix_LAA.exe` — `tools/laa.cpp`. Устройство мода описано в разделе [Technical notes](#technical-notes).

Код и ресурсы игры в репозитории не содержатся. DXVK (https://github.com/doitsujin/dxvk) входит в архив релиза без изменений, лицензия zlib/libpng.
