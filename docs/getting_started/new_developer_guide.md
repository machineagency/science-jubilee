---
title: Getting Started as a New Jubilee Developer
---

# Getting Started as a New Jubilee Developer

This page provides a general overview of the Jubilee ecosystem with an eye towards getting a new contributor up to speed as a developer of Jubilee for science. This guide was developed as a resource to aid in the onboarding of new students in the Pozzo research group, but can serve as a useful reference for anyone new to Jubilee. If you are using a Jubilee as a tool in your research in collaboration with an established Jubilee user, following this guide verbatim may be unnecessarily involved. However if you are starting from scratch with Jubilee, you will need to follow all the steps here to get a functional experiment up and running. 

## What is Jubilee?

To lift directly from the Jubilee wiki, ["Jubilee is an extensible multi-tool motion platform capable of running G-code for low force automation applications."](https://jubilee3d.com/index.php?title=Main_Page). Jubilee is originally developed and configured as a tool-changing 3D printer. Tool changing 3D printers use multiple hot-swappable extruder heads to allow them to print with multiple colors or materials. Jubilee is a great platform for experimental automation because the tool changing capability makes it possible to run multi-step experimental workflows on a single platform without moving samples manually. The open, extensible nature of the platform also makes it reasonably straightforward to develop new tools or capabilities. However, because Jubilee is an open-source system, the user is responsible for many aspects of building and running the system. This lends Jubilee a steep learning curve compared to other automation platforms. This guide provides a pathway to flatten that learning curve.

## Where to find help? 

Because Jubilee is many things to many people, information on the platform is spread across several locations. 

- The Jubilee wiki page [https://jubilee3d.com/index.php?title=Main_Page](https://jubilee3d.com/index.php?title=Main_Page) is the official website of the Jubilee project. You will find instructions for [building the core motion platform](https://jubilee3d.com/index.php?title=Assembly_Instructions) and configuring it as a 3D printer here. 
- Jubilee as a 3D printer has a large and active community. The [Jubilee discord](https://discord.gg/RxMaGJdGH9) is the best spot to interact with this community. (Open a github issue on science_jubilee if this link is broken)
- The people behind science-jubilee host an Open Source Lab Automation discord server. Join at [https://discord.gg/ubxU2rMJwN](https://discord.gg/ubxU2rMJwN). 
- Jubilee uses a commercial motion control board called Duet as its brains. For software, configuration, or wiring issues, start at the [Duet documentation](https://docs.duet3d.com/).


## Prerequisites

This guide assumes you have a few things:

### Hardware:

1. A Jubilee motion platform, either assembled or still in the box (in the box is better!). You can purchase a Jubilee kit from [filastruder](https://www.filastruder.com/collections/jubilee/products/jubilee-motion-platform-kit) or assemble the requisite parts from the [bill of materials](https://jubilee3d.com/index.php?title=Getting_Parts). If it is an option, buying the Filastruder kit is likely to be the most cost effective option, doubly so if you value your time in any way. These directions assume you are running a Duet 3 mini ethernet main board and a Duet3 3HC expansion board, but other options will work too. 
2. A [lab automation bed plate](https://github.com/machineagency/science-jubilee/tree/main/tool_library/bed_plate).
3. Hardware to run the color mixing demo. This includes an [Opentrons pipette tool](https://github.com/machineagency/science-jubilee/tree/main/tool_library/OT2_pipette) or other liquid handling tool as well as a downward-facing camera such as the [webcamera tool](https://github.com/machineagency/science-jubilee/tree/main/tool_library/webcamera).
4. An ethernet cable and means to plug it into your computer. Modern laptops will probably require and adapter. 

### Software:

1. A computer with python installed, preferably via a conda environment
2. A science-jubilee duet configuration fileset. 

### Tools:

1. A set of precision screwdrivers with hex and torx bits. We like the [Mako driver kit](https://www.ifixit.com/products/mako-driver-kit-64-precision-bits) from iFixit.
2. A set of metric hex L keys
3. #2 phillips screwdriver
4. Flush-cut clippers for zip ties 
5. Most tool builds will require 3D printing parts on a filament printer. You will not need this for the motion platform build if you buy the full kit.
6. Most tool builds will also require making electrical connections through soldering and crimping. You will not need to do this for the motion platform build if you buy the full kit.


## 1. Assemble and configure the motion platform

Estimated time: 8 hours - 5 working days

### Hardware assembly

This is a time consuming process, but it is well worth investing this time as this gets you familiar with the platform. Once you build it, you can understand issues and fix them. New developers in our research group are handed a partially disassembled Jubilee as their first task during the onboarding process. The build process is well documented on the [Jubilee3D wiki](https://jubilee3d.com/index.php?title=Assembly_Instructions). Most of the content for science-jubilee assumes you have a working motion platform and doesn't cover this step. 

### Wiring

We have a wiring [quickstart diagram](https://github.com/machineagency/science-jubilee/blob/main/docs/pdfs/jubilee_wiring_colormix.pdf) to wire the boards for our 'default' lab automation configuration. Ignore the connections for the pipette and camera for now. This wiring setup is based off of the [duet3 mini wiring diagram](https://raw.githubusercontent.com/machineagency/jubilee/main/frame/assembly_instructions/wiring/duet3_mini/duet3_mini_frame_wiring.png) from the Jubilee wiki, but may differ slightly. 

### Board provisioning and initial connection

You will need to set up configuration files on the duet board to connect to it. First, you will need a bootable microSD card for your Duet. It probably came with a pre-configured SD card in the box. If not, follow the directions at [https://docs.duet3d.com/User_manual/RepRapFirmware/SD_card](https://docs.duet3d.com/User_manual/RepRapFirmware/SD_card) to set one up from scratch.

Setting up g-code configuration files for Jubilee takes a fair amount of sorcery and dark magic. If possible, We recommend starting from our functional configuration file and modifying it to fit your needs. This config hasn't been shared yet. In the meantime DM one of us to get it. 

You will also need to set up your computer's network settings to access Jubilee over a direct ethernet connection. There is a great [write-up](https://jubilee3d.com/index.php?title=Connecting_to_Jubilee) of this process on the Jubilee wiki. 

If you have done everything correctly, now you are ready to connect to the machine and home it for the first time! Open a web browser and enter the ip address you assigned Jubilee. In our config this is `192.168.1.2`. You should connect to the Duet Web Control interface. This is a GUI interface for controlling the Duet boards on Jubilee. It is useful for editing configuration files on the Duet board, making manual machine movements, debugging, and incident recovery. 

```{figure} _static/duet_web_control.png

Screenshot of duet web control dashboard.
```

Now, you're ready to home the machine for the first time! Homing is a process the motion platform goes through to figure out where it is in space and make sure everything works. During the homing procedure, the machine will move each axis to it's 0 position (see [Jubilee coordinate system primer](primer.md)). You will need to home the machine every time you power it on. Before you proceed, make sure the bed is clear of everything, including the lab automation deck plate. To home the machine from the Duet Web Control interface, click the blue 'home all' button. The first time you home a new machine, expect something to go wrong. Watch the process carefully and keep a finger over the power switch if something goes wrong. There should be no crashing, shuddering, or grinding during this process.



## 2. Install and calibrate the lab automation deck plate


## 3. Build and install the tools you will be using 

For this tutorial, we need an OT2 pipette tool and webcamera tool

1. See the individual build guides to build, wire, and configure these tools
2. Set tool parking post positions and offsets for each tool
3. Test that they work

# 4. Control the tools with science-jubilee


# 5. Provision for and run the color mixing demonstration notebook

- Update the color mixing docs to have good instructions for this part, cut out the general setup guidelines from there. 