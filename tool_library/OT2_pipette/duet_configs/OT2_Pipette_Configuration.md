# Opentrons OT-2: Pipette Tool G-code Configuration

A relatively verbose summary of the duet configuration for an OT-2 toolhead.
These lines should be added to the `config.g` on *your* machine.


> Note:
> 1. Anywhere you see `<>`, you should remove the greater than/less than signs and replace them with the correct information based on *your* machine.
> 2. Be careful where you add the g-code lines in your `config.g` file as the order in which they are defined matters! You'll find information on where to add each one below.
>
>For more information about G-code, see the  [Duet G-code Documentation](https://docs.duet3d.com/en/User_manual/Reference/Gcodes) or the [RepRap G-code Wiki](https://reprap.org/wiki/G-code).
___
## 1. Set Drive Mapping

    M584 V<your_drive_number>

This command defines a new axis for the pipette motor and tells the Duet which board driver number you're using.
We use the *V* axis here; however, if it is already in use on your machine, you can also use *W/A/B/C*. Each driver on the Duet boards are labeled (e.g., `driver_0`,`driver_1`, etc.). Add the driver number (`n`) here and preped it with `1.n` if you are using an expansion board.

This G-code line shuold be placed the `M584` commands for your other axes in your `config.g` file. It has to come before all the other `M codes` we’ll add next.

> **Example**:
>
>     `M584 V1.2` ; pipette plugged into driver 2 on the expansion board
>     `M584 V0`   ; pipette plugged into driver 0 on the main board

## 2. Set Stepper Direction

    M569 P<your_drive_number> S0

This command sets the stepper motor direction. The `P` field should match the M584 command above. The `S` field can be either 0 or 1.
Add this command alongside the `M569` commands for your other motors in your configuration file.

The **first time** you home the pipette, you should check the direction that the motor is moving by removing the front plate and watching the draft shaft move.
During a homing step, it shold move towards the *endstop*. If it is moviong in the wrong direction (i.e., downwards), **manually** engage the endstop (i.e., click it!) and change the `S` parameter on this line from 0 to 1. Try again and make sure the motor moves in the expected direction.

> **Example**:
>
>     `M569 P1.2 S0 `

## 3. Set Motor Current

    M906 V<peak_current_in_milliamps>

This commands sets the peak motor current.
* For *Gen1* pipettes this shuold be **350** mA
* For *Gen2* pipettes this should be **500** mA
Add this command alongside the othe `M906` for the other moto5rs defined in your configuration file.

> **Example**:
>
>     `M906 V350` ; 350mA peak current for gen1 pipette
>     `M906 V500` ; 500mA peak current for gen2 pipette

## 4. Set Stepper Direction

    M92 V<steps_per_mm>
    M350 V16 I1

Set the number of steps/mm and enables *16x* microstepping with interpolation.
* For *Gen1* pipettes this should be **48**
* For *Gen2* Pipettes this should be **200**
Add these commands alongside the other `M92` and `M350` commands in your `config.g` file.

> **Example**:
>
>     `M92 V48`    ; for a gen1 single channel pipette
>     `M92 V200`   ; for a gen2 single channel pipette
>     `M350 V16 I1` ; set microstepping after M92 command
>
> Note: do not disable microstepping prior to define the `M92` command for the pipette motor to simplify calculations as it will mess with the motor settings (not sure why)

## 5. Set V Axis Motion Attribute Limits
    M201 V800
    M203 V10000
    M566 V4000

These commands set the max acceleration (`M201`), speed (`M203`) and jerk (`M566``) for the V axis.
Add these command alongside the M201/203/566 commands in your configuration file.

## 6. Configure Endstop

    M574 V1 S1 P"^<your_pin_name>"

This command configures the endstop for the **internal** axis limit switch. Note that the carat ("^") should be included to enable the pullup resistor; the quotes (" ") are necessary.
Pins are named as `<board_index>.<pin>.in`. The *pin* number can be found on your Duet board.
Add this command alongside the other `M574` commands.

> **Example** :
>
>     `M574 V1 S1 P"^0.io3.in"` ; pipette endstop plugged into io3 on main board

## 7. Define Tool
    M563 P<tool_number> S”<tool_name>”

This command actually defines your tool. The tool number should be set based on the other tools you already have defined, and you can name your tool whatever human-readable text you’d like to see it as in Duet Web Control. Note that, because we are using the *V axis*, we do not need to add a `D` field here (as we might for a syringe or extruder tool).

> **Example**:
>
>     `M563 P1 SP300 Pipette”` ; pipette with tool index 1

## 8. Define Pipette Tip Endstop

    M574 Z1 P"^<your_pin_name>"

This command is to define the external endstop for picking up pipette tips.
In this case,  it will be an enstop for the *Z axis* instead of the pipette axis (*V*). Similarly to section 6, the carat ("^")and the quotes (" ") are necessary in thsi line as well.
Again, pins are named as follows `<board_index>.<pin>.in`.
Add this command alongside the other `M574` commands

> **Example**:
>
>     `M574 Z1 P"^0.io2.in` ; pipette top pick up endstop plugged into io2 on main board

## 8. Define Homing Macro
You are now done with updating your `config.g` file!
 Next, you'll need to define the homing routing for the pipette. In the *Duet Web Control*, navigate to *System* (i.e., *sys/*), then add a *New File* and name it `homev.g`.
 Add the following content to it:

    G91              ; relative moves
    G1 V-200 F800 H1 ; big, slow negative move to look for endstop
    G1 V1 F600       ; back off endstop
    G1 V-10 F600 H1  ; find endstop again, slower
    G90              ; absolute moves
    G1 V0.5 F600     ; move to a position of 0.5 to start

**Remember**: The *first time* you home the pipette, you should check the direction of the mototr movement and ensure the draft shaft is moving upwards towardsthe endstop. If you notice the pipette tip ejector starts to engage, then manually stop the motion by pressing the endstop twice (to account for both searches for the endstop in the homing routine), and flip the direction of the motor (see step 2.)

## 9. Add V Homing to `homeall.g`

The `homeall.g` macro is used to home each of the machine's configured axis at once. You can call the `homev.g` macro at the end of this file, and the pipette will home while sitting in its parking position.To do so, navigate to *System* (i.e., *sys/*), open `homeall.g`, and add the following line to the end:

    M98 P"homev.g"

You are now done and your pipette should be configured!
