# AetherWall v3.7.1 — Fix 1

- Fixed startup crash: imported `QCheckBox` in the Qt widget imports.
- Fixed the installed launcher when launched from the source directory: it now changes to the installed application directory before importing `aetherwall`, preventing the source tree from shadowing the installed copy.
- Added a source-tree `run.sh` for deterministic launches.
