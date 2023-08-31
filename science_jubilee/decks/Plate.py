from pathlib import Path


class PlateStateError(Exception):
    """Raise this error if the plate is in the wrong state to perform such a command."""

    pass


class PlateConfigurationError(Exception):
    """Raise this error if there is something wrong with how the plate is configured"""

    pass


class Plate:
    def __init__(self, machine, name):
        self._machine = machine
        self._name = name

    def get_root_dir(self):
        return Path(__file__).parent.parent.parent
