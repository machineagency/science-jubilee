---
title: Setting Toool Offsets
---

(tool-offsets)=
# Setting Tool Offsets

Once you have defined your tool in the Duet config file and set [tool parking post positions](parking_posts.md), the last step in setting up a new tool is to set offsets. Tool offsets record the location of the 'active point' of the tool relative to the z-probe on the tool carriage, which is Jubilee's default reference point. Accurate offsets allows Jubilee to position each tool using the same coordinate system. For example, if your experiment involves pipetting reactants into a wellplate's 'A1' well, then recording the reaction in that well with a spectroscopy probe, accurate offsets will allow Jubilee to position both tools over the center of well A1. 

Offsets should be set in a config file called `toffsets.g`. Depending on how you initially set up your Jubilee, you may have tool offsets defined in config.g. We reccomend storing them in `toffsets.g`, because this allows you to update the tool offset values without restarting (and re-homing) your machine. This will make your life far easier if you are setting up multiple tools. 

To move to the `toffsets.g` format:
1. Remove the G
2 ...



## Skills and capabilities needed
- Interacting with Jubilee over Duet web control
- Editing gcode configuration files

## Equipment and supplies needed
- A tool, with parking post positions already set
- Some masking or label tape
- A fine-point pen


## Determine your tool's active point

The active point of the tool is the relevant reference point on the tool for the tool's functionality. For a pipette tool, this is the tip of the pipette barrel (without a tip attached). For a spectroscopy probe, this would be the optical tip. For a camera, this is likely the center of the field of view, but this will depend on the downstream software use. 

## Place an X on the Jubilee bed

Using the masking tape and a pen, draw and 'X' on the bed somewhere. This will be your reference point for calculating offsets. Position the 'X' such that the bed can be raised to touch the tool carriage without the lab automation deck plate interfering, and so that the active point of the tool can reach it. Beyond this, the exact position does not matter. 

## Prepare your toffsets.g file

Add your tool to the `toffsets.g` file, and zero out the offsets for now. If you are updating offsets on an existing tool, set the existing offsets to 0. This will make the math much easier later.

## Record 'X' position with Jubilee reference point

Record the location of the X relative to the Jubilee tool reference point, which is the z-axis limit switch. 

1. Make sure no tools are picked up or active
2. Position the tool carriage over the 'X' you marked
3. Carefully line up the tool carriage's Z axis limit switch over the X. This will require squinting and viewing the limit switch from different angles. A flashlight may be helpful as well. 
4. Record the X and Y position of the tool carriage for later use.

## Pick up your tool

:::{warning}
The bed will not automatically drop when you pick up the tool because you have not set up Z offsets yet. MAKE SURE TO DROP THE BED SO THAT IT CLEARS THE TOOL before picking up the tool.
:::

1. Drop the bed such that the tool will clear it when picked up
2. Pick up the tool by running the `T{toolindex}` command

## Position your tool over the 'X' 

- As before with the Jubilee z-axis limit switch, position the active point of your tool directly over the 'X' mark. The tool should be directly over the X. Raise the bed until it is just barely not touching the tip of the tool. 
- Record the XYZ position of the tool 

## Calculate tool offsets from recorded positions



## Update tool offsets 

## Verify offsets were set correctly




Placeholder for future tool offset tutorial
