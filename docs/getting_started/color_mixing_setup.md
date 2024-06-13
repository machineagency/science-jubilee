---
title: Color Mixing Demonstration Setup Guide
---

(color-mixing-setup)=
# Color Mixing Demonstration Setup Guide

## Introduction

This guide walks you through running the Pozzo research group's color mixing demonstration. The color mixing demonstration is a basic example of an autonomous experimentation platform or self driving lab. In a color mixing experiment, a system learns how to make a user-selected target color by mixing source primary colors in various ratios. In our implementation, we use diluted acrylic paint as primary source colors. A Bayesian optimization campaign optimizes toward a user-selected target color by varying the volume fraction of each primary color that is added to a sample. Samples are prepared with an OT2 pipette in a 96 well plate, and characterized using a raspberry pi camera.

While this guide is specific to this experiment, many steps detailed here are transferable to other experiments. The related config files and Jupyter notebooks could be used as templates to set up new experiments.

This guide is a work in progress. Contact bgpelkie [at] uw dot edu with questions.

You can find the instructions for running the color mix demo along with the code at [https://github.com/pozzo-research-group/jubilee_pipette_BOdemo](https://github.com/pozzo-research-group/jubilee_pipette_BOdemo)

## Required Equipment

To reproduce this tutorial exactly, you will need the following items. You should be able to substitute similar equipment with similar functionality, for example using a peristaltic pump dispensing tool instead of an OT2 pipette tool.

1. An assembled and provisioned Jubilee motion platform with a calibrated lab automation deck plate
2. An OT2 Pipette tool and webcamera tool on your Jubilee, with tool offsets and tool-specific calibrations completed.
3. Acrylic paint in red, yellow, blue, white, and black. No need for anything fancy here
4. A 96 well plate (~400 uL well volumes)
5. A 12 scintillation vial holder labware, printable from the [Pozzo group labware repo](https://github.com/pozzo-research-group/Automation-Hardware/tree/master/Vial%20Holders/20mlscintillation_12_wellplate_18000ul).
6. Opentrons tiprack, with tips, for your pipette tool
7. 5 20cc scintillation vials for holding paint stocks
