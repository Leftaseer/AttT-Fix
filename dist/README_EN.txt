AttTFix 1.2 — technical update for Ascension to the Throne
===========================================================

An unofficial, non-commercial mod for the Steam version of the game. No game files are
modified: the whole mod is a single dinput8.dll that the game loads by itself.


WHAT'S NEW IN 1.2
-----------------
  * Its own graphics settings page: Options -> video -> the "ATTTFIX" button next to the
    title. Presets and individual settings (see "GRAPHICS SETTINGS" below).
  * Direct3D 9 / DXVK renderer switch right in Options (applies after a restart).
  * Much lighter forests: 3D trees are drawn only up to the chosen distance (1500 by
    default), flat trees beyond. Most of the gain shows with the forest distance set to
    "Very far".
  * With DXVK identical trees are drawn in one call (hardware instancing), and effects
    restore render states only when something actually needs them: noticeably more FPS
    in dense forests and towns.
  * Faster: visible tree sort, skeletal model skinning (SSE, checked against the original
    while playing), 3D sound on a worker thread (up to ~13% of a battle frame before),
    fewer effect state changes.
  * The game can keep running while minimized or unfocused ([Game] Background=1, off by
    default).
  * The Windows cursor no longer stays on top of the game after start.
  * Fixed: "spinning" model parts on some units (e.g. the Slaver's boots) with animation
    smoothing; an open portal twitching at the end of its animation loop; broken tree
    distances in saved settings (the game could save a negative or an extra distance).
  * Distant trees fade without the see-through look (dissolve, Ctrl+8).
  * The prop distance is original (1.0) by default; raise it with a preset or its own
    setting.


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
  * Anisotropic texture filtering up to 16x.
  * MSAA 2x/4x/8x and foliage edge anti-aliasing (off by default).
  * Adjustable draw distance of small props, NPCs and their shadows.
  * Adjustable distance of 3D trees, and a dissolve instead of the see-through fade
    between 3D and flat trees.

Smoothness
  * Smooth movement of the hero, armies, battle units and the camera between the game's
    logic steps (the game updates the world 30 times per second). Removes the hero jitter
    when the camera turns.
  * Smooth character animations (30 frames per second in the original).
  * Smooth object animations (foliage, water, flags).
  * Particles are evaluated for the exact moment being rendered.
  * VSync also works in windowed mode, matched to the refresh rate of the monitor the game
    window is on.
  * FPS limit in Options: VSync, 30, 60, 90, 120, 144, 165, 240 or unlimited.

Performance
  * Sun / lens flare visibility test without stalling the GPU.
  * Forest trees: no redundant render state save/restore, trunks and crowns in groups,
    fast sort; hardware instancing with DXVK.
  * Effects change only the render states that actually differ (with DXVK they also
    restore them lazily).
  * Fast skeletal skinning, 3D sound on a worker thread.
  * Fast point-in-obstacle test (same result, no trigonometry per edge).

Stability and convenience
  * The game uses all CPU cores (the original pinned itself to one).
  * Fixed crashes: Alt-Tab in fullscreen, returning to the main menu.
  * Cursor and camera sensitivity in Options.
  * "Intro videos" checkbox in Options: the game starts in a couple of seconds.
  * Language choice, Russian or English (in Options, applied after a restart).
    The fullscreen checkbox is also available in the English version.
  * Optional background mode ([Game] Background=1).
  * Starting from Steam opens the game directly, without the launcher (launcher.ini).
  * The mod version is shown in the bottom right corner of the main menu.


INSTALLATION
------------
1. Open the game folder: Steam -> Library -> Ascension to the Throne -> right click ->
   Manage -> Browse local files.
2. Copy dinput8.dll there (replace it when updating).
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

Updating from 1.1: you can keep AttTFix.ini. If it has ObjectDistance=2.0 from the old
version, the prop distance stays extended; change it on the new page.

Compatibility: Steam version 1.1.128. If some part of the game differs, the mod disables
that particular fix, writes a note to AttTFix.log, and the game keeps working.
Works together with mods that add their own Resource2.pak.


UNINSTALL
---------
Delete dinput8.dll, AttTFix.ini and the AttTFix*.log files from the game folder.
If you replaced launcher.ini, restore your copy or remove the line skip=true from it.
If you ran AttTFix_LAA.exe, run "AttTFix_LAA.exe /undo" (or verify the game files in Steam:
Properties -> Installed Files -> Verify integrity).


GRAPHICS SETTINGS ("ATTTFIX" page in Options -> video)
------------------------------------------------------
  Graphics quality — a preset; "Custom" is shown once any setting is changed by hand.
                     Props   Aniso  MSAA  3D trees
      Original       x1.0    off    off   as in the game
      Recommended    x1.0    16x    off   up to 1500   (default)
      Medium         x1.5    16x    off   up to 2000
      High           x2.0    16x    off   up to 2500
      Ultra          x3.0    16x    4x    up to 4000
  Object and shadow distance — multiplier for small props, NPCs and shadows.
  Forest distance — the same setting as "Tree distance" on the left of the video page:
                     how far trees are seen at all. Saved with Apply.
  Distance of 3D trees — a DISTANCE, not a number of trees: closer trees are 3D, further
                     ones are flat pictures. Higher = nicer up close, but heavier.
                     "As in the game" follows the forest distance (at "Very far" the game
                     keeps 3D trees up to about 700).
  Tree 3D -> 2D transition — see-through (original), dissolve or short dissolve.
  Anisotropic filtering — off / 2x / 4x / 8x / 16x.
  Anti-aliasing (MSAA) — off / 2x / 4x / 8x. With the system Direct3D 9 after a restart,
                     with DXVK at once.
  Renderer — Direct3D 9 or DXVK (after a restart; needs AttTFix_LAA.exe and dxvk\d3d9.dll).
Except for the forest distance and the renderer, everything applies at once and is saved
to AttTFix.ini.


HOTKEYS
-------
  F11 — show/hide the FPS counter and the toggle panel in the top left corner.
  While it is shown (digits with Ctrl held are not passed to the game):
    Ctrl+1 — movement and camera smoothing
    Ctrl+2 — character animation smoothing
    Ctrl+3 — object animation smoothing
    Ctrl+4 — optimizations (sun, trees, obstacles, effects, sound, skinning)
    Ctrl+5 — particle smoothing
    Ctrl+6 — anisotropic filtering
    Ctrl+7 — MSAA and foliage anti-aliasing (DXVK: at once, Direct3D 9: after a restart)
    Ctrl+8 — distant tree transition: dissolve / short dissolve / original
    Ctrl+9 — extended draw distance (props, shadows, trees) / original
    Ctrl+0 — write one frame to AttTFix.log (debugging)
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
           MSAA=0              anti-aliasing at start 2/4/8 (0 = off)
           AlphaToCoverage=1   with MSAA also smooth foliage edges
           ObjectDistance=1.0  draw distance of small props and shadows (1.0 = original)
           Tree3DDistance=1500 distance up to which trees are 3D (0 = as in the game)
           TreeDistance=1.0    3D -> flat crossfade multiplier (with Tree3DDistance=0)
           TreeDissolve=1      0 = see-through (original), 1 = dissolve, 2 = short dissolve
           Renderer=d3d9       d3d9 or dxvk (see below)
           WindowedSync=dwm    VSync in a window: dwm (monitor-locked), flush or timer
           AllCores=1          use all CPU cores
  [Mouse]  CursorSpeed, CameraSpeed   cursor and camera sensitivity
  [Smooth] Interpolate=1       movement smoothing
           Animation=1         animation smoothing
           Objects=1           object animation smoothing
           Particles=1         particle smoothing
  [Perf]   AsyncSunCheck, TreeBatch, TreeGroupParts, TreeInstancing, TreeSort,
           EffectStates, EffectDeferRestore, FastSkin, AsyncSound, FastPolygonTest
                               optimizations, all =1 (0 = original)
           ShowFps=0           FPS counter at start (F11 toggles it)
           Log=0               1 = write performance statistics to AttTFix_perf.log
  [Game]   Language=en         ru or en
           Background=0        1 = the game keeps running (and playing sound) when minimized
           BackgroundFps=30    FPS limit in the background (0 = unlimited)


DXVK (OPTIONAL)
---------------
DXVK translates Direct3D 9 to Vulkan; it usually gives noticeably more FPS, and in 1.2 the
tree instancing and the lazy state restore work only with it. Not included.
1. Run AttTFix_LAA.exe (without it DXVK runs out of memory at high resolutions).
2. Download DXVK (https://github.com/doitsujin/dxvk/releases) and put x32\d3d9.dll from its
   archive into a "dxvk" subfolder of the game folder (dxvk\d3d9.dll).
3. In Options -> "ATTTFIX" pick the DXVK renderer and restart the game
   (or set [Video] Renderer=dxvk in AttTFix.ini). To go back: Direct3D 9.
The active renderer is shown in the F11 counter (D3D9 or DXVK).


TROUBLESHOOTING
---------------
The mod keeps a log in AttTFix.log (the previous run is in AttTFix.prev.log). After a crash
a .dmp dump file is saved next to it. To check whether the mod is the cause, rename
dinput8.dll and start the game again. Individual features can be switched off with the
toggles (F11 + Ctrl+digit) or in AttTFix.ini.
