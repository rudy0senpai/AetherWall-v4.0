# AetherWall v4.0 Design

## Visual language

AetherWall v4.0 uses a dark sci-fi control-room aesthetic with violet/cyan/green adaptive accents. HUD surfaces are **bubble glass** rather than flat panels: a raised shadow layer, locally blurred wallpaper capture, translucent tint, bright rim and subtle highlight create the depth seen in the v4 reference.

## Desktop composition

All HUD coordinates are based on a 1600×900 reference grid:

- Brand/title: x 42–550, y 38–118
- Clock/date: x 1200–1530, y 58–205
- Circular meters: x 58–303, y 190–895
- System: x 1190–1530, y 250–555
- CPU history: x 770–1150, y 585–850
- AetherWall dock: x 285–1115, y 848–886

The QML layer scales this reference composition uniformly to preserve proportions and alignment.

## Reactive settings

Reactive controls are persisted in `~/.config/aetherwall/config.json`:

- Reactive HUD on/off
- Background blur on/off
- Blur intensity 0–100%
- Top title
- Clock & date
- System panel
- Circular meters
- CPU history graph
- Bottom dock

## Library

The library uses a bounded icon grid. The Rows slider supports 1, 2 or 3 rows, changing preview density without stretching the whole application window. FFmpeg is used to extract representative video frames.
