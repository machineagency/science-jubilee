"""Driver for Controlling Jubilee"""
#import websocket # for reading the machine model
import requests # for issuing commands
import json
import time
import os
# import curses
# import pprint
#from inpromptu import Inpromptu, cli_method
from typing import Union
from functools import wraps
from labware.Utils import json2dict
from decks.Deck import Deck
from tools.Tool import Tool
#TODO: Figure out how to print error messages from the Duet.

##########################################
#               ERRORS
##########################################
class MachineConfigurationError(Exception):
    """Raise this error if there is something wrong with how the machine is configured"""
    pass

class MachineStateError(Exception):
    """Raise this error if the machine is in the wrong state to perform the requested action."""
    pass


def machine_is_homed(func):
    def homing_check(self, *args, **kwds):
        # Check the cached value if one exists.
        if self.axes_homed and all(self.axes_homed):
            return func(self, *args, **kwds)
        # Request homing status from the object model if not known.
        self.axes_homed = json.loads(self.gcode("M409 K\"move.axes[].homed\""))["result"][:4]
        if not all(self.axes_homed):
            raise MachineStateError("Error: machine must first be homed.")
        return func(self, *args, **kwds)
    return homing_check


class Machine():
    """Driver for sending motion cmds and polling the machine state."""

    LOCALHOST = "192.168.1.2"

    def __init__(self, address=LOCALHOST, debug=False, simulated=False, reset=False, deck_config: str=None):
        """Start with sane defaults. Setup command and subscribe connections."""
        if address != self.__class__.LOCALHOST:
            print("Warning: disconnecting this application from the network will halt connection to Jubilee.")
        # Machine Specs
        self.address = address
        self.debug = debug
        self.simulated = simulated
        self.model_update_timestamp = 0
        self.command_ws = None
        self.wake_time = None # Next scheduled time that the update thread updates.

        self._absolute_positioning = True
        self._absolute_extrusion = True # Extrusion positioning is set separately from other axes
        self._configured_axes = None
        self._configured_tools = None
        self._active_tool_index = None # Cached value under the @property.
        self._tool_z_offsets = None # Cached value under the @property.
        self._axis_limits = None # Cached value under the @property.
        self.axes_homed = [False]*4 # We have at least X/Y/Z/U axes to home. Additional axes handled below in connect()
        self.deck = None
        self.tools = {}
        self.current_well = None

        if deck_config is not None:
            self.load_deck(deck_config)

        self.connect()

        if reset:
            self.reset() # also does a reconnect.
        self._set_absolute_positioning()#force=True)

    def connect(self):
        """Connect to Jubilee over http."""
        if self.simulated:
            return
        # Do the equivalent of a ping to see if the machine is up.
        if self.debug:
            print(f"Connecting to {self.address} ...")
        try:
            # "Ping" the machine by updating the only cacheable information we care about.
            max_tries = 25
            for i in range(max_tries):
                response = json.loads(self.gcode("M409 K\"move.axes[].homed\""))["result"][:4]
                if len(response) == 0 :
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
            #pprint.pprint(json.loads(requests.get("http://127.0.0.1/machine/status").text))
            # TODO: recover absolute/relative from object model instead of enforcing it here.
            self._set_absolute_positioning()
        except json.decoder.JSONDecodeError as e:
            raise MachineStateError("DCS not ready to connect.") from e
        except requests.exceptions.Timeout as e:
            raise MachineStateError("Connection timed out. URL may be invalid, or machine may not be connected to the network.") from e
        if self.debug:
            print("Connected.")

    @property
    def configured_axes(self):
        """Return the configured axes of the machine."""
        if self._configured_axes is None: # Starting from a fresh connection
            try:
                max_tries = 25
                for i in range(max_tries):
                    response = json.loads(self.gcode('M409 K"move.axes[]"'))["result"]
                    if len(response) == 0 :
                        continue
                    else:
                        break  
                self._configured_axes = []
                for axis in response:
                    self._configured_axes.append(axis['letter'])
            except ValueError as e:
                print("Error occurred trying to read axis limits on each axis!")
                raise e
        
        # Return the cached value.
        return self._configured_axes
    
    @property
    def configured_tools(self):
        """Return the configured tools."""
        if self._configured_tools is None: # Starting from a fresh connection
            try:
                max_tries = 25
                for i in range(max_tries):
                    response = json.loads(self.gcode('M409 K"tools[]"'))["result"]
                    if len(response) == 0 :
                        continue
                    else:
                        break  
                self._configured_tools = {}
                for tool in response:
                    self._configured_tools[tool['number']] = tool['name']
            except ValueError as e:
                print("Error occurred trying to read axis limits on each axis!")
                raise e
        
        # Return the cached value.
        return self._configured_tools


    def gcode(self, cmd: str = "", response_wait: float = 10):
        """Send a GCode cmd; return the response"""
        if self.debug or self.simulated:
            print(f"sending: {cmd}")
        if self.simulated:
            return None
        # Updated to current duet web API. Response needs to be fetched separately and will be ready once the operation is complete on the machine 
        # we need to watch the 'reply count' and request the new response when it increments
        old_reply_count = requests.get(f'http://192.168.1.2/rr_model?key=seqs').json()['result']['reply']
        buffer_response = requests.get(f'http://192.168.1.2/rr_gcode?gcode={cmd}')
        # wait for a response code to be appended
        tic = time.time()
        while True:
            new_reply_count = requests.get(f'http://192.168.1.2/rr_model?key=seqs').json()['result']['reply']
            if new_reply_count != old_reply_count:
                response = requests.get(f'http://192.168.1.2/rr_reply').text
                break
            elif time.time() - tic > response_wait:
                response = None
                break
            time.sleep(0.02)

        if self.debug:
            print(f"received: {response}")
            #print(json.dumps(r, sort_keys=True, indent=4, separators=(',', ':')))
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
        """Download the file into a file object. Full filepath must be specified.
        Example: /sys/tfree0.g
        """
        # RRF3 Only
        file_contents = requests.get(f"http://{self.address}/rr_download?name={filepath}",
                                     timeout=timeout)
        return file_contents


    def reset(self):
        """Issue a software reset."""
        # End the subscribe thread first.
        self.gcode("M999") # Issue a board reset. Assumes we are already connected
        self.axes_homed = [False]*4
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
        # Having a tool is only possible if the machine was already homed.
        if self.active_tool_index != -1:
            self.park_tool()
        self.gcode("G28")
        self._set_absolute_positioning()
        # Update homing state. Do not query the object model because of race condition.
        self.axes_homed = [True, True, True, True] # X, Y, Z, U
        
        ### test to see if we can get the number of axis home using the pop_machine_state(self) !! MP 07/25/23


    def home_xyu(self):
        """Home the XY axes.
        Home Y before X to prevent possibility of crashing into the tool rack.
        """
        self.gcode("G28 Y")
        self.gcode("G28 X")
        self.gcode("G28 U")
        self._set_absolute_positioning()
        # Update homing state. Pull Z from the object model which will not create a race condition.
        z_home_status = json.loads(self.gcode("M409 K\"move.axes[].homed\""))["result"][2]
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
        Note that the Deck must be clear first.
        """
        response = input("Is the Deck free of obstacles? [y/n]")
        if response.lower() in ["y", "yes", "Yes", "Y", "YES"]:
            self.gcode("G28 Z")
        else:
            print('The deck needs to be empty of all labware before proceeding.')
        self._set_absolute_positioning()

    def home_e(self):
        """
        Home the extruder axis (syringe)
        """
        pass

    def home_in_place(self, *args: str):
        """Set the current location of a machine axis or axes to 0."""
        for axis in args:
            if axis.upper() not in ['X', 'Y', 'Z', 'U']:
                raise TypeError(f"Error: cannot home unknown axis: {axis}.")
            self.gcode(f"G92 {axis.upper()}0")

    @machine_is_homed
    def _move_xyzev(self, x: float = None, y: float = None, z: float = None, e: float = None,
                     v: float = None, s: float = 6000, param: str=None , wait: bool = False):
        """Move X/Y/Z/E/V axes. Set absolute/relative mode externally.

        Parameters
        ----------
        x: x position on the bed, in whatever units have been set (default mm)
        y: y position on the bed, in whatever units have been set (default mm)
        z: z position on the bed, in whatever units have been set (default mm)
        e: extruder position, in whatever units have been set (default mm)
        v: v axis position, in whatever units have been set (default mm)
        s: speed at which to move (default 6000 mm/min)

        Returns
        -------
        Nothing

        """
        
        if v and (v > 200 or v < 0):
            v=None
            raise Exception('V cannot be less than O or greater than 200')
        
        x = "{0:.2f}".format(x) if x is not None else None
        y = "{0:.2f}".format(y) if y is not None else None
        z = "{0:.2f}".format(z) if z is not None else None
        e = "{0:.2f}".format(e) if e is not None else None
        v = "{0:.2f}".format(v) if v is not None else None
        s = "{0:.2f}".format(s)

        # initialize coordinates commands
        x_cmd = y_cmd = z_cmd = e_cmd = v_cmd = f_cmd = param_cmd = ''
        
        if x is not None:
            x_cmd = f'X{x}'
        if y is not None:
            y_cmd = f'Y{y}'
        if z is not None:
            z_cmd = f'Z{z}'
        if e is not None:
            e_cmd = f'E{e}'
        if v is not None:
            v_cmd = f'V{v}'
        if s is not None:
            f_cmd = f'F{s}'
        if param is not None:
            param_cmd = param
        
        cmd = f"G0 {z_cmd} {x_cmd} {y_cmd} {e_cmd} {v_cmd} {f_cmd} {param_cmd}"
        self.gcode(cmd)
        if wait:
            self.gcode(f"M400")

    def move_to(self, x: float = None, y: float = None, z: float = None, e: float = None,
                 v: float = None, s: float = 6000, param: str =None, wait: bool = False):
        """Move to an absolute X/Y/Z/E/V position.

        Parameters
        ----------
        x: x position on the bed, in whatever units have been set (default mm)
        y: y position on the bed, in whatever units have been set (default mm)
        z: z position on the bed, in whatever units have been set (default mm)
        e: extruder position, in whatever units have been set (default mm)
        v: v axis position, in whatever units have been set (default mm)
        s: speed at which to move (default 6000 mm/min)
        force_extrusion: whether to force extrusion to also be absolute positioning (default True)

        Returns
        -------
        Nothing

        """
        self._set_absolute_positioning()
        # if force:
        #     self._set_absolute_extrusion()
        
        self._move_xyzev(x = x, y = y, z = z, e = e, v = v, s = s, param=param, wait=wait)

    def move(self, dx: float = None, dy: float = None, dz: float = None, de: float = None,
              dv: float = None, s: float = 6000,  param: str =None, wait: bool = False):
        """Move relative to the current position

        Parameters
        ----------
        dx: change in x position, in whatever units have been set (default mm)
        dy: change in y position, in whatever units have been set (default mm)
        dz: change in z position, in whatever units have been set (default mm)
        de: change in e position, in whatever units have been set (default mm)
        dv: change in v position, in whatever units have been set (default mm)
        s:  speed at which to move (default 6000 mm/min)
        force_extrusion: whether to force extrusion to also be relative positioning (default True)

        Returns
        -------
        Nothing

        """
        self._set_relative_positioning()
        # if force:
        #     self._set_relative_extrusion()
        
        self._move_xyzev(x = dx, y = dy, z = dz, e = de, v = dv, s = s, param=param, wait=wait)

    def safe_z_movement(self):
        current_z = self.get_position()['Z']
        safe_z = self.deck.safe_z
        if float(current_z) < safe_z :
            self.move_to(z = safe_z + 20)
        else:
            pass

    def dwell(self, t: float, millis: bool =True):
        """Pause the machine for a period of time.

        Parameters
        ----------
        t: time to pause, in milliseconds by default
        millis (optional): boolean, set to false to use seconds. default unit is milliseconds.

        Returns
        -------
        Nothing

        """
        
        param = 'P' if millis else 'S'
        cmd = f"G4 {param}{t}"
        
        self.gcode(cmd)
    
    @property
    def position(self):
        """Returns the machine control point in mm."""
        # Axes are ordered X, Y, Z, U, E, E0, E1, ... En, where E is a copy of E0.
        response_chunks = self.gcode("M114").split()
        positions = [float(a.split(":")[1]) for a in response_chunks[:3]]
        return positions

    def _get_tool_index(self, tool_item: Union[int, Tool, str]):
        if type(tool_item) == int:
            assert tool_item in set(self.tools.values()), f"Tool {tool_item} not loaded"
            return tool_item
        elif type(tool_item) == str:
            assert tool_item in set(self.tools.keys()), f"Tool {tool_item} not loaded"
            return self.tools[tool_item]
        elif isinstance(tool_item, Tool):
            assert tool_item.index in set(self.tools.values()), f"Tool {tool_item} not loaded"
            return tool_item.index
        else:
            raise ValueError(f"Unknown tool format {type(tool_item)}")


    def pickup_tool(self, tool_item: Union[int, Tool, str] = None):
        """Pick up the tool specified by tool index."""
        tool_index = self._get_tool_index(tool_item=tool_item)
        
        self.gcode(f"T{tool_index}")
        # Update the cached value to prevent read delays.
        self._active_tool_index = tool_index


    def park_tool(self):
        """Park the current tool."""
        self.gcode("T-1")
        # Update the cached value to prevent read delays.
        self._active_tool_index = -1


    @property
    def active_tool_index(self):
        """Return the index of the current tool."""
        #print('calling the property func')
        #print(self._active_tool_index)
        if self._active_tool_index is None: # Starting from a fresh connection.
            try:
                max_tries = 25
                for i in range(max_tries):
                    response = self.gcode("T")
                    if len(response)==0:
                        continue
                    else:
                        break              
                # On HTTP Interface, we get a string instead of -1 when there are no tools.
                if response.startswith('No tool'):
                    #print('active tool prop thinks theres no tool')
                    return -1
                # On HTTP Interface, we get a string instead of the tool index.
                elif response.startswith('Tool'):
                    # Recover from the string: 'Tool X is selected.'
                    self.active_tool_index = int(response.split()[1])
                else:
                    self.active_tool_index = int(response)
            except ValueError as e:
                #print("Error occurred trying to read current tool!")
                raise e
        # Return the cached value.
        return self._active_tool_index

    @property
    def tool_z_offsets(self):
        """Return (in tool order) a list of tool's z offsets"""
        # Starting from fresh connection, query from the Duet.
        if self._tool_z_offsets is None:
            try:
                max_tries = 25
                for i in range(max_tries):
                    response = json.loads(self.gcode('M409 K"tools"'))["result"]
                    if len(response) == 0 :
                        continue
                    else:
                        break               
                #pprint.pprint(response)
                self._tool_z_offsets = [] # Create a fresh list.
                for tool_data in response:
                    tool_z_offset = tool_data["offsets"][2] # Pull Z axis
                    self._tool_z_offsets.append(tool_z_offset)
            except ValueError as e:
                print("Error occurred trying to read z offsets of all tools!")
                raise e
        # Return the cached value.
        return self._tool_z_offsets

    def get_position(self):
        """Get the current position, returns a dictionary with X/Y/Z/U/E/V keys"""

        max_tries = 25
        for i in range(max_tries):
            resp = self.gcode("M114")
            if "Count" not in resp:
                continue
            else:
                break

        positions = {}
        keyword = " Count " # this is the keyword hosts like e.g. pronterface search for to track position
        keyword_idx = resp.find(keyword)
        
        count = 0
        if keyword_idx > -1:
            resp = resp[:keyword_idx]
            position_elements = resp.split(' ')
            for e in position_elements:
                axis, pos = e.split(':', 2)
                positions[axis] = pos          

        return positions
    
    @property
    def axis_limits(self):
        """Return (in XYZU order) a list of tuples specifying (min, max) axis limit"""
        # Starting from fresh connection, query from the Duet.
        if self._axis_limits is None:
            try:
                max_tries = 25
                for i in range(max_tries):
                    response = json.loads(self.gcode("M409 K\"move.axes\""))["result"]
                    if len(response) == 0 :
                        continue
                    else:
                        break
                #pprint.pprint(response)
                self._axis_limits = [] # Create a fresh list.
                for axis_data in response:
                    axis_min = axis_data["min"]
                    axis_max = axis_data["max"]
                    self._axis_limits.append((axis_min, axis_max))
            except ValueError as e:
                print("Error occurred trying to read axis limits on each axis!")
                raise e
        # Return the cached value.
        return self._axis_limits     

    def load_deck(self, deck_filename: str, path :str = os.path.join(os.path.dirname(__file__), 'decks', 'deck_definition')):
        # do thing
        deck_config = json2dict(deck_filename, path)
        deck =  Deck(deck_config)
        self.deck = deck
        return deck                        
    
    def load_tool(self, tool: Tool = None):
        name= tool.name
        idx = tool.index
        if idx in self.tools:
            raise MachineConfigurationError("Error: tool name already used by a different tool")
        else:
            pass

        if name in set(self.tools.values()):
            raise MachineConfigurationError("Error: tool index already set for a different tool")
        else:
            pass
        self.tools[idx] = name

    def load_labware(self, labware_filename : str, slot: int, path : str = None ):

        if path is not None:
            labware = self.deck.load_labware(labware_filename, slot, path = path)
        else:
            labware = self.deck.load_labware(labware_filename, slot)         

        return labware  
        
    # ***************MACROS***************
    def tool_lock(self):
        """Runs Jubilee tool lock macro. Assumes tool_lock.g macro exists."""
        macro_file = "0:/macros/tool_lock.g"
        cmd = f"M98 P{macro_file}"
        self.gcode(cmd)
        
    def tool_unlock(self):
        """Runs Jubilee tool unlock macro. Assumes tool_unlock.g macro exists."""
        macro_file = "0:/macros/tool_unlock.g"
        cmd = f"M98 P{macro_file}"
        self.gcode(cmd)

    def disconnect(self):
        """Close the connection."""
        # Nothing to do?
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.disconnect()
