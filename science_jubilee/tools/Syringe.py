from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from science_jubilee.labware.Labware import Labware, Well
from typing import Tuple, Union
import warnings
import numpy as np
import os
import json


class Syringe(Tool):
    def __init__(self, index, name, config):
        """Set default values and load in configuration"""
        super().__init__(index, name)
        
        self.min_range = 0
        self.max_range = None
        self.mm_to_ml = None
        self.e_drive = "E"

        self.load_config(config)

    def load_config(self, config):
        """Load the relevant configuration file for this pipette."""
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
        """Find extruder drive for this tool."""
        # To read the position of an extruder, we need to know which extruder # to look at
        # Query the object model to find this
        tool_info = json.loads(self._machine.gcode('M409 K"tools[]"'))["result"]
        for tool in tool_info:
            if tool["number"] == self.index:
                self.e_drive = f"E{tool['extruders'][0]}" # Syringe tool has only 1 extruder
            else:
                continue
            
    def check_bounds(self, pos):
        """Disallow commands outside of the syringe's configured range"""
        if pos > self.max_range or pos < self.min_range:
            raise ToolStateError(f"Error: {pos} is out of bounds for the syringe!")

    @requires_active_tool        
    def _aspirate(self, vol: float, s: int = 2000):
        """Aspirate a certain number of milliliters."""
        de = vol * -1 * self.mm_to_ml
        pos = self._machine.get_position()
        end_pos = float(pos[self.e_drive]) + de
        self.check_bounds(end_pos)
        self._machine.move(de=de, wait = True)

    @requires_active_tool    
    def _dispense(self, vol, s: int = 2000):
        """Dispense a certain number of milliliters."""
        de = vol * self.mm_to_ml
        pos = self._machine.get_position()
        end_pos = float(pos[self.e_drive]) + de
        self.check_bounds(end_pos)
        self._machine.move(de=de, wait = True)
    
    @requires_active_tool   
    def aspirate(
        self,
        vol: float,
        s: int = 2000,
        well: Well = None,
        from_bottom: float = 5,
        from_top: float = None,
        location: Tuple[float] = None,
    ):
        """Aspirate a given volume of liquid from a given well."""
        x, y, z = self._get_xyz(well=well, location=location)
        if well is not None:
            top, bottom = self._get_top_bottom(well=well)
            self.current_well = well

        if from_bottom is not None and well is not None:
            z = bottom + from_bottom
        elif from_top is not None and well is not None:
            z = top + from_top # TODO: this should be minus, if I'm understanding right?
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._aspirate(vol, s=s)

    @requires_active_tool    
    def dispense(
        self,
        vol: float,
        s: int = 2000,
        well: Well = None,
        from_bottom: float = None,
        from_top: float = 2,
        location: Tuple[float] = None,
    ):
        """Dispense a given volum of liquid from a given well."""
        x, y, z = self._get_xyz(well=well, location=location)

        if well is not None:
            top, bottom = self._get_top_bottom(well=well)
            self.current_well = well

        if from_bottom is not None and well is not None:
            z = bottom + from_bottom
        elif from_top is not None and well is not None:
            z = top + from_top # TODO: This should be minus, if I understand right?
            pass
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
        if type(source) != list:
            source = [source]
        if type(destination) != list:
            destination = [destination]
        
        # Assemble tuples of (source, destination)
        num_source_wells = len(source)
        num_destination_wells = len(destination)
        if num_source_wells == num_destination_wells: # n to n transfers
            pass
        elif num_source_wells == 1 and num_destination_wells > 1: # one to many transfers
            source = list(np.repeat(source, num_destination_wells))
        elif num_source_wells > 1 and num_destination_wells == 1: # many to one transfers
            destination = list(np.repeat(destination, num_source_wells))
        elif num_source_wells > 1 and num_destination_wells > 1: # uneven transfers
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
            xs, ys, zs = self._get_xyz(well=source_well)
            xd, yd, zd = self._get_xyz(well=destination_well)

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

        
    @staticmethod
    def _get_xyz(well: Well = None, location: Tuple[float] = None):
        if well is not None and location is not None:
            raise ValueError("Specify only one of Well or x,y,z location")
        elif well is not None:
            x, y, z = well.x, well.y, well.z
        else:
            x, y, z = location
        return x, y, z
        
    @staticmethod
    def _get_top_bottom(well: Well = None):
        top = well.top
        bottom = well.bottom
        return top, bottom
        
