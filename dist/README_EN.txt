AttTFix 1.0 — technical update for Ascension to the Throne
===========================================================

An unofficial, non-commercial mod for the Steam version of the game. No game files are
modified: the whole mod is a single dinput8.dll that the game loads by itself.


FEATURES
--------
Display and interface
  * Any modern resolution, including Full HD, 1440p and 4K, without a stretched picture.
    The resolution list in Options comes from your monitor, and the choice no longer resets.
  * Widescreen menus: centered in 4:3 with black bars on the sides.
    The in-game HUD stays full-screen, as in the original.
  * Fixed the Russian battle victory screen: the Gold and Experience lines no longer fall
    off the book.

Smoothness
  * Smooth movement of the hero, armies, battle units and the camera between the game's
    logic steps (the game updates the world 30 times per second). Removes the hero jitter
    when the camera turns.
  * Smooth character animations (30 frames per second in the original).
  * VSync also works in windowed mode, matched to the refresh rate of the monitor the game
    window is on.
  * FPS limit in Options: VSync, 30, 60, 90, 120, 144, 165, 240 or unlimited.

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
2. Copy dinput8.dll there.
3. (Optional) To start the game without the launcher, back up your launcher.ini and replace
   it with the launcher.ini from this archive. It differs from the original by a single
   line, skip=true, at the end.
4. Start the game. A settings file, AttTFix.ini, is created next to it on the first start.
   The language is picked from your Windows language the first time and can be changed
   in Options.

Compatibility: Steam version 1.1.128. If some part of the game differs, the mod disables
that particular fix, writes a note to AttTFix.log, and the game keeps working.
Works together with mods that add their own Resource2.pak.


UNINSTALL
---------
Delete dinput8.dll, AttTFix.ini and the AttTFix*.log files from the game folder.
If you replaced launcher.ini, restore your copy or remove the line skip=true from it.


HOTKEYS
-------
  F11 — show/hide the FPS counter in the top left corner
  F10 — movement and camera smoothing on/off (to compare with the original)
  F9  — animation smoothing on/off


SETTINGS (AttTFix.ini)
----------------------
Most things are set in the game's Options. The rest is in AttTFix.ini (a text file,
changes apply on the next start):

  [UI]     Widescreen=1        1 = menus centered in 4:3, 0 = original stretched menus
  [Video]  VSync=1             vertical sync
           FpsLimit=0          FPS limit when VSync=0 (0 = unlimited)
           SkipIntro=0         1 = skip the startup videos
           WindowedSync=dwm    VSync in a window: dwm (monitor-locked), flush or timer
           AllCores=1          use all CPU cores
  [Mouse]  CursorSpeed, CameraSpeed   cursor and camera sensitivity
  [Smooth] Interpolate=1       movement smoothing (F10)
           Animation=1         animation smoothing (F9)
  [Game]   Language=en         ru or en
  [Perf]   ShowFps=0           FPS counter at start (F11 toggles it)
           Log=0               1 = write performance statistics to AttTFix_perf.log


TROUBLESHOOTING
---------------
The mod keeps a log in AttTFix.log (the previous run is in AttTFix.prev.log). After a crash
a .dmp dump file is saved next to it. To check whether the mod is the cause, rename
dinput8.dll and start the game again.
