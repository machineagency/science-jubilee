import json
import logging
import os

from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Tuple, Union



class PeristalticPump(Tool):
    """
    Class to manage peristaltic pump operation
    """

    def init():

        # load config file

        # check if mm to volume conversion has been calibrated by user

    def pump(volume:float, speed: float):
        """turn on pump to dispense volume at speed"""

        # calculate 'mm' to dispense given volume
        
        # dispense given volume