import json
import logging
import os

from science_jubilee.labware.Labware import Labware, Well, Location
from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Tuple, Union

class PumpDispenser(Tool):
    """
    Class to manage dispenser tool, for example for a color mixing demo
    """

    def init()
        
        # offsets live in config file, pipette tip '0' is centered in Jubilee duet-level setup
        

    """
    parameters for user to give:
    - number of dispenser heads (only 3 supported for now)
    - pump:dispenser head mapping
    - garbage/waste well
    - line prime/purge volume


    This needs to have all the well management tooling of the pipette
    """

    def dispense(well, volume, speed, dispense head):


    def prime_lines(volume):
        """
        fill lines with liquid from all pumps at same time, dispense `volume` from each pump
        """

    def empty_lines(volume):
        """
        return line contents to stock wells
        """

