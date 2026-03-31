# Tool Configuration Files

This directory contains configuration files for Science Jubilee tools.

## Directory structure

```
configs/
  examples/   -- Example configs shipped with the repository. Do not edit these.
  user/       -- Your personal configs go here. This folder is gitignored.
  README.md   -- This file.
```

## How to set up your configs

1. Find the example config for your tool in `examples/`.
2. Copy it into `user/` and give it any name you like.
3. Edit the values in `user/` to match your physical setup (see below).
4. Pass the filename when initializing a tool, e.g.:

```python
pipette = Pipette.from_config(index=0, name="p300", config_file="my_p300.json")
```

The code checks `user/` first, then falls back to `examples/`, so you can override
any example by placing a file with the same name in `user/`.

## Which fields need calibration?

Every setup is different. The fields below are specific to your machine and must be
measured/calibrated before use. All other fields are hardware specifications that
can be left at their example values.

| Tool | Fields requiring calibration |
|------|------------------------------|
| Pipette (P20, P300, P1000) | `zero_position`, `blowout_position`, `drop_tip_position`, `mm_to_ul` |
| Syringe | `min_range`, `max_range`, `mm_to_ml` |
| Camera / WebCamera | `ip_address`, `focus_height`, `image_folder` |
| HTTPSyringe | `url` |
| AS7341 | `port` (serial port path, e.g. `/dev/ttyUSB0`) |
| PeristalticPumps | `steps_per_ml` |

## Backing up your configs

Because `user/` is gitignored, your configs are **not** automatically saved by git.
We recommend one of the following:

- **Cloud sync** — move your `user/` folder into a Dropbox / Google Drive / OneDrive
  folder and symlink it here:
  ```
  ln -s ~/Dropbox/jubilee_configs user
  ```
- **Zip archive** — periodically zip the folder and save it somewhere safe:
  ```
  zip -r jubilee_configs_backup.zip user/
  ```
- **Separate git repo** — initialize a separate git repository inside `user/` and
  push it to a private GitHub repository. This gives you full version history of
  your calibration data.
