import json
import logging
import os

from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Tuple, Union

class PeristalticPumpIndividual(Tool):

    """Class representation for an individual peristaltic pump. Individual pumps should be combined into a pumps group to work correctly 
    
    
    Really the only reason to have this as its own class is to let you use pumps with different steps per mm"""

    def __init__(self, steps_per_ml: float, name: str, user_calibrated: bool = False):

        super().__init__(steps_per_ml = steps_per_ml, name = name, user_calibrated = user_calibrated)

        if not user_calibrated:
            raise Warning('Peristaltic pump not calibrated, accuracy may be inadequate')       

    @classmethod
    def from_config(cls, config_file: str,
                    path :str = os.path.join(os.path.dirname(__file__), 'configs')):
        
        """Initialize the pipette object from a config file

        :param config_file: The name of the config file containign the pipette parameters
        :type config_file: str
        :returns: A :class:`Pipette` object
        :rtype: :class:`Pipette`
        """        
        config = os.path.join(path,config_file)
        with open(config) as f:
            kwargs = json.load(f)

        return cls(**kwargs)

class PeristalticPumps(Tool):
    """
    A class representation of a group of PeristalticPumpIndividual objects. Can instantiate with list of PeristalticPumpIndividual objects or a number of pumps to generate and a config. Generic to any stepper-driven peristaltic pump. Combine with PumpDispenser tool for bulk low-precision liquid handling.
    """

    def __init__(self, index, pumps = None, n_pumps = None, steps_per_ml = None, config_file = None, tool_axis = 'E'):

        self.index = index
        
        if pumps is not None:
            assert isinstance(pumps, list), '"pumps" must be a list of PeristalticPumpIndividual objects'
            self.pumps = pumps

        elif n_pumps is not None:
            assert isinstance(n_pumps, int), '"n_pumps" must be an int'
            if config_file is not None:
                pump = PeristalticPumpIndividual.from_config(config_file)
            elif steps_per_ml is not None:
                pump = PeristalticPumpIndividual(steps_per_ml, 'generic_pump', user_calibrated=True)
            self.pumps = [pump]*n_pumps

        self.n_pumps = len(self.pumps)

    def post_load(self):
        """
        After tool load, set steps per mm on machine
        """
        #set steps per mL on machine
        steps_per_ml = [str(pump.steps_per_mm) for pump in self.pumps]

        gcode = f"M92 {self.tool_axis}"+':'.join(str(steps_per_ml))
        self._machine.gcode(gcode)

        return

    @requires_active_tool
    def pump(self, volume: [float, list], speed: float):
        """turn on pump to dispense volume at speed"""

        # calculate 'mm' to dispense given volume
        # actually this is handled in the steps to mm conversion programmed in axis setup on Jubilee 
        
        # dispense given volume
        if isinstance(volume, list):
            pass

        elif isinstance(volume, float):
            volume = [volume]*self.n_pumps

        stringvol = ':'.join([str(v) for v in volume]) # negative b/c gcode pump reverse is suspect for now

        # sticking with a direct gcode to send here makes sense: no 3-motor on axis support in movement code, and no risk of crashing anything here
        self.gcode(f'G1 {self.tool_axis}{stringvol}')