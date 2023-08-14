from .Plate import Plate, PlateStateError, PlateConfigurationError

import os
import json
import math

# The Automation Bed Plate and well plates are oriented as follows:                                          

#                          BED PLATE TOP VIEW                          WELL PLATE TOP VIEW                                                                                            
#         Machine Origin                                     Machine Origin               Slot Calibration                                                                     
#             (0,0)                                              (0,0)                        Position                                                        
#                +------------------------------------+               +--------------------+                                                                      
#                |   +------+   +------+   +------+   |               | Well          Well |                                                                            
#                |   |      |   |      |   |      |   |               |  i1            A1  |                                                                                                
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |  0   |   |  1   |   |  2   |   |               |                    |                                                                        
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   +------+   +------+   +------+   | Tool Rack     |                    |                                                                        
#                |   +------+   +------+   +------+   |               |                    |                                                                                            
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |  5   |   |  4   |   |  3   |   |               |                    |                                                                                            
#   Power Supply |   |      |   |      |   |      |   |               |                    |                                                                                             
#                |   |      |   |      |   |      |   |               | Well          Well |                                                                                            
#                |   +------+   +------+   +------+   |               |  ij            Aj  |                                                                                            
#                +------------------------------------+               +--------------------+

class LabAutomationPlate(Plate):
    """Setup a lab automation plate with relevant labware."""
    def __init__(self, machine, name, config):
        """Set default values and load in plate configuration."""
        super().__init__(machine, name)
        
        # Load the config file
        config_path = os.path.join(self.get_root_dir(), f"config/machine/{config}.json")
        if not os.path.isfile(config_path):
            raise PlateConfigurationError(f"Error: config file at {config_path} does not exist")
        with open(config_path, 'r') as f:
            config_contents = json.load(f)
            
        self.sharps_container = None
        self.num_slots = len(config_contents)
        self.slots = {}
        for slot_index, origin in config_contents.items():
            slot_index = int(slot_index)
            self.slots[slot_index] = {}
            self.slots[slot_index]['origin'] = [float(i) for i in origin]
            self.slots[slot_index]['labware'] = None
        
        # The sharps container is calibrated as slot index -1
        if self.slots[-1]:
            self.sharps_container = self.slots[-1]
            
    def load_labware(self, slot_index, labware_name):
        """Load labware into a slot index."""
        # Load the labware configuration
        labware_config_path = os.path.join(self.get_root_dir(), f"config/labware/{labware_name}.json")
        
        if not os.path.isfile(labware_config_path):
            raise PlateConfigurationError(f"Error: Labware config file {labware_config_path} does not exist")
        with open(labware_config_path, 'r') as f:
            config_contents = json.load(f)
        
        slot = self.slots[slot_index]
        slot['labware'] = labware_name
        slot['slot_index'] = slot_index
        for key, value in config_contents.items():
            slot[key] = value
        
        # Calculate and store information for finding wells.
        column_count = slot['column_count']
        row_count = slot['row_count']
        max_row_letter = chr(ord('@')+row_count) # Labware rows are identified with letters
        
        # Find the machine coordinates by adding labware calibration points to the slot reference position. 
        # The slot reference position is calibrated to be the corner closest to well A1. 
        a = [sum(x) for x in zip(slot['calibration_positions']["A1"], slot['origin'])]
        slot['calibration_positions']["A1"] = a
        b = [sum(x) for x in zip(slot['calibration_positions'][f"A{column_count}"], slot['origin'])]
        slot['calibration_positions'][f"A{column_count}"] = b
        c = [sum(x) for x in zip(slot['calibration_positions'][f"{max_row_letter}{column_count}"], slot['origin'])]
        slot['calibration_positions'][f"{max_row_letter}{column_count}"] = c

        # Compute width, height, and well spacing from the configuration file.
        labware_width = math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)
        labware_height = math.sqrt((c[0] - b[0])**2 + (c[1] - b[1])**2)
        slot['labware_width'] = labware_width
        slot['labware_height'] = labware_height
        slot['x_spacing'] = slot['labware_width'] / (column_count - 1)
        slot['y_spacing'] = slot['labware_height'] / (row_count - 1)
        
        # Machine and camera axes might be slightly skewed; average the redundant angle measurement.
        theta1 = math.asin((b[1] - a[1]) / labware_width)
        theta2 = math.asin((c[0] - b[0]) / labware_height)
        theta = (theta1 + theta2)/2
        slot['theta'] = theta
        
        # ToDo: do these well operations in a separate function
        # Add position of all wells in labware
        wells = {}
        for i in range(1, column_count + 1):
            for j in range(1, row_count + 1):
                row_letter = self.row_index_to_letter(j)
                well_id = f"{row_letter}{i}"
                well_position = self.get_well_position(slot_index, well_id)
                wells[well_id] = well_position
        slot['wells'] = wells
        
        # Add rows
        rows = {}
        for i in range(1, row_count+1):
            row_letter = self.row_index_to_letter(i)
            rows[row_letter] = {}
            for j in range(1, column_count + 1):
                well_id = f"{row_letter}{j}"
                well_position = self.get_well_position(slot_index, well_id)
                rows[row_letter][well_id] = well_position
        slot['rows'] = rows
        
        # Add columns
        columns = {}
        for j in range(1, column_count+1):
            columns[j] = {}
            for i in range(1, row_count + 1):
                row_letter = self.row_index_to_letter(i)
                well_id = f"{row_letter}{j}"
                well_position = self.get_well_position(slot_index, well_id)
                columns[j][well_id] = well_position
        slot['columns'] = columns
        
        
        input(f"Load {labware_name} into slot {slot_index}. Press enter to continue.")
        
        return slot
            
    def get_well_position(self, slot_index, well_id):
        """Return machine coordinates for a well id in a bed plate slot."""
        if self.slots[slot_index]['labware'] is None:
            raise PlateStateError(f"Error: No labware loaded into slot {slot_index}")
            
        row_letter = well_id[0]
        row = int(ord(row_letter.lower()) - 96)
        column = int(well_id[1:])
        slot = self.slots[slot_index]
        
        if row <= 0 or column <= 0 or row > slot['row_count'] or column > slot["column_count"]:
            raise PlateStateError(f"Error: Well ID ({row},{column}) is out of range for this labware.")
        
        # Translate and rotate from A1 to the desired well.
        row_index = row - 1
        column_index = column - 1
        a1 = slot['calibration_positions']["A1"]
        theta = slot['theta']
        x = column_index * slot['x_spacing']
        y = row_index * slot['y_spacing']
        
        # ToDo: Check this on the machine
        # 2D rotation:
        x_rotated = a1[0] + x * math.cos(theta) - y * math.sin(theta)
        y_rotated = a1[1] - (x * math.sin(theta) + y * math.cos(theta))
        
        x_nominal = a1[0] + x
        y_nominal = a1[1] - y
        
        
        # ToDo: return just the rotated values, assuming the work
        return [x_nominal, y_nominal]
#         return [x_nominal, y_nominal, x_rotated, y_rotated]
            
    def wells(self, slot_index):
        """Return a list of all the wells for this labware."""
        
       
        slot = self.slots[slot_index]
        if not slot['labware']:
            raise PlateStateError(f"Error: No labware loaded into slot {slot_index}")
        
        # Return first down a row (A1, B1, ...) then column
        wells = []
        for i in range(1, slot['column_count'] + 1):
            for j in range(1, slot['row_count'] + 1):
                row_letter = self.row_index_to_letter(j)
                well_position = self.get_well_position(slot_index, f"{row_letter}{j}")
                wells.append(well_position)
        
        return wells
        
    def row_index_to_letter(self, row_index):
        """Convert a row number (starting at 1) to a letter"""
        return chr(ord('@')+row_index) 
    
    
    def row_letter_to_index(self, row_letter):
        """Convert a row letter (A, B, C...) to a 0-indexed number"""
        return ord(row_letter.upper()) - 65
       
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

    