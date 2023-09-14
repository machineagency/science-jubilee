from .Tool import Tool, ToolStateError
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
        tool_info = json.loads(self._machine.send('M409 K"tools[]"'))["result"]
        for tool in tool_info:
            if tool["number"] == self.index:
                self.e_drive = f"E{tool['extruders'][0]}" # Syringe tool has only 1 extruder
            else:
                continue
            
    def check_bounds(self, pos):
        """Disallow commands outside of the syringe's configured range"""
        if pos > self.max_range or pos < self.min_range:
            raise ToolStateError(f"Error: {pos} is out of bounds for the syringe!")
            
    def aspirate(self, vol):
        """Aspirate a certain number of milliliters."""
        de = vol * -1 * self.mm_to_ml
        pos = self._machine.get_position()
        end_pos = float(pos[self.e_drive]) + de
        self.check_bounds(end_pos)
        current_pos = pos[self.e_drive]
        self._machine.move(de=de)

    def dispense(self, vol):
        """Dispense a certain number of milliliters."""
        de = vol * self.mm_to_ml
        pos = self._machine.get_position()
        end_pos = float(pos[self.e_drive]) + de
        self.check_bounds(end_pos)
        self._machine.move(de=de)
