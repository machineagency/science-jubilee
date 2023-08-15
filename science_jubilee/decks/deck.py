import numpy as np

from dataclasses import dataclass
from typing import Dict, Tuple

from labware.utils import json2dict
from labware.labware import Labware


@dataclass
class Slot:
    slot_index : int
    UL: Tuple[float]
    UR: Tuple[float]
    BL: Tuple[float]
    BR: Tuple[float]
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
        if self._safe_z is None:
            self._safe_z = val
        elif self._safe_z <= val:
            self._safe_z = val
        else:
            pass
        
    def load_labware(self, labware_filename, slot, path = '../labware/LabwareDefinition/'):
        # get slot offset
        lab_file= json2dict(labware_filename, path )
        labware  = Labware(lab_file)
        offset = self.slots[str(slot)].offset 
        
        labware.offset = offset
        self.slots[str(slot)].has_labware = True
        self.slots[str(slot)].labware = labware
        self.safe_z = labware.dimensions['zDimension']
        return labware