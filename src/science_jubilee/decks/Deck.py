import json
import os
from dataclasses import dataclass
from typing import Dict, Tuple

from science_jubilee.labware.Labware import Labware


@dataclass
class Slot:
    """Class that defines a slot on the Jubilee deck.
    Each slot has a unique index, offset, and can have a labware associated with it.

    :param slot_index: The unique index of the slot, usually a number between 0 and 5.
    :type slot_index: int
    :param offset: The (x,y) offset of the slot from the origin of the deck/machine.
    :type offset: Tuple[float]
    :param has_labware: A boolean that indicates whether a labware has been loaded into the slot.
    :type has_labware: bool
    :param labware: The :class:`Labware` object that has been loaded into the slot.
    :type labware: :class:`Labware`
    """

    slot_index: int
    offset: Tuple[float]
    has_labware: bool
    labware: str


@dataclass
class SlotSet:
    """Class that defines a set of slots on the Jubilee deck.

    :param slots: A dictionary of :class:`Slot` objects, where the key is the slot's index.
    :type slots: Dict[str, :class:`Slot`]
    :param bedType: The type of bed that the slots are arranged in. Usually 'fixed' or 'removable'.
    :type bedType: str

    """

    slots: Dict[str, Slot]

    def __repr__(self):
        return str(self.bedType)

    def __getitem__(self, id_):
        """Allows the user to select a :class:`Slot` object by its index or key.

        :param id_: The index or key representing the slot.
        :type id_: str or int
        :return: The :class:`Slot` object associated with the index or key.
        :rtype: :class:`Slot`
        """
        try:
            return self.slots[id_]
        except KeyError:
            return list(self.slots.values())[id_]


class Deck(SlotSet):
    """Class that defines the Jubilee deck.

    The deck is a set of slots that can have labware loaded into them.
    The deck is defined by a configuration file that specifies the number of slots, their offsets, and the type of bed they are arranged in.

    :param deck_filename: The name of the deck configuration file.
    :type deck_filename: str
    :param path: The path to the deck configuration `.json` files for the labware,
            defaults to the 'deck_definition/' in the science_jubilee/decks directory.
    :type path: str, optional
    """

    def __init__(
        self,
        deck_filename,
        path: str = os.path.join(os.path.dirname(__file__), "deck_definition"),
    ):
        """Initializes the :class:`Deck` object by loading its configuration file and creating a dictionary of :class:`Slot` objects.

        :param deck_filename: The name of the deck configuration file.
        :type deck_filename: str
        :param path: The path to the deck configuration `.json` files for the labware,
                defaults to the 'deck_definition/' in the science_jubilee/decks directory.
        :type path: str, optional
        """
        # load in the deck configuration file
        if deck_filename[-4:] != "json":
            deck_filename = deck_filename + ".json"

        config_path = os.path.join(path, f"{deck_filename}")

        with open(config_path, "r") as f:
            deck_config = json.load(f)

        self.deck_config = deck_config
        self.slots_data = self.deck_config.get("slots", {})
        self.slots = self._get_slots()
        self._safe_z = 10

    def _get_slots(self):
        """Function that creates a dictionary of :class:`Slot` objects from the deck configuration file.

        :return: A dictionary of :class:`Slot` objects, where the key is the slot's index.
        :rtype: Dict[str, :class:`Slot`]
        """
        slots = {}
        for s, sv in self.slots_data.items():
            if type(sv) == list:
                sv = tuple(sv)
            else:
                pass
            slots[s] = Slot(slot_index=s, **self.slots_data[s])
        return slots

    @property
    def bedType(self):
        """Function that returns the type of bed loaded onto Jubilee.

        :return: The name/type of deck loaded onto Jubilee, e.g., Lab Automation Deck, Heated Deck, etc.
        :rtype: str
        """

        return self.deck_config.get("bedType", "")

    @property
    def totalslots(self):
        """Function that returns the total number of slots on the deck.

        :return: The total number of slots on the deck.
        :rtype: int
        """

        deckslots = self.deck_config.get("deckSlots", {})
        return deckslots["total"]

    @property
    def slotType(self):
        """Function that returns the type of slot arrangement the deck might have.

        :return: The slot arrangement type. This is inidcated in the configuration file. Standard is "SLAS".
        :rtype: str
        """

        deckslots = self.deck_config.get("deckSlots", {})
        return deckslots["type"]

    @property
    def offsetFrom(self):
        """Function that returns which corner or the slot to apply to a labware loaded on it.

        :return: The corner of the slot to apply to the labware. This is inidcated in the configuration file.
        :rtype: str
        """
        return self.deck_config.get("offsetFrom", {})

    @property
    def deck_material(self):
        """Function that returns the material that the deck and possible mask are made of.

        :return: The material that the deck is made of, as well as any mask that is applied to it.
        :rtype: Dict[str, str]
        """
        return self.deck_config.get("material", {})

    @property
    def safe_z(self):
        """Function that returns the movement clearance height of the deck.

        :return: The height at which the pipette can freely move without colliding with
            labware on the deck.
        :rtype: float
        """
        return self._safe_z

    @safe_z.setter
    def safe_z(self, val):
        """Function that updates the movement clearance height
        every time a new labware is loaded onto the deck

        :param val: The new safe z height.
        :type val: float
        """
        if self._safe_z is None:
            self._safe_z = val
        elif self._safe_z <= val:
            self._safe_z = val
        else:
            pass

    def load_labware(
        self,
        labware_filename: str,
        slot: int,
        path=os.path.join(
            os.path.dirname(__file__), "..", "labware", "labware_definition"
        ),
        order: str = "rows",
    ):
        """Function that loads a labware and associates it with a specific slot on the deck.
         The slot offset is also applied to the labware asocaite with it.

        :param labware_filename: The name of the labware configuration file.
        :type labware_filename: str
        :param slot: The index of the slot to load the labware into.
        :type slot: int
        :param path: The path to the labware configuration `.json` files for the labware,
                defaults to the 'labware_definition/' in the science_jubilee/labware directory.
        :type path: str, optional
        :param order: The order in which the labware is arranged on the deck.
                Can be 'rows' or 'columns', defaults to 'rows'.
        :type order: str, optional
        :return: The :class:`Labware` object that has been loaded into the slot.
        :rtype: :class:`Labware`"""

        labware = Labware(labware_filename, order=order)
        labware.add_slot(slot)
        offset = self.slots[str(slot)].offset

        labware.offset = offset

        self.slots[str(slot)].has_labware = True
        self.slots[str(slot)].labware = labware
        self.safe_z = labware.dimensions["zDimension"]
        return labware
