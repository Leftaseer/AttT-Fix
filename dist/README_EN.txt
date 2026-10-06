AttTFix 1.1 — technical update for Ascension to the Throne
===========================================================

An unofficial, non-commercial mod for the Steam version of the game. No game files are
modified: the whole mod is a single dinput8.dll that the game loads by itself.


WHAT'S NEW IN 1.1
-----------------
  * Performance: no more heavy FPS drops with the sun on screen (the game stalled the GPU
    every frame to read one pixel), next to large rocks (slow obstacle test) and in dense
    forests.
  * Smooth particles: smoke, fire and magic move at your frame rate instead of 30 times
    per second.
  * 16x anisotropic filtering: ground, roads and walls are sharp in the distance.
  * MSAA anti-aliasing (optional, Ctrl+7) together with smooth foliage edges.
  * Doubled draw distance of small props (boxes, wheels, rocks), NPCs and their shadows:
    much less pop-in at modern resolutions.
  * In-game toggles (Ctrl+digit while the F11 overlay is shown) to compare with the original.
  * AttTFix_LAA.exe tool (optional): the game can use 4 GB of memory instead of 2 GB.


FEATURES
--------
Display and interface
  * Any modern resolution, including Full HD, 1440p and 4K, without a stretched picture.
    The resolution list in Options comes from your monitor, and the choice no longer resets.
  * Widescreen menus: centered in 4:3 with black bars on the sides.
    The in-game HUD stays full-screen, as in the original.
  * Fixed the Russian battle victory screen: the Gold and Experience lines no longer fall
    off the book.

Graphics
  * 16x anisotropic texture filtering.
  * MSAA 2x/4x/8x and foliage edge anti-aliasing (off by default, Ctrl+7).
  * Longer draw distance of small props and shadows (ObjectDistance=2).

Smoothness
  * Smooth movement of the hero, armies, battle units and the camera between the game's
    logic steps (the game updates the world 30 times per second). Removes the hero jitter
    when the camera turns.
  * Smooth character animations (30 frames per second in the original).
  * Particles are evaluated for the exact moment being rendered.
  * VSync also works in windowed mode, matched to the refresh rate of the monitor the game
    window is on.
  * FPS limit in Options: VSync, 30, 60, 90, 120, 144, 165, 240 or unlimited.

Performance
  * Sun / lens flare visibility test without stalling the GPU.
  * Forest trees without redundant render state save/restore.
  * Fast point-in-obstacle test (same result, no trigonometry per edge).

Stability and convenience
  * The game uses all CPU cores (the original pinned itself to one).
  * Fixed crashes: Alt-Tab in fullscreen, returning to the main menu.
  * Cursor and camera sensitivity in Options.
  * "Intro videos" checkbox in Options: the game starts in a couple of seconds.
  * Language choice, Russian or English (in Options, applied after a restart).
    The fullscreen checkbox is also available in the English version.
  * Starting from Steam opens the game directly, without the launcher (launcher.ini).
  * The mod version is shown in the bottom right corner of the main menu.


INSTALLATION
------------
1. Open the game folder: Steam -> Library -> Ascension to the Throne -> right click ->
   Manage -> Browse local files.
2. Copy dinput8.dll there (replace it when updating from 1.0).
3. (Optional) To start the game without the launcher, back up your launcher.ini and replace
   it with the launcher.ini from this archive. It differs from the original by a single
   line, skip=true, at the end.
4. (Optional) Copy AttTFix_LAA.exe to the game folder and run it once: the game gets 4 GB of
   memory instead of 2 GB (useful at 4K, required for DXVK, see below). It keeps a backup,
   ATThrone.exe.noLAA.bak; to undo run "AttTFix_LAA.exe /undo". Run it again after a Steam
   update of the game.
5. Start the game. A settings file, AttTFix.ini, is created next to it on the first start.
   The language is picked from your Windows language the first time and can be changed
   in Options.

Compatibility: Steam version 1.1.128. If some part of the game differs, the mod disables
that particular fix, writes a note to AttTFix.log, and the game keeps working.
Works together with mods that add their own Resource2.pak.


UNINSTALL
---------
Delete dinput8.dll, AttTFix.ini and the AttTFix*.log files from the game folder.
If you replaced launcher.ini, restore your copy or remove the line skip=true from it.
If you ran AttTFix_LAA.exe, run "AttTFix_LAA.exe /undo" (or verify the game files in Steam:
Properties -> Installed Files -> Verify integrity).


HOTKEYS
-------
  F11 — show/hide the FPS counter and the toggle panel in the top left corner.
  While it is shown (digits with Ctrl held are not passed to the game):
    Ctrl+1 — movement and camera smoothing
    Ctrl+2 — character animation smoothing
    Ctrl+3 — object animation smoothing
    Ctrl+4 — optimizations (sun, trees, obstacle test)
    Ctrl+5 — particle smoothing
    Ctrl+6 — anisotropic filtering
    Ctrl+7 — MSAA and foliage anti-aliasing (short pause while the screen is re-created)
    Ctrl+9 — longer draw distance of props and shadows
  F10 / F9 / F7 — same as Ctrl+1 / Ctrl+2 / Ctrl+4.


SETTINGS (AttTFix.ini)
----------------------
Most things are set in the game's Options. The rest is in AttTFix.ini (a text file,
changes apply on the next start):

  [UI]     Widescreen=1        1 = menus centered in 4:3, 0 = original stretched menus
  [Video]  VSync=1             vertical sync
           FpsLimit=0          FPS limit when VSync=0 (0 = unlimited)
           SkipIntro=0         1 = skip the startup videos
           Anisotropy=16       anisotropic filtering 2/4/8/16 (0 = off)
           MSAA=0              anti-aliasing at start 2/4/8 (0 = off, Ctrl+7 = 4x)
           AlphaToCoverage=1   with MSAA also smooth foliage edges
           ObjectDistance=2.0  draw distance of small props and shadows (1.0 = original)
           Renderer=d3d9       d3d9 or dxvk (see below)
           WindowedSync=dwm    VSync in a window: dwm (monitor-locked), flush or timer
           AllCores=1          use all CPU cores
  [Mouse]  CursorSpeed, CameraSpeed   cursor and camera sensitivity
  [Smooth] Interpolate=1       movement smoothing
           Animation=1         animation smoothing
           Objects=1           object animation smoothing
           Particles=1         particle smoothing
  [Perf]   AsyncSunCheck=1, TreeBatch=1, FastPolygonTest=1   optimizations (0 = original)
           ShowFps=0           FPS counter at start (F11 toggles it)
           Log=0               1 = write performance statistics to AttTFix_perf.log
  [Game]   Language=en         ru or en


DXVK (OPTIONAL)
---------------
DXVK translates Direct3D 9 to Vulkan; on some systems it gives more FPS. Not included.
1. Run AttTFix_LAA.exe (without it DXVK runs out of memory at high resolutions).
2. Download DXVK (https://github.com/doitsujin/dxvk/releases) and put x32\d3d9.dll from its
   archive into a "dxvk" subfolder of the game folder (dxvk\d3d9.dll).
3. Set [Video] Renderer=dxvk in AttTFix.ini. To go back: Renderer=d3d9.
The active renderer is shown in the F11 counter (D3D9 or DXVK).


TROUBLESHOOTING
---------------
The mod keeps a log in AttTFix.log (the previous run is in AttTFix.prev.log). After a crash
a .dmp dump file is saved next to it. To check whether the mod is the cause, rename
dinput8.dll and start the game again. Individual features can be switched off with the
toggles (F11 + Ctrl+digit) or in AttTFix.ini.
