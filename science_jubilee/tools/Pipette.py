from .Tool import Tool, ToolStateError, ToolConfigurationError
import os
import json

class Pipette(Tool):
    """Control an OpenTrons Pipette"""
    def __init__(self, machine, index, name, details):
        """Set default values and load in pipette configuration."""
        super().__init__(machine, index, name, details)
        
        self.has_tip = False
        self.min_range = 0
        self.max_range = None
        self.eject_start = None
        self.mm_to_ul = None
        self.available_tips = None
        
        self.load_config(details)
        
    def load_config(self, details):
        """Load the relevant configuration file for this pipette."""
        if not details:
            raise ToolConfigurationError("Error: Specify the pipette model in your tool_types.json file")
        else:
            config_path = os.path.join(self.get_root_dir(), f'config/tools/{self._details}.json')
            if not os.path.isfile(config_path):
                raise ToolConfigurationError(f"Error: Config file {self._details}.json does not exist!")
                
            with open(config_path, 'r') as f:
                config = json.load(f)
            try:
                self.max_range = config['max_range']
                self.eject_start = config['eject_start']
                self.mm_to_ul = config['mm_to_ul'] 
            except:
                raise ToolConfigurationError("Error: Problem with provided configuration file.")
        
        # Check that all information was provided
        if None in [self.max_range, self.eject_start, self.mm_to_ul]:
            raise ToolConfigurationError("Error: Not enough information provided in configuration file.")
                
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
        tip_rack_slot = tip_rack['slot_index']
        well_pos = self._machine.plate.get_well_position(tip_rack_slot, well)
        self._machine.move_to(x=well_pos[0], y=well_pos[1])
        
        #ToDo: Implement pickup
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
        garbage_pos = self._machine.plate.sharps_container['origin']
        self._machine.move_to(x=garbage_pos[0], y=garbage_pos[1])
        self._machine.move_to(z=45)
        self._machine.move_to(v=420) # todo: config file
        self.aspirate_prime()
        self._machine.move_to(z=125)
        self.has_tip = False
    
    def aspirate(self, vol): 
        """Aspirate a certain number of microliters."""
        dv = vol* -1 * self.mm_to_ul
        pos = self._machine.get_position()
        end_pos = float(pos['V']) + dv
        self.check_bounds(end_pos)
        self._machine.move_to(v=end_pos)
        
    def dispense(self, vol): 
        """Dispense a certain number of microliters."""
        dv = vol * self.mm_to_ul
        pos = self._machine.get_position()
        end_pos = float(pos['V']) + dv
        self.check_bounds(end_pos)
        self._machine.move_to(v=end_pos)      

    def aspirate_prime(self):
        """Move to the bottom of the pipette's aspiration range."""
        self._machine.move_to(v=self.eject_start)
        
    def transfer(self, volume, source, destination, mix_after = None):
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
            
    def blowout(self, volume = 30):
        self.dispense(volume)
        self.aspirate_prime()
        
    def air_gap(self, volume = 20):
        # ToDo: move to height based on labware calibration
        self._machine.move_to(z=60)
        self.aspirate(volume)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
      