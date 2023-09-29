import os
import json
import numpy as np

from dataclasses import dataclass
from labware.Labware import Labware
from typing import Dict, Tuple

# The Automation Bed Plate and well plates are oriented as follows:                                          

#                          BED PLATE TOP VIEW                          WELL PLATE TOP VIEW                                                                                            
#         Machine Origin                                     Machine Origin               Slot Calibration                                                                     
#             (0,0)                                              (0,0)                        Position                                                        
#                +------------------------------------+               +--------------------+                                                                      
#                |   +------+   +------+   +------+   |               | Well          Well |                                                                            
#                |   |      |   |      |   |      |   |               |  i1            A1  |                                                                                                
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |  0   |   |  2   |   |  4   |   |               |                    |                                                                        
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   +------+   +------+   +------+   | Tool Rack     |                    |                                                                        
#                |   +------+   +------+   +------+   |               |                    |                                                                                            
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |      |   |      |   |      |   |               |                    |                                                                        
#                |   |  1   |   |  3   |   |  5   |   |               |                    |                                                                                            
#   Power Supply |   |      |   |      |   |      |   |               |                    |                                                                                             
#                |   |      |   |      |   |      |   |               | Well          Well |                                                                                            
#                |   +------+   +------+   +------+   |               |  ij            Aj  |                                                                                            
#                +------------------------------------+               +--------------------+



@dataclass
class Slot:
    slot_index : int
    offset: Tuple[float]
    has_labware : bool
    labware : str
    

@dataclass
class SlotSet:
    slots: Dict[str, Slot]
    def __repr__(self):
        return str(self.bedType)
    def __getitem__(self,id_):
        try:
            return self.slots[id_]
        except KeyError:
            return list(self.slots.values())[id_]


class Deck(SlotSet):
    def __init__(self, config):
        self.deck_config = config
        self.slots_data = self.deck_config.get('slots', {})
        self.slots = self._get_slots()
        self._safe_z = None
    
    def _get_slots(self):
        slots = {}
        for s, sv in self.slots_data.items():
            if type(sv) == list:
                sv= tuple(sv)
            else:
                pass
            slots[s] = Slot(slot_index = s, **self.slots_data[s])#{k: tuple(v) for k, v in self.slots_data[s].items()})
        return slots
        
    @property
    def bedType(self):
        return self.deck_config.get('bedType',"")
    @property
    def totalslots(self):
        deckslots= self.deck_config.get('deckSlots', {})
        return deckslots['total'] 

    @property
    def slotType(self):
        deckslots= self.deck_config.get('deckSlots', {})
        return deckslots['type'] 

    @property
    def offsetFrom(self):
        return self.deck_config.get('offsetFrom', {})
    
    @property
    def deck_material(self):
        return self.deck_config.get('material', {})

    @property
    def safe_z(self):
        return self._safe_z
    
    @safe_z.setter
    def safe_z(self, val):
        """Function that updates the movement clearance height 
        every time a new labware is loaded onto the deck """
        if self._safe_z is None:
            self._safe_z = val
        elif self._safe_z <= val:
            self._safe_z = val
        else:
            pass
        
    def load_labware(self, labware_filename, slot, path = os.path.join(os.path.dirname(__file__),'..', 'labware', 'labware_definition')):
        """Function that loads a labware and associates it with a specific slot on the deck.
         The slot offset is also applied to the labware asocaite with it."""

        if labware_filename[-4:] != 'json':
            labware_filename = labware_filename + '.json'

        config_path = os.path.join(path, labware_filename)
        with open(config_path, "r") as f:
            labware_config = json.load(f)

        labware  = Labware(labware_config)
        labware.add_slot(slot)
        offset = self.slots[str(slot)].offset 
        
        labware.offset = offset      

        self.slots[str(slot)].has_labware = True
        self.slots[str(slot)].labware = labware
        self.safe_z = labware.dimensions['zDimension']
        return labware