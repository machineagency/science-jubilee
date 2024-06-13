---
title: Lab Automation Deck Tutorial
---

(deck-guide)=
# Lab Automation Deck Tutorial

This guide walks you through the basics of using a lab automation deck in conjunction with labware. It assumes you have a lab automation deck installed on your machine. If you don't have a lab deck installed on your machine, check out the [deck build instructions](../building/lab_automation_deck.md)

The lab automation

## Creating a Deck Definition

The standard lab automation deck consists of 6 slots that accept and [ANSI/SLAS](https://www.slas.org/education/ansi-slas-microplate-standards/) standard microplate, or any piece of labware that adheres to the footprint dimensions of this standard.  (indices 0-5), and a number of optional garbage containers which can be positioned outside of the deck footprint:

```{figure} _static/plate.png
---
scale: 50%
alt: deck layout
---
A lab automation deck holding a 6-, 24-, and 96-well plate as well as a pipette tip rack and petri dish of duckweed. The 3D printed frame off the bed houses a sharps container.
```

```{figure} _static/deck_layout.png
---
scale: 50%
alt: deck layout
---
Orientation of slots on deck and labware in slots.
```

To use the lab automation deck, we need to set the offsets for each of the 6 slots, as well as any off-deck containers, and place the definition in the `decks/deck_definitions/` directory. The preferred method to do so accurately is with a camera tool; the [deck definition calibration notebook](https://github.com/machineagency/science-jubilee/blob/main/src/science_jubilee/calibration/LabAutomationDeckCalibration.ipynb) interactively guides you through this process. If you do not have a camera tool, this can also be done using any other tool that extends into the build volume such that you can accurately align the tool tip to a corner of each slot. Make sure to load the appropriate deck calibration file every time you set up an experiment (#TODO: Add a 'setting up an experiment' page that walks through how to set up with science-jubilee library).

You should not need to re-do the deck calibration often during normal usage. You will need to re-do the calibration if you disassemble the lab automation deck assembly (ie remove the delrin mask from the aluminum bed plate).

## Creating Labware Definitions

Each piece of labware requires a labware definition in `labware/labware_definitions`. This file contains accurate measurements and information about the dimensions, well positions, and more for your labware. Our format is identical to the [OpenTrons labware definitions](https://support.opentrons.com/s/article/What-is-a-labware-definition). If you have used an OpenTrons before, this means you can use any existing labware definitions you have with Jubilee. It also means you can use the Opentrons [Labware Designer](https://labware.opentrons.com/create/) to create custom definitions.

In general, labware is saved in the format `<brand>_<number_of_wells>_<labware_type>_<well_volume>_<extra_identifiers>.json`. For example, a Corning 96 well plate has the name `corning_96_wellplate_360ul_flat.json`; an OpenTrons pipette tip rack is named `opentrons_96_tiprack_300ul.json`. We recommend following this convention for specificity and for sharing experimental workflows.

## Labware Calibration

Due to tolerances in the deck plate, labware, and their interface, you will likely need to perform a manual offset calibration to get good location accuracy. This is mostly the case for smaller labware items like 96 well tipracks and well plates. Do this calibration after you have performed a deck definition calibration (described above) and selected a labware layout for your experiment. This calibration will correct for any translational or rotational deviations from the deck plate calibration.

**Note: This calibration will assume your wells are evenly spaced on your labware. If this is not the case, do not use this calibration. You instead may need to manually set a position for each individual well or adjust your deck definition coordinates**

1. Place your labware in the selected location on the deck plate.
2. Pick up a tool that has had its offsets correctly set. An OT2 pipette tool or other 'probe' tool is preferred for this step
3. Using the Duet Web Control interface jog controls, place the tool over the 'A1' well on the first piece of labware. Align the tool as precisely as you can, then write down the XY coordinates
4. Repeat step 3 for the ("first row, last column") and ("last row, last column") wells on the same piece of labware. In the example labware shown in the deck schematic above, this would be the 'A12' and 'H12' wells.
5. Repeat steps 3-4 for each of the labware items that need calibration.
5. When setting up the experiment in your python code, apply the recorded manual offset values to each piece of labware. Example code:

```
tiprack = jubilee.load_labware('opentrons_96_tiprack_300uL.json', 0) #Load an opentrons 300uL tiprack into deck slot 0
tiprack.manual_offset([[<A1 X coord., A1 Y coord>], [<A12 X coord, A12 Y coord>], [<H12 X coord, H12 Y coord>]], save=True)
```

The `save` keyword argument is optional. If True, the offsets will save to the labware definition json file, allowing you to load them directly from the file next time you use the labware.

## Using a Lab Automation Deck + Labware

We can use our deck + labware definitions in code. First, we need to import relevant modules:

```python
from science_jubilee.Machine import Machine
from science_jubilee.Decks import Deck
```

We can then load a deck onto the machine, and labware into the deck:

```python
m = Machine()
deck = m.load_deck("<my_deck_definition>")
labware = deck.load_labware("<my_labware_definition>")
```

Note that we can omit the `.json` file extension. Let's take an example using a 24-well plate. Each labware is made up of a number of `Well` objects. We can access information like size and location of each well by its row-column identification (A1, A2, ...) or its index (0, 1, ...), where index 0 corresponds to A1:

```python
labware = deck.load_labware("greiner_24_wellplate_3300ul", 1)
well = labware["A1"]  # Identical to labware[0]
```

The value of `well` for this labware is:

```python
Well(name='A1', depth=16.5, totalLiquidVolume=3300, shape='circular',
     diameter=16.28, xDimension=None, yDimension=None, x=175.13,
     y=79.3, z=2.5, offset=[160.0, 7.3])
```

The value of `offset` comes from your specific automation deck calibration, and is used to adjust the position of each well. All other information derives from your labware definition. We can access each attribute directly:

```python
well.x      # 175.13, the x position of the well center
well.y      # 79.3,   the y position of the well center
well.depth  # 16.5,   the usable depth of

 this well from the top of the labware
well.z      # 7.5,    the thickness of the labware plate
```
