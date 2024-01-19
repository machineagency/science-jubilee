Note: see [machineagency/sonication_station](https://github.com/machineagency/sonication_station) for more details for this solution.

# Sonicator PCB

This PCB attaches on top of the Raspberry Pi enabling its GPIOs to control the Sonicator.


## Fabrication

To make this pcb, you'll need to send files (usually gerbers) out to a PCB Fab house of your choice.
Here are some options:

* [OSH Park](https://oshpark.com/) will actually natively accept **.kicad\_pcb** files directly. (This is probably the easiest option.)
    * [instructions for gerber generation](https://docs.oshpark.com/design-tools/kicad/generating-kicad-gerbers/)
* [PCBWay](http://pcbway.com/)
    * [instructions for gerber generation](https://www.pcbway.com/blog/help_center/Generate_Gerber_file_from_Kicad.html)
* Bay Area Circuits has a No-Silk-No-Soldermask 24-hour [Bare Bones Special](https://bayareacircuits.com/prototype-printed-circuit-boards-pcbs/) for time crunched prototypes.

## Assembly

This PCB can be assembled by hand with some tweezers, a microscope (or cheap microscope webcam), and, optionally, a stencil.
Parts will need to be ordered from the BOM.
(You can regenerate the BOM from the native Kicad files.)
