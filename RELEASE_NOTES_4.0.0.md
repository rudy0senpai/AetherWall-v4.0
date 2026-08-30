# AetherWall v4.0.0

## Major release

v4.0 moves the project from the flat/frosted v3 HUD treatment to a consistent bubble-glass visual system and adds CPU average temperature plus a first-class Plasma widget.

### HUD
- Bubble-glass cards with local frosted wallpaper capture.
- Consistent 1600×900 reference geometry for alignment.
- CPU, RAM and battery circular meters remain on the left.
- Clock remains upper-right.
- System card remains right-aligned and now includes CPU average temperature.
- CPU history remains lower-center/right.
- Bottom AetherWall dock remains independent of the KDE panel.

### Telemetry
- Added `cpu_temp` to the telemetry payload.
- Temperature is the arithmetic mean of available `psutil.sensors_temperatures()` readings.
- Missing temperature sensors produce `null` and the UI displays `N/A`.

### Widget
- Added Plasma 6 widget package: `org.aetherwall.widget`.
- Resizable compact bubble-glass system HUD.
- Reads the same localhost telemetry endpoint as the wallpaper HUD.

### Packaging
- Version bumped to 4.0.0.
- Supplied AetherWall PNG is installed as the application icon.
- Added `.desktop` launcher.
- Installer now deploys the Plasma widget.
