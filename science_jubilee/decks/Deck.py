from dataclasses import dataclass
from typing import Dict, Tuple
from pathlib import Path
import os
import json
import copy
from science_jubilee.labware.Utils import json2dict
from science_jubilee.labware.Labware import Labware


@dataclass
class Slot:
    slot_index: int
    offset: Tuple[float]
    has_labware: bool
    labware: str


@dataclass
class SlotSet:
    slots: Dict[str, Slot]

    def __repr__(self):
        return str(self.bed_type)

    def __getitem__(self, id_):
        try:
            if isinstance(id_, slice):
                slot_list = []
                start = id_.start
                stop = id_.stop
                if id_.step is not None:
                    step = id_.step
                else:
                    step = 1
                for sub_id in range(start, stop, step):
                    slot_list.append(self.slots[sub_id])
                return slot_list
            else:
                return self.slots[id_]
        except KeyError:
            return list(self.slots.values())[id_]


class Deck(SlotSet):
    def __init__(self, config):
        self.deck_config = config
        self.slots_data = self.deck_config.get("slots", {})
        self.slots = self._get_slots()
        self._safe_z = 5

    def _get_slots(self):
        slots = {}
        for s, sv in self.slots_data.items():
            if type(sv) == list:  # When would this happen?
                print("list")
                sv = tuple(sv)
            slots[s] = Slot(slot_index=s, **self.slots_data[s])
        return slots

    @property
    def bed_type(self):
        return self.deck_config.get("bed_type", "")

    @property
    def total_slots(self):
        deckslots = self.deck_config.get("deck_slots", {})
        return deckslots["total"]

    @property
    def slot_type(self):
        deckslots = self.deck_config.get("deckSlots", {})
        return deckslots["type"]

    @property
    def offset_from(self):
        return self.deck_config.get("offset_from", {})

    @property
    def deck_material(self):
        return self.deck_config.get("material", {})

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

    def load_labware(self, labware_filename, slot):
        # root_dir = Path(__file__).parent.parent
        # config_path = os.path.join(
        #     root_dir, "labware", "labware_definitions", f"{labware_filename}.json"
        # )
        # with open(config_path, "r") as f:
        #     labware_config = json.load(f)
        labware = Labware(labware_filename)
        
        # Flip offsets to align with machine coordinates, if necessary
        # TODO: Test this from all orientations
        offset = copy.copy(self.slots[str(slot)].offset)
        offset_from = self.offset_from['corner']
        OFFSET_OPTIONS = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        if offset_from not in OFFSET_OPTIONS:
            print("Error: unknown offset option.") # TODO: Make a DeckStateError in base deck class
        
        labware_dims = labware.dimensions
        if 'right' in offset_from:
            offset[0] -= labware_dims['xDimension']
        if 'top' in offset_from:
            offset[1] -= labware_dims['yDimension']

        labware.offset = offset
        self.slots[str(slot)].has_labware = True
        self.slots[str(slot)].labware = labware
        self.safe_z = labware.dimensions["zDimension"]
        return labware
