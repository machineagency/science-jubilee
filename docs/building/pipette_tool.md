---
title: Pipette Tool
---

(pipette-tool)=
# Pipette Tool

The pipette tool mounts an [Opentrons OT2 pipette](https://opentrons.com/products/single-channel-electronic-pipette-p20) to Jubilee to perform liquid handling with disposable pipette tips. Opentrons OT2 pipettes are available in three volume ranges (up to 20 uL, up to 300 uL, and up to 1000 uL) and have a form factor that is amenable to integrating with Jubilee. Many automation-focused labs already have an OT2 and hence OT2 pipettes. This tool provides a way to repurpose them on Jubilee. Compared to syringe-based liquid handling tools, these pipettes avoid the possibility of sample cross contamination and provides options for greater accuracy and precision at low transfer volumes. The tool consists of a mounting bracket to attach the pipette to a tool changer plate, a flexure mechanism that enables pipette tip pickups, and a wiring harness to control the pipette's internal motor. We have been able to reproduce the accuracy and precision values [published by Opentrons](https://opentrons.com.cn/wp-content/uploads/2023/11/Opentrons-Pipettes-White-Paper.pdf) for their pipettes after performing a gravimetric calibration. Choose the OT2 pipette tool if you need disposable pipette tips for your workflow or you need the pipette's accuracy at low volumes. Consider other liquid handling tools if the cost of the pipette is prohibitive, you need access to a wider range of volumes, or you are purchasing pipettes from scratch. While this is an effective pipette tool, due to the high cost and limited feature set of OT2 pipettes we don't recommend that new users purchase them specifically for working with Jubilee. New users should consider a syringe based tool as a starting point. If you do need a true disposable tip pipette, the [Open Lab Automata project](https://www.openlabautomata.xyz/) is developing an open hardware option - keep an eye on them for progress updates. We also are considering alternative commercial solutions and are happy to discuss these more if they are of interest to you.

:::{danger}
Using an OT2 pipette on Jubilee is obviously outside the design and support scope of Opentrons, so do so at your own risk. The Jubilee project further does not guarantee the safety or reliability of the OT2 piptte tool adaptation (or any other component of the Jubilee platform). There is a risk of destroying a pipette with an incorrectly configured machine (ask me how I know this...) so move slow and verify everything is set up correctly. 
:::

```{figure} _static/pipette-flexure.jpg
:scale: 50 %

Back of the pipette tool showing the flexure mechanism. When the pipette experiences resistance (i.e., pressing it against a pipette tip to pick it up), the flexure mechanism compresses until an endstop is triggered.
```

```{figure} _static/pickup.gif
:scale: 40 %

Pipette tool picking up a tip. When the flexure mechanism shown above reaches the endstop, the pipette tool considers the tip to have been picked up and resumes other tasks.
```

## Parts to Buy

- OT-2 Pipette (tested with gen1 and gen2)
- See the shopping list for tool parts [here](https://docs.google.com/spreadsheets/d/1Bp4ZdpHsX01EHIsc5mqbzi92CpQlax4KNS-QtPmUZUM/edit#gid=1582949094).

## Parts to Fabricate

- Pipette tool frame SolidWorks file and correctly sized parking posts can be found [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/OT2_pipette).

## Assembly Instructions

There are two version to choose from.

- [Version using only 3D printed parts](https://github.com/machineagency/science-jubilee/blob/main/tool_library/OT2_pipette/assembly_docs/OT2_Pipette_3D_only_assembly_instructions.pdf)
  - [*Purchase this endstop](https://www.digikey.ca/en/products/detail/e-switch/SS0750301F020P1A/2639077)
- [Version using 3D printed parts and a laser-cut flexible delrin part](https://github.com/machineagency/science-jubilee/blob/main/tool_library/OT2_pipette/assembly_docs/OT_laser_cut_assembly_instructions.pdf)

## Electronics

- [Wiring Diagram](https://github.com/machineagency/science-jubilee/blob/main/tool_library/OT2_pipette/assembly_docs/OT2_Wiring_Diagram.pdf)

## Duet Configuration

- Instructions [here](https://github.com/machineagency/science-jubilee/blob/main/tool_library/OT2_pipette/duet_configs/OT2_Pipette_Configuration.md)

## Media

<iframe width="708.75" height="398.25" src="https://www.youtube.com/embed/meaXhH14zzY?si=4p9Iwl6hgjO9En3n" title="Assembling the 3D printed only version of the OT2 pipette" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

<iframe width="354.375" height="630"
src="https://www.youtube.com/embed/pMmDV9pAfZU"
title="Assembling tool post"
frameborder="0"
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
allowfullscreen></iframe>

<iframe width="354.375" height="630"
src="https://www.youtube.com/embed/0mGqOwAkS5k"
title="Arbor press"
frameborder="0"
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
allowfullscreen></iframe>

<iframe width="354.375" height="630"
src="https://www.youtube.com/embed/F8c2MbFglJU?mute=1"
title="First tool loaded"
frameborder="0"
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
allowfullscreen></iframe>
