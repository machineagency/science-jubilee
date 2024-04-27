import json
import logging
import os

from itertools import dropwhile, takewhile
from science_jubilee.labware.Labware import Labware, Well, Location
from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool

from typing import Tuple, Union, Iterator, List

class Afl_catch(Tool):
    def __init__(self, deck_object, index, name = 'piston'):

        self.name = name
        self.index = index
        self.labware = deck_object
        self.z_seal_height = 60

    @requires_active_tool
    def close_catch(self):
        x = self.labware[0].x
        y = self.labware[0].y

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=self.z_seal_height)


    def open_catch(self):
        self._machine.safe_z_movement()
        self._machine.move_to(z = 200)


