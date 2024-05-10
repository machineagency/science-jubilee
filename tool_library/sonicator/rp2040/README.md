# Setting up the RP2040 Pico microcontroller

The projects implements the [Raspberry Pi Pico C/C++ SDK](https://datasheets.raspberrypi.com/pico/getting-started-with-pico.pdf).

To start, you should clone the GitHub repository for the [Pico-sdk](https://github.com/raspberrypi/pico-sdk) in your *PROJECT_DIRECTORY* and set up all the required submodules by running the following command in the sdk directory:

`git submodule update --init --recursive`

You can now follow the instructions to *Quick-start your own project*.

The `CMakelists.txt`, as well as the `main.c` files can be found here and should be placed in your *PROJECT_DIRECTORY* too.

## Compile the Firmware
Create a `/build` directory and navigate to it, then run the following commands:

`cmake ..`

This creates all the files required to later create the executable `.uf2` files. You can do so by running :

`make`

## Upload the Firmware onto the RP2040
Load the Pico in BOOTSEL mode and plug it into your computer's usb. Now, you can drag-and-drop the generated `.uf2` file into the mass storage device representing the Pico. It should now be automatically ejected and ready to use.

## Editing the Firmware
You can edit the `main.c` file to change which pins you are using to connect to the MCP4725 DAC or which GPIO pin turns on/off the sonicator.
If you do so, you will need to re-run the following command:

`make`

    Note: if you make changes to the `CMakeLists.txt` file, you will need to re-create the `/build` folder, navigate to it, and run `cmake ..` , followed by `make` too.
