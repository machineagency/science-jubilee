---
title: Lab Automation Deck
---

(lab-automation-deck)=
# Lab Automation Deck

```{figure} _static/deck.png
:scale: 50 %

Lab automation deck for Science Jubilee.
```

There is also a lab automation deck documented [on the Jubilee Wiki](https://jubilee3d.com/index.php?title=Lab_Automation_Plate). The deck attachment here is easier to build, requires less materials, and has slots off the build plate for disposal (e.g., sharps) containers. It also uses a flexure based design to accommodate slight labware heterogeneity. If you are working with more dangerous or expensive materials, the attachment on the Jubilee Wiki can provide greater stability.

## Parts to Buy

- [1/8" Delrin](https://www.onlinemetals.com/en/buy/plastic/0-125-acetal-sheet-homopolymer-delrin-natural/pid/6761)
- 12x M3* 12mm button head machine screws
- PLA for printing (just a few grams is enough)

## Parts to Fabricate

- Design files for the deck can be found [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/bed_plate/fabrication_files).  The `1-layer_deck_bottom.AI` and `1-layer_deck_top.AI` should be lasercut or water cut.  Please note that laser cutting Delrin releases formaldehyde, requiring proper ventilation.  Alternatively, services like [SendCutSend](http://sendcutsend.com) can produce these parts for about 80 USD

- Print 6 copies of the [bed plate coupler](https://github.com/machineagency/jubilee/tree/main/bed_plates/6x_well_plate_bed/fabrication_exports/stls) in PLA.  Use the [standard recommendations](https://jubilee3d.com/index.php?title=3D_Printed_Parts) of: *PLA + 0.4mm nozzle + No supports + 0.2mm layer height + 6 perimeter layers + 20% infill + outer perimeter layer first*

- Screw the pieces together using the machine screws (self-tapping, the design provided does not allow for insets). Pay attention to the alignment in the photograph above, and be sure to orient the "top" and "bottom" pieces relative to one another so that the flextures are oriented consistently.


## Duet Config Files

- The Jubilee homing routine needs to be adjusted to probe points on the platform, rather than the deck attachment. Find the updated config files [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/bed_plate/duet_config).
