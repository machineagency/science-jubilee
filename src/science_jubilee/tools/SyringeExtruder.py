import json
import math
import os
import warnings
from typing import Tuple, Union

import numpy as np

from science_jubilee.labware.Labware import Labware, Location, Well
from science_jubilee.tools.Tool import (
    Tool,
    ToolConfigurationError,
    ToolStateError,
    requires_active_tool,
)


class SyringeExtruder(Tool):
    """A class representation of a syringe for extrusion 3D printing.

    :param Tool: The base tool class
    :type Tool: :class:`Tool`
    """

    def __init__(self, index, name, config):
        """Constructor method"""
        super().__init__(index, name)

        self.min_range = 0
        self.max_range = None
        self.mm_to_ml = None
        self.e_drive = "E1"

        self.nozzle_diameter = 0.898  # default 18 gauge tip
        self.syringe_diameter = 14

        self.load_config(config)

    def load_config(self, config):
        """Loads the confirguration file for the syringe tool

        :param config: Name of the config file for your syringe. Expects the file to be in /tools/configs
        :type config: str
        """

        config_directory = os.path.join(os.path.dirname(__file__), "configs")
        config_path = os.path.join(config_directory, f"{config}.json")
        if not os.path.isfile(config_path):
            raise ToolConfigurationError(
                f"Error: Config file {config_path} does not exist!"
            )

        with open(config_path, "r") as f:
            config = json.load(f)
        self.min_range = config["min_range"]
        self.max_range = config["max_range"]
        self.mm_to_ml = config["mm_to_ml"]

        # Check that all information was provided
        if None in vars(self):
            raise ToolConfigurationError(
                "Error: Not enough information provided in configuration file."
            )

    def post_load(self):
        """Query the object model after loading the tool to find the extruder number of this syringe."""

        # To read the position of an extruder, we need to know which extruder number to look at
        # Query the object model to find this
        tool_info = json.loads(self._machine.gcode('M409 K"tools[]"'))["result"]
        for tool in tool_info:
            if tool is None:
                continue
            if tool["number"] == self.index:
                self.e_drive = (
                    f"E{tool['extruders'][0]}"  # Syringe tool has only 1 extruder
                )
            else:
                continue

    def check_bounds(self, pos):
        """Disallow commands outside of the syringe's configured range

        :param pos: The E position to check
        :type pos: float
        """
        if pos > self.max_range or pos < self.min_range:
            raise ToolStateError(f"Error: {pos} is out of bounds for the syringe!")

    def make_e(self, x, y, z):
        pos = self._machine.get_position()
        start = [float(pos["X"]), float(pos["Y"]), float(pos["Z"])]
        if x is None:
            x = start[0]
        if y is None:
            y = start[1]
        if z is None:
            z = start[2]
        end = [x, y, z]
        d = self.dist(start, end)

        return 2 * d * (self.nozzle_diameter / self.syringe_diameter) ** 2

    def dist(self, start, end):
        dist = math.sqrt(
            (end[0] - start[0]) ** 2
            + (end[1] - start[1]) ** 2
            + (end[2] - start[2]) ** 2
        )
        return dist

    def wipe_nozzle(self, x=285, y=250, z=0.2):
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self.move_extrude(x=x, y=y - 50, z=z, multiplier=3)

    def wipe_tower(self, x=285, y=250, z=0.2):
        self._machine.move_to(x=x, y=y, s=3600)
        self._machine.move_to(z=z)
        self.move_extrude(x=x, y=y - 20, z=z, s=200)
        self.move_extrude(x=x - 20, y=y - 20, z=z, s=200)
        self.move_extrude(x=x - 20, y=y, z=z, s=200)
        self.move_extrude(x=x, y=y, z=z, s=200)
        self._machine.move(dx=3)

    @requires_active_tool
    def move_extrude(self, x=None, y=None, z=None, s=180, multiplier=1, e=None):
        if not e:
            e = self.make_e(x, y, z)
            e *= multiplier

        x = "{0:.2f}".format(x) if x is not None else None
        y = "{0:.2f}".format(y) if y is not None else None
        z = "{0:.2f}".format(z) if z is not None else None
        e = "{0:.2f}".format(e) if e is not None else None
        s = "{0:.2f}".format(s)

        # initialize coordinates commands
        x_cmd = y_cmd = z_cmd = e_cmd = f_cmd = ""

        if x is not None:
            x_cmd = f"X{x}"
        if y is not None:
            y_cmd = f"Y{y}"
        if z is not None:
            z_cmd = f"Z{z}"
        if e is not None:
            e_cmd = f"E{e}"
        if s is not None:
            f_cmd = f"F{s}"

        cmd = f"G0 {z_cmd} {x_cmd} {y_cmd} {e_cmd} {f_cmd}"
        self._machine.gcode(cmd)

    @requires_active_tool
    def _aspirate(self, vol: float, s: int = 2000):
        """Aspirate a certain volume in milliliters. Used only to move the syringe; to aspirate from a particular well, see aspirate()

        :param vol: Volume to aspirate, in milliliters
        :type vol: float
        :param s: Speed at which to aspirate in mm/min, defaults to 2000
        :type s: int, optional
        """
        de = vol * -1 * self.mm_to_ml
        pos = self._machine.get_position()
        end_pos = float(pos[self.e_drive]) + de
        self.check_bounds(end_pos)
        self._machine.move(de=de, wait=True)

    @requires_active_tool
    def _dispense(self, vol, s: int = 2000):
        """Dispense a certain volume in milliliters. Used only to move the syringe; to dispense into a particular well, see dispense()

        :param vol: Volume to dispense, in milliliters
        :type vol: float
        :param s: Speed at which to dispense in mm/min, defaults to 2000
        :type s: int, optional
        """
        de = vol * self.mm_to_ml
        pos = self._machine.get_position()
        end_pos = float(pos[self.e_drive]) + de
        self.check_bounds(end_pos)
        self._machine.move(de=de, wait=True)

    @requires_active_tool
    def aspirate(
        self, vol: float, location: Union[Well, Tuple, Location], s: int = 2000
    ):
        """Aspirate a certain volume from a given well.

        :param vol: Volume to aspirate, in milliliters
        :type vol: float
        :param location: The location (e.g. a `Well` object) from where to aspirate the liquid from.
        :type location: Union[Well, Tuple, Location]
        :param s: Speed at which to aspirate in mm/min, defaults to 2000
        :type s: int, optional
        """
        x, y, z = Labware._getxyz(location)

        # self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._aspirate(vol, s=s)

    @requires_active_tool
    def dispense(
        self, vol: float, location: Union[Well, Tuple, Location], s: int = 2000
    ):
        """Dispense a certain volume into a given well.

        :param vol:  Volume to dispense, in milliliters
        :type vol: float
        :param location: The location to dispense the liquid into.
        :type location: Union[Well, Tuple, Location]
        :param s: Speed at which to dispense in mm/min, defaults to 2000
        :type s: int, optional

        """
        x, y, z = Labware._getxyz(location)

        # self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._dispense(vol, s=s)
