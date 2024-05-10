# Raspberry Pi WebCamera

The WebCamera tool is just a Raspberry Pi Camera set up to support a livestream video over the web.
This can be used to monitor samples/objects on the deck. Alternatively, it can also be used to collect images of samples as a Tool hosted on your Jubilee.

## Necessary Hardware:
* A Raspberry Pi SBC
* Raspberry Pi camera (V2 or V3)
* An arducam pi camera HDMI extension kit along with an [hdmi cable](https://www.amazon.com/Arducam-Extension-Module-Raspberry-Specific/dp/B06XDNBM63/ref=sr_1_3?keywords=raspberry+pi+camera+hdmi+cable+extension&qid=1690922784&sprefix=raspberry+pi+camera+hdmi%2Caps%2C122&sr=8-3*)
* Hdmi cable (at least 3ft)
* Ethernet cable ( at least 3ft)

## Ring Light (Optional):
* Side emitting COB LED lights (e.g., [LED lights](https://www.amazon.com/dp/B0CG9H983Z?psc=1&ref=ppx_yo2ov_dt_b_product_details))

To control the LED lights, you can use the Duet board by plugging them into a 'fan' port. On your main Duet board you can for example `out5` or `out6` ports.
1. Cabling :

* connect the *positive LED lead* into the *"V_OUTLC2 +"* pin
* connect the *negative LED lead* into the *"out5 -"* pin

2. Duet Config

Define the LED lights into the `config.g` file of your jubilee by using the `M950` command:
`M950 P0 C"0.out5"` # P{LED index}; C{port name}

To turn on and off the light you will use the `M42` command:
`M42 P0 S0.5` # P{LED index}; S{intensity}, ranges from 0 (off) to 1 (max intensity)
    Note: this optin is alreadyimplement in the tool.WebCamera mdule. You will need to define the LED index in the tool config file and set `light=True` and `light_intensity= float` in the `capture_image()` method.

## RaspberryPi Set up

* Install raspberry pi os on a Raspberry Pi 4GB of ram should be fine - we’re just running a web server on it to stream videos
* Connect the camera using the hdmi cable extension kit. Make sure the camera works at this stage before trying to get the web server to work.
* Clone the `PI-camera-stream-flask` repo onto your raspberry pi. Brenden Pelkies’s fork has a few updates that makes it work with jubilee. [Github repository](https://github.com/brendenpelkie/pi-camera-stream-flask)
* Follow the instructions in the readme of the repo to get the camera up and running.
* Connect the raspberry pi to your local network and manually specify an IP address for it. To complete these steps, there are a lot of tutorials. [Here is one](https://www.makeuseof.com/raspberry-pi-set-static-ip/)
* Connect to your raspberry pi camera by navigating to `http:/<yourPi_IPaddress>:50001`. You should now be able to see a live feed video displayed with some buttons and a target pattern.
