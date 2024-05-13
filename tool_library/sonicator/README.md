# Sonicator

This tool can be assembled and interfaced in different ways. You can find below a list of necessary components

## Hardware Checklist

### Sonicator Tool
* Q125 Sonicator Horn
* Sonicator Probe (various probe sizes, including pn: 4423, pn: 4422, and pn: 4435)
* Sonicator Control PCB, pn: KITVC1025 (20kHz) or pn: KITVC1045 (40kHz)
* Sonicator Wiring Harness
    * 1x [Molex: 0022552102](https://www.digikey.com/en/products/detail/molex/0022552102/303176)
    * 3x [Molex: 0016020086](https://www.digikey.com/en/products/detail/molex/0016020086/467788)
    * 1x [McMaster-Carr: 7243K117](https://www.mcmaster.com/7243K117/) for the sonicator horn wiring
    * 1x [McMaster-Carr: 7243K122](https://www.mcmaster.com/7243K122/) for the sonicator horn wiring
    * 1x [Digikey: ED10562-ND](https://www.digikey.com/en/products/detail/on-shore-technology-inc/OSTVN03A150/1588863?s=N4IgTCBcDaIKIBECMAGArANjAWgHIJAF0BfIA)

### Raspberry Pi Pico Microcontroller
One of the ways to interface with the sonicator control PCB board is using a Raspberry Pi Pico microcontroller. This solution allows the user to interface the tool through their computer directly, instead of relying on a Raspberry Pi SBC. To set up the RP2040 pico, the instructions and necessary files can be found in the `rp2040` folder.

For this solution, the following items are required:
* 1x [Raspberry Pi Pico RP2040 microcontroller](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
* 1x [Adafruit MCP4725 12-bit DAC](https://www.adafruit.com/product/935)
* 1x [Half-size Breadboard](https://www.adafruit.com/product/64), alternatively you can also purchase a [Half-size soldering breadboard](https://www.digikey.com/en/products/detail/sparkfun-electronics/PRT-12070/5230951)
* 1x [Breadboard wire bundle](https://www.adafruit.com/product/153)
* 1x [2N7000 MOSFET](https://www.digikey.com/en/products/detail/onsemi/2N7000/244278)
* 1x [100𝜇F Capacitor](https://www.amazon.com/100uF-105%C2%B0C-Aluminum-Electrolytic-Capacitor/dp/B07D6WDQMV/ref=sr_1_3?keywords=100+mfd+capacitor&qid=1705604871&sr=8-3)
* 1x [4.7kΩ Resistor](https://www.adafruit.com/product/2783)

Below is a schematics for the assembly:
<img src="https://github.com/machineagency/science-jubilee/tree/main/tool_library/sonicator/schematics/RaspberryPi_Pico_Microcontroller_Schematics.png">

### Raspberry Pi SBC and PCB Hat
If you are interfacing your Science Jubilee using a Raspberry Pi singleboard computer, you will need to order and assemble the *sonicator PCB* hat. The instructions and necessary files can be found in the `pcb_hat` folder. The Sonicator Pi Hat will be attached to the Pi and connected to the Sonicator Control PCB.
A schematics can be found [here](https://github.com/machineagency/science-jubilee/tree/main/tool_library/sonicator/schematics/RaspberryPi_PCB_Hat_Schematics.pdf)
This solution is the original imlementaiotn of this tool in combination with a Jubilee platform. This project was also known as the *Sonication Station*. The original repository is [here](https://github.com/machineagency/sonication_station).
