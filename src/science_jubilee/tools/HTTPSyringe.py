import json
import logging
import os
from itertools import dropwhile, takewhile
from typing import Iterator, List, Tuple, Union

import requests

from science_jubilee.labware.Labware import Labware, Location, Well
from science_jubilee.tools.Tool import (
    Tool,
    ToolConfigurationError,
    ToolStateError,
    requires_active_tool,
)



class HTTPSyringe(Tool):

    def __init__(self, index, url):
        """
        HTTP Syringe is digital syringe for Jubilee
        
        """
        # get config things from HTTP interface
        config_r = requests.get(url+'/get_config')

        config = config_r.json

        super().__init(index, **config, url = url)

        status_r = requests.get(url + '/get_status')

        status = status_r.json

        self.syringe_loaded = status['syringe_loaded']
        self.remaining_volume = status['remaining_volume']

        return

    @classmethod
    def from_config(cls, index, fp):
        with open(fp) as f:
            kwargs = json.load(f)

        return cls(index, **kwargs)
    
    @requires_active_tool
    def _aspirate(self, vol):

        assert isinstance(vol, float) or isinstance(vol, int), 'Vol must be float or int'

        assert vol < self.capacity - self.remaining_volume, f'Error: Syringe {self.name} available volume is {self.capacity - self.remaining_volume} uL, {vol} mL aspiration requested'

        r = requests.post(self.url+ '/aspirate', json = {'volume':vol})

        assert r.status_code == 200, f'Error in aspirate request: {r.content}'

        status_r = requests.get(self.url+'/get_status')

        status_dict = status_r.json

        self.remaining_volume = status_dict['remaining_volume']

        return
    
    @requires_active_tool
    def _dispense(self, vol):
        
        assert isinstance(vol, float) or isinstance(vol, int), 'Vol must be flaot or int'
        assert vol < self.remaining_volume, f'Error: Syringe {self.name} remaining volume is {self.remaining_volume} uL, but {vol} uL dispense requested'

        r = requests.post(self.url+ '/dispense', json = {'volume':vol})

        assert r.status_code == 200, f'Error in dispense request: {r.content}'

        status_r = requests.get(self.url+ '/get_status')
        status_dict = status_r.json
        self.remaining_volume = status_dict['remaining_volume']
        return
    

    @requires_active_tool
    def dispense(
        self, vol: float, location: Union[Well, Tuple, Location]
    ):
        """Moves the pipette to the specified location and dispenses the desired volume of liquid

        :param vol: The volume of liquid to dispense in uL
        :type vol: float
        :param location: The location to dispense the liquid into.
        :type location: Union[Well, Tuple, Location]
        :raises ToolStateError: If the pipette does not have a tip attached
        """
        x, y, z = Labware._getxyz(location)

        if type(location) == Well:
            self.current_well = location
            if z == location.z:
                z = z + 10
            else:
                pass
        elif type(location) == Location:
            self.current_well = location._labware
        else:
            pass

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._dispense(vol)

    
    @requires_active_tool
    def aspirate(
        self, vol: float, location: Union[Well, Tuple, Location]
    ):
        """Moves the pipette to the specified location and aspirates the desired volume of liquid

        :param vol: The volume of liquid to aspirate in uL
        :type vol: float
        :param location: The location from where to aspirate the liquid from.
        :type location: Union[Well, Tuple, Location]
        :raises ToolStateError: If the pipette does not have a tip attached
        """
        x, y, z = Labware._getxyz(location)

        if type(location) == Well:
            self.current_well = location
        elif type(location) == Location:
            self.current_well = location._labware
        else:
            pass

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._aspirate(vol)






