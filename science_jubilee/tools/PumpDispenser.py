import json
import logging
import os

from science_jubilee.labware.Labware import Labware, Well, Location
from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Tuple, Union
from science_jubilee import utils

class PumpDispenser(Tool):
    """
    Class to manage dispenser tool, for example for a color mixing demo
    """


    def __init__(self, index, name, pump_group, dispense_tip_offsets, line_volume, waste = None):
        """
        parameters for user to give:
        - number of dispenser heads (only 3 supported for now)
        - pump:dispenser head mapping
        - garbage/waste well
        - line prime/purge volume


        This needs to have all the well management tooling of the pipette
        """
        super().__init__(index, name, pump_group = pump_group, dispense_tip_offsets = dispense_tip_offsets)

        self.n_dispense_heads = len(self.dispense_tip_offsets)
        self.waste = waste
        self.line_volume = line_volume
        assert self.pump_group.n_pumps == self.n_dispense_heads, "Number of pumps must match number of dispenser tips"

    @classmethod
    def from_config(cls, index, pump_group, config_file: str,
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
        kwargs['pump_group'] = pump_group
        kwargs['index'] = index

        return cls(**kwargs)


    def add_waste(self, location: Union[Well, Tuple, Location]):
        """
        Specify a waste collection container
        """
        assert isinstance(location, Well) or isinstance(location, Tuple) or isinstance(location, Location), 'location must be a well, tuple, or location'
        self.waste = location


    def dispense(self, vol: Union[float, int, list], location:Union[Well, Tuple, Location], dispense_head_index = None):
        """
        Dispense volume vol from dispense head dispense_head_index into location 
        """
        # get dispense volumes for each dispense head 
        if isinstance(vol, list):
            assert len(vol) == self.n_dispense_heads
            dispense_volumes = vol
        elif isinstance(vol, float) or isinstance(vol, int):
            if dispense_head_index is None:
                # dispense same volume from every head
                dispense_volumes = [vol]*self.n_dispense_heads
            elif isinstance(dispense_head_index, int):
                dispense_volumes = [0]*self.n_dispense_heads
                dispense_volumes[dispense_head_index] = vol
            else:
                raise AssertionError('dispense_head_index must be an integer') 
        else:
            raise AssertionError('vol must be a float, int, or list')


        # calculate XY location for each dispense head
        x, y, z = utils.getxyz(location)

        if type(location) == Well:
            if z == location.z:
                z = z + 10
            else:
                pass
        else:
            pass

        # iterate over each dispense head, skip if 0. Move to location and dispense 
        for i, vol in enumerate(dispense_volumes):
            if vol == 0:
                continue
            else:
                # get volume for this specific dispense head 
                iter_vol = [0]*self.n_dispense_heads
                iter_vol[i] = vol

                tip_offsets = self.dispense_tip_offsets[i]
                x_tip = x + tip_offsets[0]
                y_tip = y + tip_offsets[1]

                self._machine.safe_z_movement()
                self._machine.move_to(x = x_tip, y = y_tip)
                self._machine.move_to(z = z)

                self.pump_group.pump(iter_vol)

        


    def prime_lines(self, volume: Union[int, float] = None, location:Union[Well, Tuple, Location] = None):
        """
        fill lines with liquid from all pumps at same time, dispense `volume` from each pump
        """

        if volume is None:
            try:
                volume = self.line_volume
            except AttributeError:
                raise AssertionError('Line prime volume not specified in configuration. Please specify a volume')
        
        if location is None and self.waste is None:
            raise AssertionError('Please specify a waste location')
        
        if location is None:
            location = self.waste

        # calculate XY location for each dispense head
        x, y, z = utils.getxyz(location)

        if type(location) == Well:
            if z == location.z:
                z = z + 10
            else:
                pass
        else:
            pass

        self._machine.safe_z_movement()
        self._machine.move_to(x = x, y = y)
        self._machine.move_to(z = z)

        self.pump_group.pump(volume)

        
    def empty_lines(self, volume: Union[int, float] = None):
        """
        return line contents to stock wells
        """
        if volume is None:
            try:
                volume = self.line_volume
            except AttributeError:
                raise AssertionError('Line prime volume not specified in configuration. Please specify a volume')

        self.pump_group.pump(-volume)



