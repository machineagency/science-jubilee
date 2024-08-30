---
title: Lab Automation Deck
---

(lab-automation-deck)=
# Lab Automation Deck

```{figure} _static/deck.png
:scale: 50 %

Lab automation deck for Science Jubilee.
```

The lab automation deck attachment allows you to repeatably and (somewhat) securely position [ANSI/SLAS standard footprint labware](https://www.slas.org/SLAS/assets/File/public/standards/ANSI_SLAS_1-2004_FootprintDimensions.pdf) on your Jubilee deck. This is a critical component for most experimental automation work with Jubilee. The automation deck attachment is cut from Delrin or Acetal. This attachment mounts to the Jubilee aluminum bed plate. Delrin flexures provides elastic positioning of labware. The deck holds up to 6 wellplates, with options to attach disposal (e.g., sharps) containers. 

## Versions
There are two versions of the automation deck attachment: a clamp-mount version and a screw mount version. The clamp-mount version uses 6 3D printed clasps that clamp around the perimeter of the bed. The screw-mount version uses 9 tapped holes in the bed to mount. The screw mount version is more secure and is less prone to warping. However, installing it requires access to a drill press, M3 tapping capabilities, and the willingness to put holes in your Jubilee bed. If you don't have any of these things, the clamp-mount version is for you. 

There is also a lab automation deck documented [on the Jubilee Wiki](https://jubilee3d.com/index.php?title=Lab_Automation_Plate). The deck attachment here is easier to build, requires less materials, and has slots off the build plate for disposal (e.g., sharps) containers. It also uses a flexure based design to accommodate slight labware heterogeneity. If you are working with more dangerous or expensive materials, the attachment on the Jubilee Wiki can provide greater stability.
## Material selection
Once you have selected a version, you also need to select a material thickness for the attachment. The attachment can be cut from either 1/8" or 1/4" acetal (generic copolymer) or Delrin (brand name, homopolymer). Either will work for the deck attachment. 1/4" material will be more robust and hold labware more securely. However, it may interfere with some labware and is harder to cut. If you have labware that does not comply with the SLAS footprint (85.48 x 127.76 mm) 1/4" above it's base but does at 1/8" above the base, use 1/8" material. If you have access to a laser cutter that will cut 1/8" material but not 1/4", get the 1/8" material. Otherwise, we recommend the 1/4" thickness. 

## Procuring an Automation Attachment
To procure an automation attachment, you can either have the part fabricated by an online service like SendCutSend, or cut the part yourself. For most academic labs without easy laser cutter access, purchasing the part from an online service is the better choice, as the overhead compared to purchasing the material is relatively small.


## Parts to Buy (if laser-cutting yourself)
- [1/8" or 1/4" Delrin](https://www.interstateplastics.com/Acetal-Plastic-Acetal-Copolymer-Natural-Color-Sheet-ACENE%7E%7ESH.php?sku=ACENE++SH&vid=20240830234117-9p&dim2=14&dim3=14&thickness=0.250&qty=1&recalculate.x=112&recalculate.y=31). This vendor will sell custom sized sheets of delrin. Buy a sheet slightly larger than the footprint of the attachment you are making. 

## Parts to Fabricate

### Attachment component files

Clamp mount version: [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/bed_plate/fabrication_files)

The clamp-mount version is split in half for compatability with smaller laser cutters and materials sourcing constraints. If you can find a large enough sheet of material and have a large laser cutter, the top and bottom can be combined and cut as a single part. 

Screw mount version:


## Duet Config Files

- The Jubilee homing routine needs to be adjusted to probe points on the platform, rather than the deck attachment. Find the updated config files [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/bed_plate/duet_config).
