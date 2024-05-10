"""Driver for Controlling Jubilee"""

# import websocket # for reading the machine model

import json
import os
import time
import warnings
from functools import wraps
from pathlib import Path
from typing import Union

import requests  # for issuing commands
from requests.adapters import HTTPAdapter, Retry

from science_jubilee.decks.Deck import Deck
from science_jubilee.tools.Tool import Tool

# TODO: Figure out how to print error messages from the Duet.


# copied from machine agency version, may not be needed here


def get_root_dir():
    """Return the path to the duckbot directory."""
    return Path(__file__).parent.parent


##########################################
#               ERRORS
##########################################
class MachineConfigurationError(Exception):
    """Raise this error if there is something wrong with how the machine is configured"""

    pass


class MachineStateError(Exception):
    """Raise this error if the machine is in the wrong state to perform the requested action."""

    pass


##########################################
#               DECORATORS
##########################################
def machine_homed(func):
    """Decorator used to check if the machine is homed before performing certain actions."""

    def homing_check(self, *args, **kwds):
        # Check the cached value if one exists.
        if self.simulated:
            return func(self, *args, **kwds)
        if self.axes_homed and all(self.axes_homed):
            return func(self, *args, **kwds)
        # Request homing status from the object model if not known.
        self.axes_homed = json.loads(self.gcode('M409 K"move.axes[].homed"'))["result"]
        if not all(self.axes_homed):
            raise MachineStateError("Error: machine must first be homed.")
        return func(self, *args, **kwds)

    return homing_check


def requires_deck(func):
    """Decorator used ot check if a deck has been configured before performing certain actions."""

    def deck_check(self, *args, **kwds):
        if self.deck is None:
            raise MachineStateError("Error: No deck is set up")
        return func(self, *args, **kwds)

    return deck_check


def requires_safe_z(func):
    """Decorator used to ensure the deck is at a safe height before performing certain actions."""

    def z_check(self, *args, **kwds):
        current_z = float(self.get_position()["Z"])
        if self.deck:
            safe_z = self.deck.safe_z
        else:
            safe_z = 0
            # warnings.warn(f"No deck configured, safe z height has been set to {safe_z}. Please modify this if needed.")
        if current_z < safe_z:
            self.move_to(z=safe_z + 20)
        return func(self, *args, **kwds)

    return z_check


##########################################
#             MACHINE CLASS
##########################################


class Machine:
    """A class representation of Jubilee used to send  motion commands and polling the machine state."""

    # TODO: Set this up so that a keyboard interrupt leaves the machine in a safe state - ie tool offsets correct. I had an issue
    # where I keyboard interrupted during pipette tip pickup - tip was picked up but offset was not applied, crashing machine on next move. This should not be possible.

    LOCALHOST = "192.168.1.2"

    def __init__(
        self,
        port: str = None,
        baudrate: int = 115200,
        address: str = None,
        deck_config: str = None,
        simulated: bool = False,
    ):
        """Initialize the Machine object.

        :param port: The port to connect to the machine over serial, defaults to None
        :type port: str, optional
        :param baudrate: The baudrate to use when connecting to the machine, defaults to 115200
        :type baudrate: int, optional
        :param address: The IP address of the machine. This should match what is loaded onto the config.g on the Jubilee Duet's main board, defaults to None
        :type address: str, optional
        :param deck_config: The name of the deck configuration file to load, defaults to None
        :type deck_config: str, optional
        :param simulated: Whether to simulate the machine, defaults to False
        :type simulated: bool, optional

        :raises MachineStateError: If the machine is not in the correct state to perform the requested action. This is a user error, not a machine error.
        :raises MachineConfigurationError: If the machine does nto support the indicated configuration, e.g., a tool index is already in use.
        :raises ValueError: If Jubilee returns an invalid value, e.g., the axis limit queried is not correct or query is unsuccessful.

        """
        if address != self.__class__.LOCALHOST:
            print(
                "Warning: disconnecting this application from the network will halt connection to Jubilee."
            )
        # Machine Specs

        # serial info
        self.ser = None
        self.port = port
        self.baudrate = baudrate
        self.lineEnding = "\n"  # serial stuff

        # HTTP info
        self.address = address

        # self.debug = debug
        self.simulated = simulated
        self.model_update_timestamp = 0
        self.command_ws = None
        self.wake_time = None  # Next scheduled time that the update thread updates.

        self._absolute_positioning = True
        self._absolute_extrusion = (
            True  # Extrusion positioning is set separately from other axes
        )
        self._configured_axes = None
        self._configured_tools = None
        self._active_tool_index = None  # Cached value under the @property.
        self._tool_z_offsets = None  # Cached value under the @property.
        self._axis_limits = (None, None, None)  # Cached value under the @property.
        self.axes_homed = [
            False
        ] * 4  # We have at least X/Y/Z/U axes to home. Additional axes handled below in connect()
        self.deck = None
        # TODO: this is confusingly named
        self.tools = {}  # this is the list of available tools
        self.tool = None  # this is the current active tool
        self.current_well = None

        requests_session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )

        requests_session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session = requests_session

        if deck_config is not None:
            self.load_deck(deck_config)

        self.connect()

        self._set_absolute_positioning()  # force=True)

    def connect(self):
        """Connects to Jubilee over http.

        :raises MachineStateError: If the connection to the machine is unsuccessful.
        """
        # TODO: incorporate serial connection from machine agency version
        if self.simulated:
            return
        # Do the equivalent of a ping to see if the machine is up.

        # if self.debug:
        #    print(f"Connecting to {self.address} ...")
        try:
            # "Ping" the machine by updating the only cacheable information we care about.
            # TODO: This should handle a response from self.gcode of 'None' gracefully.
            max_tries = 50
            for i in range(max_tries):
                response = json.loads(self.gcode('M409 K"move.axes[].homed"'))[
                    "result"
                ][:4]
                if len(response) == 0:
                    continue
                else:
                    break
            self.axes_homed = response

            # These data members are tied to @properties of the same name
            # without the '_' prefix.
            # Upon reconnecting, we need to flag that the @property must
            # refresh; otherwise we will retrieve old values that may be invalid.
            self._active_tool_index = None
            self._tool_z_offsets = None
            self._axis_limits = None

            # To save time upon connecting, let's just hit the API on the
            # first try for all the @properties we care about.
            self.configured_axes
            self.active_tool_index
            self.tool_z_offsets
            self.axis_limits
            # pprint.pprint(json.loads(requests.get("http://127.0.0.1/machine/status").text))
            # TODO: recover absolute/relative from object model instead of enforcing it here.
            self._set_absolute_positioning()
        except json.decoder.JSONDecodeError as e:
            raise MachineStateError("DCS not ready to connect.") from e
        except requests.exceptions.Timeout as e:
            raise MachineStateError(
                "Connection timed out. URL may be invalid, or machine may not be connected to the network."
            ) from e
        # if self.debug:
        #    print("Connected.")

    @property
    def configured_axes(self):
        """Return the configured axes of the machine.
        This is a list of all configured axis on the machine. Usually these are ['X', 'Y', 'Z', 'U']. If a tool has a
        an associated driver, it will be appended at the end of the axis list.

        :return: A list of configured axes.
        :rtype: list
        """
        if self._configured_axes is None:  # Starting from a fresh connection
            try:
                max_tries = 50
                for i in range(max_tries):
                    response = json.loads(self.gcode('M409 K"move.axes[]"'))["result"]
                    if len(response) == 0:
                        continue
                    else:
                        break
                self._configured_axes = []
                for axis in response:
                    self._configured_axes.append(axis["letter"])
            except ValueError as e:
                print("Error occurred trying to read axis limits on each axis!")
                raise e

        # Return the cached value.
        return self._configured_axes

    @property
    def configured_tools(self):
        """Returns a list of configured tools.

        :return: A list of configured tools.The tool name is queried from the `config.g` file on the machine.
        :rtype: list

        Note: This list is obtained directly from the tools added to the machine's `config.g` file.
        """

        # TODO: Compare this to loaded tools list
        if self._configured_tools is None:  # Starting from a fresh connection
            try:
                max_tries = 50
                for i in range(max_tries):
                    response = json.loads(self.gcode('M409 K"tools[]"'))["result"]
                    if len(response) == 0:
                        continue
                    else:
                        break
                self._configured_tools = {}
                for tool in response:
                    self._configured_tools[tool["number"]] = tool["name"]
            except ValueError as e:
                print("Error occurred trying to read axis limits on each axis!")
                raise e

        # Return the cached value.
        return self._configured_tools

    @property
    def active_tool_index(self):
        """Return the index of the current active tool.

        :return: The index of the current active tool. If no tool is active, returns -1.
        :rtype: int
        """

        if self._active_tool_index is None:  # Starting from a fresh connection.
            try:
                max_tries = 50
                for i in range(max_tries):
                    response = self.gcode("T")
                    if len(response) == 0:
                        continue
                    else:
                        break
                # On HTTP Interface, we get a string instead of -1 when there are no tools.
                if response.startswith("No tool"):
                    # print('active tool prop thinks theres no tool')
                    return -1
                # On HTTP Interface, we get a string instead of the tool index.
                elif response.startswith("Tool"):
                    # Recover from the string: 'Tool X is selected.'
                    self.active_tool_index = int(response.split()[1])
                else:
                    self.active_tool_index = int(response)
            except ValueError as e:
                # print("Error occurred trying to read current tool!")
                raise e
        # Return the cached value.
        return self._active_tool_index

    @active_tool_index.setter
    def active_tool_index(self, tool_index: int):
        """Sets the current tool, and toggle the old tool off."""
        if self.tool is not None:
            self.tool.is_active_tool = False

        if tool_index < 0:
            self._active_tool_index = -1
            self.tool = None
        else:
            self._active_tool_index = tool_index
            if tool_index not in self.tools:
                temp_tool = Tool(tool_index, "temp_tool")
                self.load_tool(temp_tool)
            tool = self.tools[tool_index]["tool"]
            self.tool = tool
            tool.is_active_tool = True

    @property
    def tool_z_offsets(self):
        """Return (in tool order) a list of tool's z offsets.

        Note: This list is obtained directly from the tools added to the machine's `config.g` file.

        :return: A list of tool z offsets, in the order of the tool index
        :rtype: list"""
        # Starting from fresh connection, query from the Duet.
        # if self._tool_z_offsets is None:
        try:
            max_tries = 50
            for i in range(max_tries):
                response = json.loads(self.gcode('M409 K"tools"'))["result"]
                if len(response) == 0:
                    continue
                else:
                    break

            self._tool_z_offsets = {}  # Create a fresh dictionary.
            for tool_data in response:
                if tool_data is None:
                    continue
                tool_number = tool_data["number"]
                tool_z_offset = tool_data["offsets"][2]  # Pull Z axis
                self._tool_z_offsets[tool_number] = tool_z_offset
        except ValueError as e:
            print("Error occurred trying to read z offsets of all tools!")
            raise e
        # Return the cached value.
        return self._tool_z_offsets

    @property
    def axis_limits(self):
        """Return (in XYZU order) a list of tuples specifying (min, max) axis limit

        :return: A list of tuples specifying (min, max) axis limit
        :rtype: list

        Note: This list is obtained directly from the tools added to the machine's `config.g` file.
        """
        # Starting from fresh connection, query from the Duet.
        if self._axis_limits is None:
            try:
                max_tries = 50
                for i in range(max_tries):
                    response = json.loads(self.gcode('M409 K"move.axes"'))["result"]
                    if len(response) == 0:
                        continue
                    else:
                        break
                # pprint.pprint(response)
                self._axis_limits = []  # Create a fresh list.
                for axis_data in response:
                    axis_min = axis_data["min"]
                    axis_max = axis_data["max"]
                    self._axis_limits.append((axis_min, axis_max))
            except ValueError as e:
                print("Error occurred trying to read axis limits on each axis!")
                raise e
        # Return the cached value.
        return self._axis_limits

    @property
    def position(self):
        """Returns the current machine control point in mm.

        :return: A dictionary of the machine control point in mm. The keys are the axis name, e.g. 'X'
        :rtype: dict
        """
        # Axes are ordered X, Y, Z, U, E, E0, E1, ... En, where E is a copy of E0.
        response_chunks = self.gcode("M114").split()
        positions = [float(a.split(":")[1]) for a in response_chunks[:3]]
        return positions

    ##########################################
    #                BED PLATE
    ##########################################
    def load_deck(
        self,
        deck_filename: str,
        path: str = os.path.join(os.path.dirname(__file__), "decks", "deck_definition"),
    ):
        """Load a deck configuration file onto the machine.

        :param deck_filename: The name of the deck configuration file.
        :type deck_filename: str
        :param path: The path to the deck configuration `.json` files for the labware,
                defaults to the 'deck_definition/' in the science_jubilee/decks directory.
        :type path: str, optional
        :return: A :class:`Deck` object
        :rtype: :class:`Deck`
        """
        deck = Deck(deck_filename, path=path)
        self.deck = deck
        return deck

    def gcode(self, cmd: str = "", timeout=None, response_wait: float = 30):
        """Send a G-Code command to the Machine and return the response.

        :param cmd: The G-Code command to send, defaults to ""
        :type cmd: str, optional
        :param timeout: The time to wait for a response from the machine, defaults to None
        :type timeout: float, optional
        :param response_wait: The time to wait for a response from the machine, defaults to 30
        :type response_wait: float, optional

        :return: The response message from the machine. If too long, the message might not display in the terminal.
        :rtype: str
        """

        # TODO: Add serial option for gcode commands from MA
        if self.simulated:
            print(f"sending: {cmd}")
            return None

        try:
            # Try sending the command with requests.post
            response = requests.post(
                f"http://{self.address}/machine/code", data=f"{cmd}", timeout=timeout
            ).text
            if "rejected" in response:
                raise requests.RequestException
        except requests.RequestException:
            # If requests.post fails ( not supported for standalone mode), try sending the command with requests.get
            try:
                # Paraphrased from Duet HTTP-requests page:
                # Client should query `rr_model?key=seqs` and monitor `seqs.reply`. If incremented, the command went through
                # and the response is available at `rr_reply`.
                reply_count = self.session.get(
                    f"http://{self.address}/rr_model?key=seqs"
                ).json()["result"]["reply"]
                buffer_response = self.session.get(
                    f"http://{self.address}/rr_gcode?gcode={cmd}", timeout=timeout
                )
                # wait for a response code to be appended
                # TODO: Implement retry backoff for managing long-running operations to avoid too many requests error. Right now this is handled by the generic exception catch then sleep. Real fix is some sort of backoff for things running longer than a few seconds.
                tic = time.time()
                while True:
                    try:
                        new_reply_count = self.session.get(
                            f"http://{self.address}/rr_model?key=seqs"
                        ).json()["result"]["reply"]
                        if new_reply_count != reply_count:
                            response = self.session.get(
                                f"http://{self.address}/rr_reply"
                            ).text
                            break
                        elif time.time() - tic > response_wait:
                            response = None
                            break
                    except Exception as e:
                        print("Connection error, sleeping 1 second")
                        time.sleep(2)
                        continue

            except requests.RequestException as e:
                print(f"Both `requests.post` and `requests.get` requests failed: {e}")
                response = None
        # TODO: handle this with logging. Also fix so all output goes to logs
        return response

    def _set_absolute_positioning(self):
        """Set absolute positioning for all axes except extrusion"""
        self.gcode("G90")
        self._absolute_positioning = True

    def _set_relative_positioning(self):
        """Set relative positioning for all axes except extrusion"""
        self.gcode("G91")
        self.absolute_positioning = False

    def _set_absolute_extrusion(self):
        """Set absolute positioning for extrusion"""
        self.gcode("M82")
        self._absolute_extrusion = True

    def _set_relative_extrusion(self):
        """Set relative positioning for extrusion"""
        self.gcode("M83")
        self.absolute_extrusion = False

    def push_machine_state(self):
        """Push machine state onto a stack"""
        self.gcode("M120")

    def pop_machine_state(self):
        """Recover previous machine state"""
        self.gcode("M121")

    def download_file(self, filepath: str = None, timeout: float = None):
        """Download a file into a file object. Full machine filepath must be specified.
        Example: /sys/tfree0.g

        :param filepath: The full filepath of the file to download, defaults to None
        :type filepath: str, optional
        :param timeout: The time to wait for a response from the machine, defaults to None
        :type timeout: float, optional
        :return: The file contents
        :rtype: file object
        """
        # RRF3 Only
        file_contents = requests.get(
            f"http://{self.address}/rr_download?name={filepath}", timeout=timeout
        )
        return file_contents

    def reset(self):
        """Issue a software reset."""
        # End the subscribe thread first.
        self.gcode("M999")  # Issue a board reset. Assumes we are already connected
        self.axes_homed = [False] * 4
        self.disconnect()
        print("Reconnecting...")
        for i in range(10):
            time.sleep(1)
            try:
                self.connect()
                return
            except MachineStateError as e:
                pass
        raise MachineStateError("Reconnecting failed.")

    def home_all(self):
        """Home all axes."""
        # Having a tool is only possible if the machine was already homed.
        # TODO: Check if machine is already homed and have a user input to verify clear deck to avoid wasting time by accidentally rerunning and \
        # avoid major deck wrecks
        # TODO: Catch errors where tool is already on and forward to user for fix
        if self.active_tool_index != -1:
            self.park_tool()
        self.gcode("G28")
        self._set_absolute_positioning()
        # Update homing state. Do not query the object model because of race condition.
        self.axes_homed = [True, True, True, True]  # X, Y, Z, U

        ### test to see if we can get the number of axis home using the pop_machine_state(self) !! MP 07/25/23

    def home_xyu(self):
        """Home the XYU axes. Home Y before X to prevent possibility of crashing into the tool rack."""
        self.gcode("G28 Y")
        self.gcode("G28 X")
        self.gcode("G28 U")
        self._set_absolute_positioning()
        # Update homing state. Pull Z from the object model which will not create a race condition.
        z_home_status = json.loads(self.gcode('M409 K"move.axes[].homed"'))["result"][2]
        self.axes_homed = [True, True, z_home_status, True]

    def home_x(self):
        """Home the X axis"""
        cmd = "G28 X"
        self.gcode(cmd)

    def home_y(self):
        """Home the Y axis"""
        cmd = "G28 Y"
        self.gcode(cmd)

    def home_u(self):
        """Home the U (tool) axis"""
        cmd = "G28 U"
        self.gcode(cmd)

    def home_v(self):
        """Home the V axis"""
        cmd = "G28 V"
        self.gcode(cmd)

    def home_z(self):
        """Home the Z axis.
        Note: The deck must be clear first. Will ask for user input to verify.
        """
        response = input("Is the Deck free of obstacles? [y/n]")
        if response.lower() in ["y", "yes", "Yes", "Y", "YES"]:
            self.gcode("G28 Z")
        else:
            print("The deck needs to be empty of all labware before proceeding.")
        self._set_absolute_positioning()

    def home_e(self):
        """
        Home the extruder axis (syringe)
        """
        pass

    def home_in_place(self, *args: str):
        """Set the current location of a machine axis or axes to 0."""
        for axis in args:
            if axis.upper() not in ["X", "Y", "Z", "U"]:
                raise TypeError(f"Error: cannot home unknown axis: {axis}.")
            self.gcode(f"G92 {axis.upper()}0")

    def set_tool_offset(self, tool_idx=None, x=None, y=None, z=None):
        if tool_idx is None:
            raise MachineConfigurationError("No tool index provided!")

        x = "{0:.2f}".format(x) if x is not None else None
        y = "{0:.2f}".format(y) if y is not None else None
        z = "{0:.2f}".format(z) if z is not None else None

        p_cmd = x_cmd = y_cmd = z_cmd = ""

        if tool_idx is not None:
            p_cmd = f"P{tool_idx}"
        if x is not None:
            x_cmd = f"X{x}"
        if y is not None:
            y_cmd = f"Y{y}"
        if z is not None:
            z_cmd = f"Z{z}"

        cmd = f"G10 {p_cmd} {z_cmd} {x_cmd} {y_cmd}"
        self.gcode(cmd)

    @machine_homed
    def _move_xyzev(
        self,
        x: float = None,
        y: float = None,
        z: float = None,
        e: float = None,
        v: float = None,
        s: float = 6000,
        param: str = None,
        wait: bool = False,
    ):
        """Move X/Y/Z/E/V axes. Set absolute/relative mode externally.

        :param x: x position on the bed, in whatever units have been set (default mm)
        :type x: float, optional
        :param y: y position on the bed, in whatever units have been set (default mm)
        :type y: float, optional
        :param z: z position on the bed, in whatever units have been set (default mm)
        :type z: float, optional
        :param e: extruder position, in whatever units have been set (default mm)
        :type e: float, optional
        :param v: v axis position, in whatever units have been set (default mm)
        :type v: float, optional
        :param s: speed at which to move (default 6000 mm/min)
        :type s: float, optional
        """

        x = "{0:.2f}".format(x) if x is not None else None
        y = "{0:.2f}".format(y) if y is not None else None
        z = "{0:.2f}".format(z) if z is not None else None
        e = "{0:.2f}".format(e) if e is not None else None
        v = "{0:.2f}".format(v) if v is not None else None
        s = "{0:.2f}".format(s)

        # initialize coordinates commands
        x_cmd = y_cmd = z_cmd = e_cmd = v_cmd = f_cmd = param_cmd = ""

        if x is not None:
            x_cmd = f"X{x}"
        if y is not None:
            y_cmd = f"Y{y}"
        if z is not None:
            z_cmd = f"Z{z}"
        if e is not None:
            e_cmd = f"E{e}"
        if v is not None:
            v_cmd = f"V{v}"
        if s is not None:
            f_cmd = f"F{s}"
        if param is not None:
            param_cmd = param

        cmd = f"G0 {z_cmd} {x_cmd} {y_cmd} {e_cmd} {v_cmd} {f_cmd} {param_cmd}"
        self.gcode(cmd)
        if wait:
            self.gcode(f"M400")

    def move_to(
        self,
        x: float = None,
        y: float = None,
        z: float = None,
        e: float = None,
        v: float = None,
        s: float = 6000,
        param: str = None,
        wait: bool = False,
    ):
        """Move to an absolute X/Y/Z/E/V position.

        :param x: x position on the bed, in whatever units have been set (default mm)
        :type x: float, optional
        :param y: y position on the bed, in whatever units have been set (default mm)
        :type y: float, optional
        :param z: z position on the bed, in whatever units have been set (default mm)
        :type z: float, optional
        :param e: extruder position, in whatever units have been set (default mm)
        :type e: float, optional
        :param v: v axis position, in whatever units have been set (default mm)
        :type v: float, optional
        :param s: speed at which to move (default 6000 mm/min)
        :type s: float, optional

        """
        self._set_absolute_positioning()

        self._move_xyzev(x=x, y=y, z=z, e=e, v=v, s=s, param=param, wait=wait)

    def move(
        self,
        dx: float = 0,
        dy: float = 0,
        dz: float = 0,
        de: float = 0,
        dv: float = 0,
        s: float = 6000,
        param: str = None,
        wait: bool = False,
    ):
        """Move relative to the current position

        :param dx: change in x position, in whatever units have been set (default mm)
        :type dx: float, optional
        :param dy: change in y position, in whatever units have been set (default mm)
        :type dy: float, optional
        :param dz: change in z position, in whatever units have been set (default mm)
        :type dz: float, optional
        :param de: change in e position, in whatever units have been set (default mm)
        :type de: float, optional
        :param dv: change in v position, in whatever units have been set (default mm)
        :type dv: float, optional
        :param s:  speed at which to move (default 6000 mm/min)
        :type s: float, optional
        """
        # Check that the relative move doesn't exceed user-defined limit
        # By default, ensure that it won't crash into the parked tools
        if any(self._axis_limits):
            x_limit, y_limit, z_limit = self._axis_limits[0:3]
            pos = self.get_position()
            if (
                x_limit
                and dx != 0
                and (
                    (float(pos["X"]) + dx > x_limit[1])
                    or (float(pos["X"]) + dx < x_limit[0])
                )
            ):
                raise MachineStateError("Error: Relative move exceeds X axis limit!")
            if (
                y_limit
                and dy != 0
                and (
                    (float(pos["Y"]) + dy > y_limit[1])
                    or (float(pos["Y"]) + dy < y_limit[0])
                )
            ):
                raise MachineStateError("Error: Relative move exceeds Y axis limit!")
            if (
                z_limit
                and dz != 0
                and (
                    (float(pos["Z"]) + dz > z_limit[1])
                    or (float(pos["Z"]) + dz < z_limit[0])
                )
            ):
                raise MachineStateError("Error: Relative move exceeds Z axis limit!")
        self._set_relative_positioning()

        self._move_xyzev(x=dx, y=dy, z=dz, e=de, v=dv, s=s, param=param, wait=wait)

    def dwell(self, t: float, millis: bool = True):
        """Pauses the machine for a period of time.

        :param t: time to pause, in milliseconds by default
        :type t: float
        :param millis: boolean, set to false to use seconds. default unit is milliseconds.
        :type millis: bool, optional
        """

        param = "P" if millis else "S"
        cmd = f"G4 {param}{t}"

        self.gcode(cmd)

    def safe_z_movement(self):
        """Move the Z axis to a safe height to avoid crashing into labware."""
        # TODO is this redundant? can we reuse decorator ?
        current_z = self.get_position()["Z"]
        safe_z = self.deck.safe_z
        if float(current_z) < safe_z:
            self.move_to(z=safe_z + 20)
        else:
            pass

    def _get_tool_index(self, tool_item: Union[int, Tool, str]):
        """Return the tool index from the provided tool item.

        This method is allows the user to call a toll by its index, its name, or to use a :class:`Tool` object
        directly.

        :param tool_item: The tool index, name, or :class:`Tool` object
        :type tool_item: Union[int, Tool, str]
        :return: The tool index
        :rtype: int
        """
        if type(tool_item) == int:
            assert tool_item in set(self.tools.values()), f"Tool {tool_item} not loaded"
            return tool_item
        elif type(tool_item) == str:
            assert tool_item in set(self.tools.values()), f"Tool {tool_item} not loaded"
            return self.tools[tool_item]
        elif isinstance(tool_item, Tool):
            assert tool_item.index in set(
                self.tools.keys()
            ), f"Tool {tool_item} not loaded"
            return tool_item.index
        else:
            raise ValueError(f"Unknown tool format {type(tool_item)}")

    def load_tool(self, tool: Tool = None):
        """Add a new tool for use on the machine."""
        # TODO: Fix this so if you reload you don't break everything
        name = tool.name
        idx = tool.index

        # Ensure that the provided tool index and name are unique.
        if idx in self.tools:
            # Handle the case that connection was established with a tool equipped
            if self.tools[idx]["name"] == "temp_tool":
                tool.is_active_tool = True
        for loaded_tool in self.tools.values():
            if loaded_tool["name"] is name and loaded_tool["tool"].index != idx:
                raise MachineConfigurationError("Error: Tool name already in use.")

        self.tools[idx] = {"name": name, "tool": tool}
        tool._machine = self
        tool.post_load()
        tool.tool_offset = self.tool_z_offsets[idx]

    def reload_tool(self, tool: Tool = None):
        """Update a tool which has already been loaded."""
        name = tool.name
        idx = tool.index

        # Ensure that the provided tool index and name are unique.
        if idx not in self.tools:
            raise MachineConfigurationError(
                f"Error: No tool with index {idx} to update."
            )
        for loaded_tool in self.tools.values():
            if loaded_tool["name"] is name:
                raise MachineConfigurationError("Error: Tool name already in use.")

        self.tools[idx] = {"name": name, "tool": tool}
        tool._machine = self

    # TODO: Unload tool method

    @requires_safe_z
    def pickup_tool(self, tool_id: Union[int, str, Tool]):
        """Pick up the tool specified by a tool index, name or :class:`Tool` object.

        :param tool_id: The tool index, name, or :class:`Tool` object
        :type tool_id: Union[int, str, Tool]
        :raises MachineConfigurationError: If the tool is not loaded on the machine.
        :raises ValueError: If the indicated tool_id is not of type Union[int, str, Tool].
        """
        # TODO: Make sure axis limits are checked and not exceeded when picking up pipette
        if isinstance(
            tool_id, int
        ):  # Accept either tool index, tool name, or reference to the tool itself
            if tool_id in self.tools:
                tool_index = tool_id
            else:
                raise MachineConfigurationError(
                    f"Error: No tool with index {tool_id} is currently loaded."
                )
        elif isinstance(tool_id, str):
            tool_index = None
            for loaded_tool_index in self.tools:
                if self.tools[loaded_tool_index]["name"] is tool_id:
                    tool_index = loaded_tool_index
                    break
            if tool_index is None:
                raise MachineConfigurationError(
                    f"Error: No tool with name {tool_id} is currently loaded."
                )
        elif isinstance(tool_id, Tool):
            tool_index = None
            for loaded_tool_index in self.tools:
                if self.tools[loaded_tool_index]["tool"] is tool_id:
                    tool_index = loaded_tool_index
                    break
            if tool_index is None:
                raise MachineConfigurationError(
                    f"Error: No tool of type {tool_id} is currently loaded."
                )
        else:
            raise ValueError(f"Unknown tool format {type(tool_id)}")

        #         self.safe_z_movement()
        self.gcode(f"T{tool_index}")
        self.active_tool_index = tool_index
        self.tools[tool_index]["tool"].is_active_tool = True

    @requires_safe_z
    def park_tool(self):
        """Park the current tool adn cahnges active tool index to `-1`."""
        # self.safe_z_movement()
        self.gcode("T-1")
        # Update the cached value to prevent read delays.
        current_tool_index = self.active_tool_index
        self.tools[current_tool_index]["tool"].is_active_tool = False
        self._active_tool_index = -1

    def get_position(self):
        """Get the current position of the machine control point in mm.

        :return: A dictionary of the machine control point in mm. The keys are the axis name, e.g. 'X'
        :rtype: dict
        """

        max_tries = 50
        for i in range(max_tries):
            resp = self.gcode("M114")
            if "Count" not in resp:
                continue
            else:
                break
        positions = {}
        keyword = " Count "  # this is the keyword hosts like e.g. pronterface search for to track position
        keyword_idx = resp.find(keyword)

        count = 0
        if keyword_idx > -1:
            resp = resp[:keyword_idx]
            position_elements = resp.split(" ")
            for e in position_elements:
                axis, pos = e.split(":", 2)
                positions[axis] = pos

        return positions

    def load_labware(
        self, labware_filename: str, slot: int, path: str = None, order: str = "rows"
    ):
        """Function that loads a labware and associates it with a specific slot on the deck.
         The slot offset is also applied to the labware asocaite with it.

        :param labware_filename: The name of the labware configuration file.
        :type labware_filename: str
        :param slot: The index of the slot to load the labware into.
        :type slot: int
        :param path: The path to the labware configuration `.json` files for the labware.
        :type path: str, optional
        :param order: The order in which the labware is arranged on the deck.
                Can be 'rows' or 'columns', defaults to 'rows'.
        :type order: str, optional
        :return: The :class:`Labware` object that has been loaded into the slot.
        :rtype: :class:`Labware`
        """
        if path is not None:
            labware = self.deck.load_labware(
                labware_filename, slot, path=path, order=order
            )
        else:
            labware = self.deck.load_labware(labware_filename, slot, order=order)

        return labware

    # ***************MACROS***************
    def tool_lock(self):
        """Runs Jubilee tool lock macro. Assumes tool_lock.g macro exists."""
        cmd = 'M98 P"0:/macros/tool_lock.g"'
        self.gcode(cmd)

    def tool_unlock(self):
        """Runs Jubilee tool unlock macro. Assumes tool_unlock.g macro exists."""
        cmd = 'M98 P"0:/macros/tool_unlock.g"'
        self.gcode(cmd)

    def disconnect(self):
        """Close the connection."""
        # Nothing to do?
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.disconnect()
