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

import time



class HTTPSyringe(Tool):

    def __init__(self, index, name, url):
        """
        HTTP Syringe is digital syringe for Jubilee
        
        """

        self.name = name
        self.index = index
        # get config things from HTTP interface
        config_r = requests.post(url+'/get_config', json = {'name':name})

        config = config_r.json()

        super().__init__(index, **config, url = url)

        status_r = requests.post(url + '/get_status', json = {'name':name})

        status = status_r.json()

        self.syringe_loaded = status['syringe_loaded']
        self.remaining_volume = status['remaining_volume']

        return

    @classmethod
    def from_config(cls, index, fp):
        with open(fp) as f:
            kwargs = json.load(f)

        return cls(index, **kwargs)
    
    def status(self):
        """
        Fetch and update status
        """

        r  = requests.post(self.url + '/get_status', json = {'name':self.name})
        status = r.json()

        self.syringe_loaded = status['syringe_loaded']
        self.remaining_volume = status['remaining_volume']

        return status


    def load_syringe(self, volume, pulsewidth):
        """
        Configure a syringe after physically loading it

        volume: Current loaded volume in syringe
        pulsewidth: current pulsewidth position of servo
        """

        data = {}
        data['volume'] = volume
        data['pulsewidth'] = pulsewidth
        data['name'] = self.name

        requests.post(self.url + '/load_syringe', json = data)

        status = self.status()

        print(f'Loaded syringe, remaining volume {status["remaining_volume"]} uL')

        return

    @requires_active_tool
    def _aspirate(self, vol):

        assert isinstance(vol, float) or isinstance(vol, int), 'Vol must be float or int'

        assert vol < self.capacity - self.remaining_volume, f'Error: Syringe {self.name} available volume is {self.capacity - self.remaining_volume} uL, {vol} mL aspiration requested'

        r = requests.post(self.url+ '/aspirate', json = {'volume':vol, 'name':self.name})

        assert r.status_code == 200, f'Error in aspirate request: {r.content}'

        status_r = requests.post(self.url+'/get_status', json = {'name':self.name})

        status_dict = status_r.json()

        self.remaining_volume = status_dict['remaining_volume']

        return
    
    @requires_active_tool
    def _dispense(self, vol):
        
        assert isinstance(vol, float) or isinstance(vol, int), 'Vol must be flaot or int'
        assert vol < self.remaining_volume, f'Error: Syringe {self.name} remaining volume is {self.remaining_volume} uL, but {vol} uL dispense requested'

        r = requests.post(self.url+ '/dispense', json = {'volume':vol, 'name':self.name})

        assert r.status_code == 200, f'Error in dispense request: {r.content}'

        status_r = requests.post(self.url+ '/get_status', json = {'name':self.name})
        status_dict = status_r.json()
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
        self._machine.move_to(x=x, y=y, wait = True)
        self._machine.move_to(z=z, wait = True)
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
        self._machine.move_to(x=x, y=y, wait = True)
        self._machine.move_to(z=z, wait= True)
        self._aspirate(vol)

    @requires_active_tool
    def mix(
            self, 
            vol: float,
            n_mix: int,
            location: Union[Well, Tuple, Location],
            t_hold: int = 1,
    ):
        """
        Mixes n times with volume vol
        """
        x, y, z = Labware._getxyz(location)

        if type(location) == Well:
            self.current_well = location
        elif type(location) == Location:
            self.current_well = location._labware
        else:
            pass

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y, wait = True)
        self._machine.move_to(z=z, wait= True)

        for _ in range(n_mix):
            print('aspirate')
            self._aspirate(vol)
            time.sleep(t_hold)
            print('dispense')
            self._dispense(vol)
            time.sleep(t_hold)




    def set_pulsewidth(self, pulsewidth):
        """
        Manually move the servo actuator to a new location by setting the new pulsewidth.

        Does not update volume, use carefully 
        """

        assert pulsewidth > self.full_position
        assert pulsewidth < self.empty_position

        r = requests.post(self.url + '/set_pulsewidth', json = {'pulsewidth':pulsewidth, 'name':self.name})

        status = self.status()

        return 






