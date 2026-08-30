# AetherWall v4.0.0 — Reactive Wallpaper Engine

AetherWall v4.0 is the next major release of the native KDE Plasma 6 wallpaper project.

## v4.0 highlights

- **Bubble-glass HUD:** every persistent HUD card uses raised, rounded bubble-glass depth, local frosted capture and glossy highlights.
- **Adaptive colour:** per-region contrast and accent adaptation from the active image/video wallpaper remains enabled.
- **CPU average temperature:** the telemetry service reads available hardware temperature sensors and exposes their average to the HUD and widget.
- **Aligned HUD geometry:** the desktop HUD uses a fixed 1600×900 reference composition so title, clock, meters, system panel, graph and bottom dock stay aligned instead of drifting with aspect ratio.
- **Image + video wallpaper plugins:** static images use `org.aetherwall.wallpaper`; videos use `org.aetherwall.video` and Qt Multimedia.
- **Video previews:** FFmpeg generates real preview frames for video cards in the library.
- **1–3 row library:** the wallpaper library keeps a bounded preview grid and lets the user change density from 1 to 3 rows.
- **Reactive controls:** enable/disable the HUD, toggle background blur, change blur intensity and independently show/hide each HUD region.
- **Plasma widget:** `org.aetherwall.widget` is installable as a normal Plasma widget through the widget manager. It shows CPU, RAM, battery, CPU average temperature, power state and clock.
- **Application icon:** the supplied AetherWall icon is installed as the application icon and desktop launcher icon.
- **Fixed navigation:** Library, Favorites, Reactive, Performance, Setup and Diagnostics remain independent pages.

## Install on CachyOS / Arch Linux

```bash
chmod +x install.sh
./install.sh
```

Then run:

```bash
aetherwall
```

The installer installs the required runtime packages, creates the isolated Python environment, installs both Plasma wallpaper plugins, installs the Plasma widget, registers the supplied application icon, creates a desktop launcher and enables the user telemetry service.

## Add the widget

After installation, open the KDE Plasma desktop's **Edit Mode → Add Widgets** and search for **AetherWall Reactive HUD**. Add it to the desktop or panel and resize it like a normal widget.

If the widget does not appear immediately, restart Plasma or log out/in once so the Plasma package cache is rebuilt.

## Notes

- CPU temperature depends on hardware sensors exposed by the Linux kernel. If no sensor is available, AetherWall displays `N/A` instead of inventing a value.
- Video audio is muted by default.
- AetherWall never executes wallpaper files as programs.
- The AetherWall bottom dock is separate from the user's KDE panel/dock.
