import json
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


class Syringe(Tool):
    """A class representation of a syringe.

    :param Tool: The base tool class
    :type Tool: :class:`Tool`
    """

    def __init__(self, index, name, config):
        """Constructor method"""
        super().__init__(index, name)

        self.min_range = 0
        self.max_range = None
        self.mm_to_ml = None
        self.e_drive = "E"

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

        self._machine.safe_z_movement()
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

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._dispense(vol, s=s)

    @requires_active_tool
    def transfer(
        self,
        vol: float,
        s: int = 2000,
        source: Well = None,
        destination: Well = None,
        mix_before: tuple = None,
        mix_after: tuple = None,
    ):
        """Transfer liquid from source well(s) to a set of destination well(s). Accommodates one-to-one, one-to-many, many-to-one, and uneven transfers.

        :param vol: Volume to transfer in milliliters
        :type vol: float
        :param s: Speed at which to aspirate and dispense in mm/min, defaults to 2000
        :type s: int, optional
        :param source: A source well or set of source wells, defaults to None
        :type source: Well, optional
        :param destination: A destination well or set of destination wells, defaults to None
        :type destination: Well, optional
        :param mix_before: Mix the source well before transfering, defaults to None
        :type mix_before: tuple, optional
        :param mix_after: Mix the destination well after transfering, defaults to None
        :type mix_after: tuple, optional
        """
        if type(source) != list:
            source = [source]
        if type(destination) != list:
            destination = [destination]

        # Assemble tuples of (source, destination)
        num_source_wells = len(source)
        num_destination_wells = len(destination)
        if num_source_wells == num_destination_wells:  # n to n transfers
            pass
        elif (
            num_source_wells == 1 and num_destination_wells > 1
        ):  # one to many transfers
            source = list(np.repeat(source, num_destination_wells))
        elif (
            num_source_wells > 1 and num_destination_wells == 1
        ):  # many to one transfers
            destination = list(np.repeat(destination, num_source_wells))
        elif num_source_wells > 1 and num_destination_wells > 1:  # uneven transfers
            # for uneven transfers, find least common multiple to pair off wells
            # raise a warning, as this might be a mistake
            # this mimics OT-2 behavior
            least_common_multiple = np.lcm(num_source_wells, num_destination_wells)
            source_repeat = least_common_multiple / num_source_wells
            destination_repeat = least_common_multiple / num_destination_wells
            source = list(np.repeat(source, source_repeat))
            destination = list(np.repeat(destination, destination_repeat))
            warnings.warn("Warning: Uneven source & destination wells specified.")

        source_destination_pairs = list(zip(source, destination))
        for source_well, destination_well in source_destination_pairs:
            # TODO: Large volume transfers which exceed tool capacity should be split up into several transfers
            xs, ys, zs = Labware._getxyz(source_well)
            xd, yd, zd = Labware._getxyz(destination_well)

            self._machine.safe_z_movement()
            self._machine.move_to(x=xs, y=ys)
            self._machine.move_to(z=zs + 5)
            self.current_well = source_well
            self._aspirate(vol, s=s)

            #             if mix_before:
            #                 self.mix(mix_before[0], mix_before[1])
            #             else:
            #                 pass

            self._machine.safe_z_movement()
            self._machine.move_to(x=xd, y=yd)
            self._machine.move_to(z=zd + 5)
            self.current_well = destination_well
            self._dispense(vol, s=s)


#             if mix_after:
#                 self.mix(mix_after[0], mix_after[1])
#             else:
#                 pass
