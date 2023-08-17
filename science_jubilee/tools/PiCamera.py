import requests
import webbrowser
import time
from .Tool import Tool
from labware.Utils import json2dict
import os


class Camera(Tool):
    """
    raspberry pi camera server client
    """
    def __init__(self, machine, index, name, ip_address, port,
                 video_endpoint, still_endpoint, image_folder):
        super().__init__(machine, index, name, ip_address = ip_address,
                         port = port, video_endpoint = video_endpoint,
                         still_endpoint = still_endpoint,image_folder= image_folder)
        self.still_url = f'http://{self.ip_address}:{self.port}/{self.still_endpoint}'
        self.video_url = f'http://{self.ip_address}:{self.port}/{self.video_endpoint}'
    
    @classmethod
    def from_config(cls, machine, index, name, config_file: str,
                    path :str = os.path.join(os.path.dirname(__file__), 'configs')):
        kwargs = json2dict(config_file, path = path)
        return cls(machine=machine, index=index, name=name,**kwargs)
    
    
    def capture_image(self, timeout = 10):
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

    def video_feed(self):
        webbrowser.open(self.video_url)
