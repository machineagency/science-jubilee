.. _color_mixing_setup:

**************************************
Color Mixing Demonstration Setup Guide
**************************************

Last Edited: Brenden, 2024.05.08

Introduction:
=============
This is a guide to configuring a Jubilee to run the color mixing demo (link to pozzorg color mixing demo repo goes here)

While this guide is specific to this experiment, many steps detailed here are transferrable to other experiments. The related config files and jupyter notebooks could be used as templates to set up new experiments.

This guide is a work in progress. Contact bgpelkie [at] uw dot edu with questions. 

Prerequisites
=============

This guide assumes you have: 
1. A correctly assembled Jubilee motion platform with a lab automation deck plate, running a duet 5 mini ethernet and duet 3 expansion board 
2. A completed opentrons pipette tool
3. A Raspberry pi-based WebCamera tool with a ring light 

Steps 
=====
1. Update the duet config.g file with the associated example file
2. Wire everything according to the wiring guide
3. Make sure everything homes without crashing 
4. Set tool parking post positions
5. Set tool offsets
6. Perform deck calibration 
7. perform manual labware offset calibration for small labware items (ie 96 well plates and tipracks)
8. Run color mixing demonstration notebook. 
