import cv2
import json
import os
import requests
import time
import webbrowser

import matplotlib.pyplot as plt
import numpy as np

from labware.Labware import Well
from typing import Tuple, Union
from .Tool import Tool


class Camera(Tool):
    """
    raspberry pi camera server client
    """
    def __init__(self, machine, index, name, ip_address, port,
                 video_endpoint, still_endpoint, image_folder):
        super().__init__(index, name, ip_address = ip_address,
                         port = port, video_endpoint = video_endpoint,
                         still_endpoint = still_endpoint,image_folder= image_folder)
        self._machine = machine
        self.still_url = f'http://{self.ip_address}:{self.port}/{self.still_endpoint}'
        self.video_url = f'http://{self.ip_address}:{self.port}/{self.video_endpoint}'
        self.tool_offset = self._machine.tool_z_offsets[self.index] 

        #TODO: Ping camera server and make sure that it is reachable

    @classmethod
    def from_config(cls, machine, index, name, config_file: str,
                    path :str = os.path.join(os.path.dirname(__file__), 'configs')):
        config = os.path.join(path,config_file)
        with open(config, 'rt') as f:
            kwargs = json.load(f)
        return cls(machine=machine, index=index, name=name,**kwargs)
    
    @staticmethod
    def _getxyz(location: Union[Well, Tuple]):
        if type(location) == Well:
            x, y, z = location.x, location.y, location.z
        elif type(location) == Tuple:
            x, y, z = location
        else:
            raise ValueError("Location should be of type Well or Tuple")
        
        return x,y,z


    def _capture_image(self, timeout = 10):
        """
        Capture image from raspberry pi and write to file
        """
        try:
            response = requests.get(self.still_url, timeout = timeout)
        except [ConnectionError, ConnectionRefusedError]:
            raise AssertionError
        time.sleep(2)
        assert response.status_code == 200

        return response.content
    
    def capture_image(self, location: Union[Well, Tuple]):
        
        x, y, z = self._getxyz(location)

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y, wait=True)
        self._machine.move_to(z = 43.4, wait = True)
        image = self._capture_image()
        return image

    def video_feed(self):
        webbrowser.open(self.video_url)

    def decode_image(self, image_bin):
        image_arr = np.frombuffer(image_bin, np.uint8)
        image = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
        image_rgb = image[:,:,[2,1,0]]
        return image_rgb

    def process_image(self, image_bin, radius= 50):
        """
        externally callable function to run processing pipeline
        
        takes an image as a bstring
        """
        image = self.decode_image(image_bin)
        r = radius
        masked_image = self._mask_image(image, r)
        t = time.time()
        cv2.imwrite(f'./sampleimage_full_{t}.jpg', image)
        cv2.imwrite(f'./sampleimage_masked_{t}.jpg', masked_image)
        rgb_values = self._get_rgb_avg(masked_image)
        return rgb_values

    def _mask_image(self, image, radius= 50):

        mask = np.zeros(image.shape[:2], dtype = "uint8")
        cv2.circle(mask, (300, 300), radius, 255, -1)
        masked = cv2.bitwise_and(image, image, mask=mask)

        return masked
    
    def _get_rgb_avg(self, image):
        bgr = []
        for dim in [0,1,2]:
            flatdim = image[:,:,dim].flatten()
            indices = flatdim.nonzero()[0]
            value = flatdim.flatten()[indices].mean()
            bgr.append(value)

        #opencv uses bgr so convert to rgb for loss
        print('swapping')
        rgb = [bgr[i] for i in [2,1,0]]
        return rgb

    def view_image(self, image_bin, masked =False, radius =50):
        image = self.decode_image(image_bin)
        if masked is True:
            image = self._mask_image(image, radius)
        else:
            pass
        
        fig, ax = plt.subplots(figsize=(3,4))
        plt.setp(plt.gca(), autoscale_on=True)
        ax.imshow(image)

        #return fig # need to test this return statement