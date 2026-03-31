# Deck Definition Files

This directory contains deck configuration files that describe the physical layout of
slots on a Science Jubilee deck.

## Directory structure

```
deck_definition/
  examples/   -- Reference deck configs shipped with the repository. Do not edit these.
  user/       -- Your personal deck configs go here. This folder is gitignored.
  README.md   -- This file.
```

## How to set up your deck config

Deck slot offsets are specific to your physical machine — they must be measured during
calibration and will differ from any example file.

The recommended workflow is:

1. Run the calibration notebook in `src/science_jubilee/calibration/` to generate a
   deck config for your machine.
2. Save the output JSON into `user/` with a descriptive name (e.g. `my_lab_deck.json`).
3. Load it when initializing a Deck:

```python
deck = machine.load_deck("my_lab_deck")
```

The code checks `user/` first, then falls back to `examples/`.

## Which fields require calibration?

The `offset` values for each slot are physically measured and machine-specific.
All other fields (`deck_type`, `deck_slots`, `material`) describe the hardware and
can be copied from an example.

## Backing up your deck config

Because `user/` is gitignored, your configs are **not** automatically saved by git.
See `tools/configs/README.md` for backup strategies (cloud sync, zip archive, or a
separate private git repository).
