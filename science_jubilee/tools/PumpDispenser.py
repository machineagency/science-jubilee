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


    def __init__(self, index, pump_group, dispense_tip_offsets):
        """
        parameters for user to give:
        - number of dispenser heads (only 3 supported for now)
        - pump:dispenser head mapping
        - garbage/waste well
        - line prime/purge volume


        This needs to have all the well management tooling of the pipette
        """
        super().__init__(index, pump_group = pump_group, dispense_tip_offsets = dispense_tip_offsets)

        self.n_dispense_heads = len(self.dispense_tip_offsets)
        self.waste = None
        assert self.pump_group.n_pumps == self.n_dispense_heads, "Number of pumps must match number of dispenser tips"

    def add_waste(self, location: Union[Well, Tuple, Location]):
        """
        Specify a waste collection container
        """
        assert isinstance(location, Union[Well, Tuple, Location]), 'location must be a well, tuple, or location'
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
                volumes = [0]*self.n_dispense_heads
                volumes[dispense_head_index] = vol
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
        for i, vol in enumerate(volumes):
            if vol == 0:
                continue
            else:
                tip_offsets = self.dispense_tip_offsets[i]
                x_tip = x - tip_offsets[0]
                y_tip = y - tip_offsets[1]

                self._machine.safe_z_movement()
                self._machine.move_to(x = x_tip, y = y_tip)
                self._machine.move_to(z = z)

                self.pump_group.pump(dispense_volumes)

        


    def prime_lines(self, volume: Union[int, float] = None, location:Union[Well, Tuple, Location] = None):
        """
        fill lines with liquid from all pumps at same time, dispense `volume` from each pump
        """

        if volume is None:
            try:
                volume = self.prime_line_volume
            except AttributeError:
                raise AssertionError('Line prime volume not specified in configuration. Please specify a volume')
        
        if location is None and self.waste is None:
            raise AssertionError('Please specify a waste location')
        
        self.dispense(volume, location)

        
    def empty_lines(self, volume: Union[int, float] = None):
        """
        return line contents to stock wells
        """
        if volume is None:
            try:
                volume = self.prime_line_volume
            except AttributeError:
                raise AssertionError('Line prime volume not specified in configuration. Please specify a volume')

        self.pump_group.pump(-volume)



