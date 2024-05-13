import json
import os
import random
import warnings
from typing import Tuple

import numpy as np

from science_jubilee.labware.Labware import Well
from science_jubilee.tools.Tool import Tool, requires_active_tool


class Loop(Tool):
    """A class representation of an inoculation loop.

    :param Tool: The base tool class
    :type Tool: :class:`Tool`
    """

    def __init__(self, index, name):
        """Constructor method"""
        super().__init__(index, name)

    @requires_active_tool
    def transfer(
        self,
        source: Well = None,
        destination: Well = None,
        s: int = 2000,
        sweep_x: float = 5,
        sweep_y: float = 5,
        sweep_z: float = 10,
        sweep_speed: float = 100,
        up_speed: float = 800,
        randomize_pickup: bool = False,
    ):
        """Dip into a number of (source, destination) well pairs. Used for transferring items from source to destination.

        :param source: Source well, defaults to None
        :type source: :class:`Well`, optional
        :param destination: Destination well, defaults to None
        :type destination: :class:`Well`, optional
        :param s: Movement speed in mm/min, defaults to 2000
        :type s: int, optional
        :param sweep_x: Distance (in mm) to sweep in the x direction to pick up material, defaults to 5
        :type sweep_x: float, optional
        :param sweep_y: Distance (in mm) to sweep in the y direction to pick up material, defaults to 5
        :type sweep_y: float, optional
        :param sweep_z: Distance (in mm) to move in the z direction to pick up material, defaults to 10
        :type sweep_z: float, optional
        :param sweep_speed: Speed (in mm/min) at which to sweep to pick up material, defaults to 100
        :type sweep_speed: float, optional
        :param up_speed: Speed to move out of well (in mm/min), defaults to 800
        :type up_speed: float, optional
        :param randomize_pickup: Move to a random position in the source well to pick up material, defaults to False
        :type randomize_pickup: bool, optional
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
            xs, ys, zs = self._get_xyz(well=source_well)
            if (
                randomize_pickup
            ):  # to make sure we don't try to pickup from an empty region
                r = 20
                rx = random.randint(-r, r)
                ry = random.randint(-r, r)
                xs += rx
                ys += ry
            xd, yd, zd = self._get_xyz(well=destination_well)

            self._machine.safe_z_movement()
            self._machine.move_to(x=xs, y=ys)
            self._machine.move_to(z=zs + 5)
            # slowly sweep in the reservoir to pick up duckweed
            # can tune these default values
            self._machine.move(dx=sweep_x, s=sweep_speed)
            self._machine.move(dy=sweep_y, s=sweep_speed)
            self._machine.move(dz=sweep_z, s=up_speed)
            self.current_well = source_well
            # self._aspirate(vol, s=s)

            self._machine.safe_z_movement()
            self._machine.move_to(x=xd, y=yd)
            self._machine.move_to(z=zd + 5)
            # sweep again to drop off duckweed
            # make smaller movements and move opposite direction
            self._machine.move(dx=sweep_x / 2, s=sweep_speed)
            self._machine.move(dy=-sweep_y, s=sweep_speed)
            self._machine.dwell(250)  # give the duckweed time to release
            self.current_well = destination_well
            # self._dispense(vol, s=s)

    @staticmethod
    def _get_xyz(well: Well = None, location: Tuple[float] = None):
        """Get the (x,y,z) position of a well.

        :param well: The well to fetch position of, defaults to None
        :type well: :class:`Well`, optional
        :param location: Directly specify an (x,y,z) location, defaults to None
        :type location: Tuple[float], optional
        :raises ValueError: Must specify either a well or a location
        :return: The well location
        :rtype: Tuple[float, float, float]
        """
        if well is not None and location is not None:
            raise ValueError("Specify only one of Well or x,y,z location")
        elif well is not None:
            x, y, z = well.x, well.y, well.z
        else:
            x, y, z = location
        return x, y, z

    @staticmethod
    def _get_top_bottom(well: Well = None):
        """Get the top and bottom heights of a well.

        :param well: The well to fetch position of, defaults to None
        :type well: Well, optional
        :return: The z-height of the top and bottom of the well
        :rtype: Tuple[float, float]
        """
        top = well.top
        bottom = well.bottom
        return top, bottom
