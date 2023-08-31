from .Tool import Tool, ToolStateError, ToolConfigurationError
import os
import json


class Pipette(Tool):
    """Control an OpenTrons Pipette"""

    def __init__(self, machine, index, name, config):
        """Set default values and load in pipette configuration."""
        super().__init__(machine, index, name)

        self.brand = None  # Do we need this?
        self.model = None  # Do we need this?
        self.has_tip = False
        self.min_range = 0
        self.max_range = None
        self.zero_position = None
        self.blowout_position = None
        self.eject_tip_position = None
        self.mm_to_ul = None
        # self.available_tips = None

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
        self.brand = config["brand"]
        self.model = config["model"]
        self.min_range = config["min_range"]
        self.max_range = config["max_range"]
        self.zero_position = config["zero_position"]
        self.blowout_position = config["blowout_position"]
        self.eject_tip_position = config["eject_tip_position"]
        self.mm_to_ul = config["mm_to_ul"]

        # Check that all information was provided
        if None in vars(self):
            raise ToolConfigurationError(
                "Error: Not enough information provided in configuration file."
            )

    def check_bounds(self, pos):
        """Disallow commands outside of the pipette's configured range"""
        if pos > self.max_range or pos < self.min_range:
            raise ToolStateError(f"Error: {pos} is out of bounds for the syringe!")

    def pickup_tip(self, tip_rack, position="A1"):
        """Pick up a pipette tip."""
        if self.has_tip:
            raise ToolStateError("Error: Pipette already equipped with a tip.")

        # The first time we pickup a tip, start to keep track of available tips on the rack
        # N.B. We assume the rack is full to start
        if self.available_tips is None:
            self.available_tips = iter(tip_rack["wells"])

        well = next(self.available_tips)
        tip_rack_slot = tip_rack["slot_index"]
        well_pos = self._machine.plate.get_well_position(tip_rack_slot, well)
        self._machine.move_to(x=well_pos[0], y=well_pos[1])

        # ToDo: Implement pickup
        self._machine.move_to(z=46)
        self._machine.move_to(z=125)
        self.aspirate_prime()
        self.has_tip = True

    def eject_tip(self):
        """Eject attached pipette tip."""
        # ToDo: only eject over sharps container/drop bed and move there automatically?
        if not self.has_tip:
            raise ToolStateError("Error: Pipette does not have tip to eject.")

        self._machine.move_to(z=125)
        garbage_pos = self._machine.plate.sharps_container["origin"]
        self._machine.move_to(x=garbage_pos[0], y=garbage_pos[1])
        self._machine.move_to(z=45)
        self._machine.move_to(v=420)  # todo: config file
        self.aspirate_prime()
        self._machine.move_to(z=125)
        self.has_tip = False

    def aspirate(self, vol):
        """Aspirate a certain number of microliters."""
        dv = vol * -1 * self.mm_to_ul
        pos = self._machine.get_position()
        end_pos = float(pos["V"]) + dv
        self.check_bounds(end_pos)
        self._machine.move_to(v=end_pos)

    def dispense(self, vol):
        """Dispense a certain number of microliters."""
        dv = vol * self.mm_to_ul
        pos = self._machine.get_position()
        end_pos = float(pos["V"]) + dv
        self.check_bounds(end_pos)
        self._machine.move_to(v=end_pos)

    def aspirate_prime(self):
        """Move to the bottom of the pipette's aspiration range."""
        self._machine.move_to(v=self.eject_start)

    def transfer(self, volume, source, destination, mix_after=None):
        """Transfer liquid from a source to destination well(s)"""
        m = self._machine
        plate = m.plate
        #         m.move_to(z=125) # move to a safe z

        # ToDo: Calibrate this more generally
        safe_height = 70
        aspirate_height = 47
        dispense_height = 60

        # Our destination might be an individual well, or a dictionary of wells
        if isinstance(destination, dict):
            for well in destination:
                well_position = destination[well]
                # move in (x,y) to the source well
                m.move_to(x=source[0], y=source[1])
                #               Aspirate
                #               ToDo: Calibrate this more generally
                m.move_to(z=aspirate_height)
                self.aspirate(volume)
                m.move_to(z=safe_height)
                m.move_to(x=well_position[0], y=well_position[1])
                m.move_to(z=dispense_height)
                self.dispense(volume)
                self.blowout()
                if mix_after is not None:
                    number_of_mixes = mix_after[0]
                    mix_volume = mix_after[1]
                    m.move_to(z=aspirate_height)
                    self.mix(number_of_mixes, mix_volume)
                    m.move_to(z=dispense_height)
                    self.blowout()
                m.move_to(z=safe_height)
        else:
            # move in (x,y) to the source well
            m.move_to(x=source[0], y=source[1])
            #           Aspirate
            #           ToDo: Calibrate this more generally
            m.move_to(z=aspirate_height)
            self.aspirate(volume)
            m.move_to(z=safe_height)
            m.move_to(x=destination[0], y=destination[1])
            m.move_to(z=dispense_height)
            self.dispense(volume)
            self.blowout()
            if mix_after is not None:
                number_of_mixes = mix_after[0]
                mix_volume = mix_after[1]
                m.move_to(z=aspirate_height)
                self.mix(number_of_mixes, mix_volume)
                m.move_to(z=dispense_height)
                self.blowout()
            m.move_to(z=safe_height)

    def mix(self, number_of_mixes, volume):
        for i in range(number_of_mixes):
            self.aspirate(volume)
            self.dispense(volume)

    def blowout(self, volume=30):
        self.dispense(volume)
        self.aspirate_prime()

    def air_gap(self, volume=20):
        # ToDo: move to height based on labware calibration
        self._machine.move_to(z=60)
        self.aspirate(volume)
