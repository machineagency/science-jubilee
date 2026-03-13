---
title: Software Setup
---

(software)=
# Software Setup

By default, the Duet 3 hardware supports a [limited set of HTTP commands](https://github.com/Duet3D/RepRapFirmware/wiki/HTTP-requests).  Connecting a [Raspberry Pi](https://www.raspberrypi.com) single board computer (ACT) to act as an interface between the outside world and the Duet hardware  enables extended HTTP functionality, which we will use in several ways.  First, it exposes a web-based interface for controlling the machine.  Second, the Science Jubilee `Machine` software library makes use of an extended HTTP functionality available in SBC mode.  Third, some of the tools, such as the camera, are controlled by USB; the Raspberry Pi can integrate these alongside the control capabilities of the Duet hardware.


## Raspberry Pi SBC 

1. Follow the [Duet3 SBC setup instructions](https://docs.duet3d.com/User_manual/Machine_configuration/SBC_setup) to setup the Raspberry Pi system image, connect it to the Duet3 board, and perform basic hello-world. 
    - **Note:** The Duet Mini comes with an 16GB SD card in the slot, so there is no need to buy an additional one.  However be sure to remove the SD card from the Duet board regardless of whether you use it or not.  
    - (*Aside:* If your Filastruder kit is missing the SBC connector cable (which should have been included with the Duet 3...), this is just a [standard 40pin to 26 pin downgrade cable](https://amzn.to/4eanvkN); they also [sell them as one-offs](https://www.filastruder.com/products/duet-3-to-raspberry-pi-ribbon-cable)).  


**Philosophical decision:** We will assume that you are running the Raspberry Pi in "headless" (no keyboard, no monitor) mode and log into it remotely via SSH; if that is the case, you should choose the "Lite" version, which avoids the GUI portions of the operating system.  The instructions below assume that you will be logging in remotely to the machine

**Suggested customization:** I suggest that you edit the user configurations in the Raspberry Pi imaginer.  Name your device (e.g. `jubilee`), create a username (e.g., `jubilee`) and password, enable SSH access, and enable WiFi by providing an access point and password (if desired).

(In principle, during this setup you should also be able to configure the Raspberry Pi to [use the USB-C port as a network interface](https://learn.adafruit.com/turning-your-raspberry-pi-zero-into-a-usb-gadget/ethernet-gadget) instead of needing a separate network connector.  However, some [other trickery is needed with the Raspberry Pi 5](https://github.com/verxion/RaspberryPi/blob/main/Pi5-ethernet-and-power-over-usbc.md))

2. Connect to your Raspberry Pi and in a command-line terminal update the operating system and install git (the software update can take a while...best to set this up to run over night) 
```
sudo apt update
sudo apt full-upgrade
sudo apt install git
```

3. (optional) It may be convenient to edit files and work on the command line on the Pi via VS Code on your laptop.  Setup VS Code remote connection: [Follow the instructions](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) 
    a. On your laptop, install VS Code and install the Remote-SSH extension (see above link)
    b. From your laptop connect to Remote-SSH to the Jubilee Raspberry Pi, using the username, hostname, and password that you setup earlier.

4. [Install the science Jubilee software.](https://science-jubilee.readthedocs.io/en/latest/getting_started/installation.html) You may choose to drive the Jubilee (via the SBC) from software running on your laptop **and/or** running directly on the Raspberry Pi SBC.  These are **not** mutually exclusive:  The underlying science jubilee code merely makes HTTP requests to control the machine.  There may be value in having it running on the Pi if there is a need to control more sophisticated tools.  

5. On another machine on the same network, open a web-browser and go to [jubilee.local](https://jubilee.local) --- you should have the Duet Web Control running and connected to the board.

## Machine configuration

The following assumes that you are successfully running the Duet Web Control, e.g., [jubilee.local](https://jubilee.local)

6. Update the software versions by issuing the following G-Code commands:
```
M997 S2    ; upgrades web control software 
M997       ; upgrades firmware on main board
M997 B001  ; upgrades firmware on CAN bus board at address 001
``` 
(your web control software is likely to be ahead of the Duet firmware, and the web control will pester you with error messages unless you upgrade)

6. Upload the [Duet 3 Mini+HC system configuration files](https://github.com/machineagency/jubilee/tree/main/software/duet_config_files/duet3_mini_with_3hc)

7. Take a moment to skim through the `/sys/config.g` file that you just uploaded. 
    - Because you are running with SBC mode, comment out the `M552`, `M554` and `M553` lines at the beginning
    - If you are building the notional "Science Jubilee" (without a bed heater), you may also comment out the relevant lines towards the end of the file.


8. Conduct the [pre-flight check](https://jubilee3d.com/index.php?title=Pre-Flight_Checks) to confirm the machine is oriented correctly.  
    - You can use the `M119` gcode command to check the status of the limit switches.
    -  **IMPORTANT:**  The XY direction check is crucial; otherwise the machine will move in the wrong direction which does not have a limit switch.  If the X and Y positive and negative directions are reversed, then you must modify the `/sys/config.g` file to change the default `M569 S` argument.

```
; Motor (Drive) Currents and Directions
;-------------------------------------------------------------------------------
M569 P1.0 S1              ; Flip 3HC Motor 0 (corexy a) direction
M569 P1.1 S1              ; Flip 3HC Motor 1 (corexy b) direction  
```

    - You may also wish to turn on the TMC22099 advanced stepper control which will reduce the annoying buzz when the machine is on but idling, by adding the [M569](https://docs.duet3d.com/User_manual/Reference/Gcodes#m569-set-motor-driver-direction-enable-polarity-mode-and-step-pulse-timing)  `D3` option to the end of your motor definition lines (of course, keep whatever directions you defined above)

```
M569 P1.0 S1 D3            ; Flip 3HC Motor 0 (corexy a) direction
M569 P1.1 S1 D3            ; Flip 3HC Motor 1 (corexy b) direction 
...
M569 P0.2 S0 D3            ; Flip Mainboard Motor 2 (Front Left Z) direction.
M569 P0.3 S0 D3            ; Flip Mainboard Motor 2 (Front Right Z) direction.
M569 P0.4 S0 D3            ; Flip Mainboard Motor 2 (Back Z) direction.
...
M569 P0.1 S0 D3            ; Flip Main Board Motor 0 (toolchanger) directon.
```

    - Use a level app on your phone to approximate level the Z-bed.

9. Perform [mesh-bed leveling](https://jubilee3d.com/index.php?title=Mesh_Bed_Leveling)

# Run your first experiment

10. You are now ready to get started using your Science Jubilee.  Consult the main [Getting started guide](https://science-jubilee.readthedocs.io/en/latest/getting_started/index.html) or the [POSE2025 guide; especially Start Here](https://github.com/machineagency/POSE25/tree/main) for your next steps. 
