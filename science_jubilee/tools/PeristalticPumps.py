import json
import logging
import os

from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Tuple, Union



class PeristalticPump(Tool):
    """
    Class to manage peristaltic pump operation
    """

    def __init__(self, index, steps_per_ml, ):

        # load config file

        # check if mm to volume conversion has been calibrated by user
        # overwrite machine steps per mm with config supplied one
        # send M92E{value}

       

    @classmethod
    def from_config(cls, machine, index, name, config_file: str,
                    path :str = os.path.join(os.path.dirname(__file__), 'configs')):
        
        """Initialize the pipette object from a config file

        :param machine: The :class:`Machine` object that the pipette is loaded on
        :type machine: :class:`Machine`
        :param index: The tool index of the pipette on the machine
        :type index: int
        :param name: The tool name
        :type name: str
        :param config_file: The name of the config file containign the pipette parameters
        :type config_file: str
        :returns: A :class:`Pipette` object
        :rtype: :class:`Pipette`
        """        
        config = os.path.join(path,config_file)
        with open(config) as f:
            kwargs = json.load(f)

        return cls(machine, index, name, **kwargs)

    def pump(volume:float, speed: float):
        """turn on pump to dispense volume at speed"""

        # calculate 'mm' to dispense given volume
        # actually this is handled in the steps to mm conversion programmed in axis setup on Jubilee 
        
        # dispense given volume
        volumes = [0,0,0]
        volumes[pippette_index] = volume
        stringvol = ':'.join([str(v) for v in volumes]) # negative b/c gcode pump reverse is suspect for now

        self.gcode(f'G1 E{stringvol}')