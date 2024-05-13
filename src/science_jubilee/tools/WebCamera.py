import json
import os
import time
import webbrowser
from typing import Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
import requests

from science_jubilee.labware.Labware import Labware, Location, Well
from science_jubilee.tools.Tool import Tool, requires_active_tool


class Camera(Tool):
    """A class representation of a Raspberry Pi camera server client."""

    def __init__(
        self,
        index,
        name,
        ip_address,
        port,
        video_endpoint,
        still_endpoint,
        image_folder,
        focus_height,
        light: bool = False,
        light_pin: int = None,
    ):
        """Initializes the Camera object.

        :param index: The tool index of the pipette on the machine
        :type index: int
        :param name: The name associated with the tool (e.g. 'p300_single')
        :type name: str
        :param ip_address: The IP address of the Raspberry Pi camera server
        :type ip_address: str
        :param port: The port for the camera http requests
        :type port: int
        :param video_endpoint: The endpoint for the video feed
        :type video_endpoint: str
        :param still_endpoint: The endpoint for the still image
        :type still_endpoint: str
        :param image_folder: The folder to save captured images to
        :type image_folder: str
        :param light: LED ring light associated with the camera, defaults to False
        :type light: bool, optional
        :param light_pin: The GPIO pin (defined in the `M950` command in the machine `config.g`) for the LED ring light, defaults to None
        :type light_pin: int, optional
        """

        super().__init__(
            index,
            name,
            ip_address=ip_address,
            port=port,
            video_endpoint=video_endpoint,
            still_endpoint=still_endpoint,
            image_folder=image_folder,
            light=light,
            light_pin=light_pin,
            focus_height=focus_height,
        )
        self.still_url = f"http://{self.ip_address}:{self.port}/{self.still_endpoint}"
        self.video_url = f"http://{self.ip_address}:{self.port}/{self.video_endpoint}"

        # TODO: Ping camera server and make sure that it is reachable

    @classmethod
    def from_config(
        cls,
        index,
        name,
        config_file: str,
        path: str = os.path.join(os.path.dirname(__file__), "configs"),
    ):
        """Initialize the pipette object from a config file

        :param index: The tool index of the pipette on the machine
        :type index: int
        :param name: The name associated with the tool (e.g. 'WebCamera')
        :type name: str
        :param config_file: The name of the config file containing the tool parameters
        :type config_file: str
        :param path: The path to the labware configuration `.json` files for the labware,
                defaults to the 'labware_definition/' in the science_jubilee/labware directory.
        :type path: str, optional
        :return: the initialized :class:`Camera` object
        :rtype: :class:`Camera` object
        """

        config = os.path.join(path, config_file)
        with open(config, "rt") as f:
            kwargs = json.load(f)
        return cls(index=index, name=name, **kwargs)

    @requires_active_tool
    def _capture_image(self, timeout=30):
        """Capture image from raspberry pi and write to file

        :param timeout: the timeout for the http request, defaults to 10
        :type timeout: int, optional
        :return: the image as a bstring
        :rtype: bytes
        """
        time.sleep(1)
        try:
            response = requests.get(self.still_url, timeout=timeout)
        except [ConnectionError, ConnectionRefusedError]:
            raise AssertionError
        time.sleep(2)
        assert response.status_code == 200

        return response.content

    @requires_active_tool
    def capture_image(
        self,
        location: Union[Well, Tuple],
        light: bool = False,
        light_intensity: int = 0,
        timeout=30,
    ):
        """Capture an image from the WebCamera at the specified location

        :param location: the location of the well to capture an image of
        :type location: Union[Well, Tuple]
        :param light: Option to turn on a ring light before taking the image, defaults to False
        :type light: bool, optional
        :param light_intensity: Intensity of the led rign light, defaults to 0
        :type light_intensity: int, optional
        :return: the image as an bstring
        :rtype: bytes
        """
        assert 0 <= light_intensity <= 1, "Light intensity must be between 0 and 1"

        x, y, z = Labware._getxyz(location)

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y, wait=True)

        picture_heigth = self.focus_height - abs(self.tool_offset)
        self._machine.move_to(z=picture_heigth, wait=True)
        if light is True:
            self._machine.gcode(f"M42 P{self.light_pin} S{light_intensity}")
            image = self._capture_image(timeout=timeout)
            self._machine.gcode(f"M42 P{self.light_pin} S0")
        else:
            image = self._capture_image()

        return image

    def video_feed(self):
        """Deploys a video feed at the url specified in the config file"""
        webbrowser.open(self.video_url)

    def decode_image(self, image_bin):
        """Decode a bstring image into an np.array

        :param image_bin: the image as a bstring
        :type image_bin: bytes
        :return: the image as an np.array
        :rtype: np.array
        """
        image_arr = np.frombuffer(image_bin, np.uint8)
        image = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
        image_rgb = image[:, :, [2, 1, 0]]
        return image_rgb

    def process_image(self, image_bin, radius=50):
        """Externally callable function to run processing pipeline

        :param image_bin: the image as a bstring
        :type image_bin: bytes
        :param radius: the radius (in pixels) of the circular mask, defaults to 50
        :type radius: int, optional
        :return: the average rgb values of the masked image
        :rtype: list

        """
        image = self.decode_image(image_bin)
        r = radius
        masked_image = self._mask_image(image, r)
        t = time.time()
        cv2.imwrite(f"./sampleimage_full_{t}.jpg", image)
        cv2.imwrite(f"./sampleimage_masked_{t}.jpg", masked_image)
        rgb_values = self._get_rgb_avg(masked_image)
        return rgb_values

    def _mask_image(self, image, radius=50):
        """Apply a circular mask to an image

        :param image: the image object
        :type image: np.array
        :param radius: the size (in pixels) of the circular mask, defaults to 50
        :type radius: int, optional
        :return: the masked image
        :rtype: np.array
        """
        image_shape = image.shape[:2]
        w = image_shape[0] // 2
        h = image_shape[1] // 2
        mask = np.zeros(image_shape, dtype="uint8")
        cv2.circle(mask, (w, w), radius, 255, -1)
        masked = cv2.bitwise_and(image, image, mask=mask)

        return masked

    def _get_rgb_avg(self, image):
        """Extract the average rgb values from an image

        :param image: the image object
        :type image: np.array
        :return: the average rgb values in a list [R,G,B]
        :rtype: list
        """
        bgr = []
        for dim in [0, 1, 2]:
            flatdim = image[:, :, dim].flatten()
            indices = flatdim.nonzero()[0]
            value = flatdim.flatten()[indices].mean()
            bgr.append(value)

        # opencv uses bgr so convert to rgb for loss
        print("swapping")
        rgb = [bgr[i] for i in [2, 1, 0]]
        return rgb

    def view_image(self, image_bin, masked=False, radius=50):
        """Show the image in a matplotlib window

        :param image_bin: the image as a bstring
        :type image_bin: bytes
        :param masked: Wether to mask the image or not, defaults to False
        :type masked: bool, optional
        :param radius: the size (in pixel) of the circular mask toapply to the image , defaults to 50
        :type radius: int, optional
        """

        image = self.decode_image(image_bin)
        if masked is True:
            image = self._mask_image(image, radius)
        else:
            pass

        fig, ax = plt.subplots(figsize=(3, 4))
        plt.setp(plt.gca(), autoscale_on=True)
        ax.imshow(image)
