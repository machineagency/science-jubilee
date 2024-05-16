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

## Parts to Fabricate

- Design files for the deck can be found [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/bed_plate/fabrication_files).

## Duet Config Files

- The Jubilee homing routine needs to be adjusted to probe points on the platform, rather than the deck attachment. Find the updated config files [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/bed_plate/duet_config).
