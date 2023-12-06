import json
import logging
import os

from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Tuple, Union

class PeristalticPumps(Tool):
    """
    A class representation of a group of PeristalticPumpIndividual objects. Can instantiate with number of pumps to generate and a config. Generic to any stepper-driven peristaltic pump. Combine with PumpDispenser tool for bulk low-precision liquid handling.
    """

    def __init__(self, index: int, n_pumps: int, steps_per_ml: Union[float, list], tool_axis: str = 'E', name: str = 'dispenser_pumps'):

        self.index = index
        self.tool_axis = tool_axis
        self.n_pumps = n_pumps
        self.name = name

        if isinstance(steps_per_ml, float) or isinstance(steps_per_ml, int):
            self.steps_per_ml = [steps_per_ml]*n_pumps
        elif isinstance(steps_per_ml, list):
            assert len(steps_per_ml) == n_pumps, 'steps per ml list length much equal number of pumps'
            self.steps_per_ml = steps_per_ml

    @classmethod
    def from_config(cls, config_file: str,
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
        print(kwargs)
        return cls(**kwargs)
        

    def post_load(self):
        """
        After tool load, set steps per mm on machine
        """
        #set steps per mL on machine
        steps_per_ml = self.steps_per_ml

        gcode = f"M92 {self.tool_axis}"+':'.join([str(stpml) for stpml in steps_per_ml])
        print(gcode)
        self._machine.gcode(gcode)

        return
    

    def pump(self, volume: Union[int, float, list]):
        """turn on pump to dispense volume"""

        # calculate 'mm' to dispense given volume
        # actually this is handled in the steps to mm conversion programmed in axis setup on Jubilee 
        
        # dispense given volume
        if isinstance(volume, list):
            assert isinstance(volume[0], float) or isinstance(volume[0], int), 'Volume list must be floats or ints'
            pass

        elif isinstance(volume, float) or isinstance(volume, int):
            volume = [volume]*self.n_pumps
        
        else:
            raise TypeError('Volume must be an int, float, or list of ints or floats')

        stringvol = ':'.join([str(v) for v in volume]) # negative b/c gcode pump reverse is suspect for now

        # sticking with a direct gcode to send here makes sense: no 3-motor on axis support in movement code, and no risk of crashing anything here
        self._machine.gcode(f'G1 {self.tool_axis}{stringvol}')