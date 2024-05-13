---
title: Color Mixing Demonstration Setup Guide
---

(color-mixing-setup)=
# Color Mixing Demonstration Setup Guide

## Introduction

This is a guide to configuring a Jubilee to run [the color mixing demo](https://github.com/pozzo-research-group/jubilee_pipette_BOdemo).

While this guide is specific to this experiment, many steps detailed here are transferable to other experiments. The related config files and Jupyter notebooks could be used as templates to set up new experiments.

This guide is a work in progress. Contact bgpelkie [at] uw dot edu with questions.

## Prerequisites

This guide assumes you have:
1. A correctly assembled Jubilee motion platform with a lab automation deck plate, running a Duet 5 Mini Ethernet and Duet 3 expansion board.
2. A completed Opentrons pipette tool.
3. A Raspberry Pi-based WebCamera tool with a ring light.

## Steps

1. Update the Duet config.g file with the associated example file.
2. Wire everything according to the wiring guide.
3. Make sure everything homes without crashing.
4. Set tool parking post positions.
5. Set tool offsets.
6. Perform deck calibration.
7. Perform manual labware offset calibration for small labware items (e.g., 96 well plates and tipracks).
8. Run the color mixing demonstration notebook.
