import json
import logging
import os
from typing import Union

_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")


def _find_config(filename: str, path: str = None) -> str:
    """Return the full path to a config file.

    If *path* is given explicitly, look there.  Otherwise check ``configs/user/``
    first (user-specific calibration), then fall back to ``configs/examples/``
    (shipped example files).
    """
    if path is not None:
        return os.path.join(path, filename)
    user = os.path.join(_CONFIGS_DIR, "user", filename)
    if os.path.isfile(user):
        return user
    return os.path.join(_CONFIGS_DIR, "examples", filename)

_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")


def _find_config(filename: str, path: str = None) -> str:
    """Return the full path to a config file.

    If *path* is given explicitly, look there.  Otherwise check ``configs/user/``
    first (user-specific calibration), then fall back to ``configs/examples/``
    (shipped example files).
    """
    if path is not None:
        return os.path.join(path, filename)
    user = os.path.join(_CONFIGS_DIR, "user", filename)
    if os.path.isfile(user):
        return user
    return os.path.join(_CONFIGS_DIR, "examples", filename)

from science_jubilee.tools.Tool import Tool


class PeristalticPumps(Tool):
    """
    class representation of peristaltic pumps. Due to duet-level axis definition requirements, currently requires an accompanying PumpDispenser tool to control pumps.

    :param n_pumps: Number of peristaltic pumps
    :type n_pumps: int
    :param steps_per_mL: stepper motor steps to turn pump to pump 1mL of liquid. calibrate gravimetrically. Can pass a float or int to apply same value to each pump or list to apply unique value to each pump.
    :type steps_per_mL: float, int, list
    :param tool_axis: Motion axis tool is defined to on duet. Default E
    :type tool_axis: str
    :param name: name of tool
    :type name: str
    """

    def __init__(
        self,
        n_pumps: int,
        steps_per_ml: Union[float, int, list],
        tool_axis: str = "E",
        name: str = "dispenser_pumps",
    ):
        self.tool_axis = tool_axis
        self.n_pumps = n_pumps
        self.name = name

        if isinstance(steps_per_ml, float) or isinstance(steps_per_ml, int):
            self.steps_per_ml = [steps_per_ml] * n_pumps
        elif isinstance(steps_per_ml, list):
            assert (
                len(steps_per_ml) == n_pumps
            ), "steps per ml list length much equal number of pumps"
            self.steps_per_ml = steps_per_ml

    @classmethod
    def from_config(
        cls,
        config_file: str,
        path: str = None,
    ):
        """Initialize a PeristalticPumps object from a config file

        :param config_file: The name of the config file containing the pump parameters
        :type config_file: str
        :param path: Directory containing the config file.  If omitted, ``configs/user/``
                is checked first, then ``configs/examples/``.
        :type path: str, optional
        :returns: A :class:`PeristalticPumps` object
        :rtype: :class:`PeristalticPumps`
        """
        config = _find_config(config_file, path)
        with open(config) as f:
            kwargs = json.load(f)
        print(kwargs)
        return cls(**kwargs)

    def post_load(self):
        """
        After tool load, set steps per mm on machine
        """
        # set steps per mL on machine
        steps_per_ml = self.steps_per_ml

        gcode = f"M92 {self.tool_axis}" + ":".join(
            [str(stpml) for stpml in steps_per_ml]
        )
        print(gcode)
        self._machine.gcode(gcode)

        return

    def pump(self, volume: Union[int, float, list]):
        """transfer volume using pump

        :param volume: volume to pump. Specify a number (int/float) to pump same amount from all pumps simultaneously, or a list of numbers to pump unique amount from each pump.
        :type volume: int, float, list
        """
        # dispense given volume
        if isinstance(volume, list):
            assert isinstance(volume[0], float) or isinstance(
                volume[0], int
            ), "Volume list must be floats or ints"
            pass

        elif isinstance(volume, float) or isinstance(volume, int):
            volume = [volume] * self.n_pumps

        else:
            raise TypeError("Volume must be an int, float, or list of ints or floats")

        stringvol = ":".join([str(v) for v in volume])

        # sticking with a direct gcode to send here makes sense: no 3-motor on axis support in movement code, and no risk of crashing anything here
        self._machine.gcode(f"G1 {self.tool_axis}{stringvol}")
