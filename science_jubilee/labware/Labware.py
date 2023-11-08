import numpy as np
from dataclasses import dataclass
from itertools import chain
from typing import List, Dict, Tuple, Union, Iterable, NamedTuple
import os
import json
from pathlib import Path


@dataclass
class Well:
    name: str  # Name of the well, e.g., 'A1', 'B1', etc.
    depth: float
    totalLiquidVolume: float
    shape: str
    diameter: float = None
    xDimension: float = None
    yDimension: float = None
    x: float
    y: float
    z: float
    offset: Tuple[float] = None

    @property
    def x(self):
        """Offsets the x-position of the each well with respect to the deck-slot coordinates"""
        if self.offset is not None:
            return self._x + self.offset[0]
        else:
            return self._x

    @x.setter
    def x(self, new_x):
        self._x = new_x

    @property
    def y(self):
        """Offsets the y-position of the each well with respect to the deck-slot coordinates"""
        if self.offset is not None:
            return self._y + self.offset[1]
        else:
            return self._y

    @y.setter
    def y(self, new_y):
        self._y = new_y

    @property
    def z(self):
        if self.offset is not None and len(self.offset) ==3 :
            return self._z + self.offset[2]
        else:
            return self._z

    @z.setter
    def z(self, new_z):
        self._z = new_z

    @property
    def top_(self):
        """Defines the top-most point of the well"""
        return self.z + self.depth

    @property
    def bottom_(self):
        """Defines the bottom-most point of the well"""
        return self.z
    
    def bottom(self, z: float = 0.0):
        from_bottom_z = self.bottom_ +z
        coord = (self.x, self.y, from_bottom_z)

        return Location(coord, self)
  
    def top(self, z: float = 0.0 ):
        from_top_z = self.top_ +z
        coord = (self.x, self.y, from_top_z)

        return Location(coord, self)


@dataclass(repr=False)
class WellSet:
    wells: Dict[str, Well]

    def __repr__(self):
        """Displays the wellset as the list of wells and the deck-slot nunmber"""
        return str(f'{list(self.wells.keys())}')

    def __getitem__(self, id_):
        try:
            if isinstance(id_, slice):
                well_list = []
                start = id_.start
                stop = id_.stop
                if id_.step is not None:
                    step = id_.step
                else:
                    step = 1
                for sub_id in range(start, stop, step):
                    well_list.append(self.wells[sub_id])
                return well_list
            else:
                return self.wells[id_]
        except KeyError:
            return list(self.wells.values())[id_]


@dataclass(repr=False)
class Row(WellSet):
    # For example, "A", "B", etc.
    identifier: str  


@dataclass(repr=False)
class Column(WellSet):
    # For example, 1, 2, etc.
    identifier: int  


class Labware(WellSet):
    def __init__(self, labware_filename: str, offset: Tuple[float] = None, order : str = 'rows',
                 path :str = os.path.join(os.path.dirname(__file__), 'labware_definition')):
       
        # load in the labware configuration file
        if labware_filename[-4:] != 'json':
            labware_filename = labware_filename + '.json'

        config_path = os.path.join(
            path, f"{labware_filename}" )

        with open(config_path, "r") as f:
            self.data = json.load(f)

        self.wells_data = self.data.get("wells", {})
        self.data["ordering"] = np.array(self.data["ordering"]).T
        self.row_data, self.column_data, self.wells = self._create_rows_and_columns()
        
        order_options = ['rows', 'row', 'Rows', 'Row', 'R', 'cols', 'col' ,'C', 'columns', 'Columns']
        assert order in order_options, "Order must be one of {}".format(order_options)
        self.withWellOrder(order)
        self.offset = offset
        self.slot= None 

    def __repr__(self):

        display = self.metadata()['displayCategory'] + ': ' + self.parameters()['loadName'] 
        if self.slot is not None:
            display = display + ' ' + f" on {self.slot}"
        return display

    def _create_rows_and_columns(self):
        rows = {}
        columns = {}
        wells = {}

        for row_order, column_data in enumerate(self.data.get('ordering', [])):
            # Assumes the first char is the row identifier, e.g., "A" in "A1"
            row_id = column_data[0][0]  
            # Extracts column number, e.g., "1" in "A1"
            col_ids = [int(well[1:]) for well in column_data]  

            if row_id not in rows:
                rows[row_id] = {}

            for col_order, well_id in enumerate(column_data):
                well = Well(name=well_id, **self.wells_data[well_id])
                rows[row_id][well_id] = well

                if col_order + 1 not in columns:  # +1 since indexing starts at 0
                    columns[col_order + 1] = {}

                columns[col_order + 1][well_id] = well
                wells[well_id] = well

        # Convert dictionary data to Row and Column classes
        rows = {k: Row(identifier=k, wells=v) for k, v in rows.items()}
        columns = {k: Column(identifier=k, wells=v) for k, v in columns.items()}

        return rows, columns, wells

    def get_row(self, row_id: str) -> Row:
        return self.row_data.get(row_id)

    def get_column(self, col_id: int) -> Column:
        return self.column_data.get(col_id)

    @property
    def shape(self):
        return (len(self.row_data), len(self.column_data))

    @property
    def ordering(self) -> List[List[str]]:
        return self.data.get("ordering", [])

    @property
    def brand(self) -> dict:
        return self.data.get("brand", {})

    # @property
    def metadata(self) -> dict:
        return self.data.get("metadata", {})

    @property
    def display_name(self):
        return self.metadata()["displayName"]

    @property
    def labware_type(self):
        return self.metadata()["displayCategory"]

    @property
    def volume_units(self):
        return self.metadata()["displayVolumeUnits"]

    @property
    def dimensions(self) -> dict:
        return self.data.get("dimensions", {})

    @property
    def groups(self) -> List[dict]:
        return self.data.get("groups", [])

    def parameters(self) -> dict:
        return self.data.get("parameters", {})

    @property
    def is_tip_rack(self):
        return self.parameters()["isTiprack"]
    
    @property
    def load_name(self):
        return self.parameters()["loadName"]

    @property
    def tip_length(self):
        try:
            return self.parameters()["tipLength"]
        except:
            pass

    @property
    def tip_overlap(self):
        try:
            return self.parameters()["tipOverlap"]
        except:
            pass

    @property
    def namespace(self) -> str:
        return self.data.get("namespace", "")

    @property
    def version(self) -> int:
        return self.data.get("version", 1)

    @property
    def schemaVersion(self) -> int:
        return self.data.get("schemaVersion", 1)

    @property
    def corner_offset_from_slot(self) -> dict:
        return self.data.get("cornerOffsetFromSlot", {})

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, new_offset):
        self._offset = new_offset
        if new_offset is not None:
            for w in self:
                w.offset = new_offset
    
    def add_slot(self, slot_):
        """Add name of deck slot after labware has been loaded"""
        self.slot = slot_
    
    def withWellOrder(self, order) -> list:
        """Reorders the wells by rows or by columns. Automatically updates"""
        ordered_wells = {}
        if order in ['rows', 'row', 'Rows', 'Row', 'R']:
            for well in list(chain(*self.row_data.values())):
                ordered_wells[well.name] = well
        elif order in ['cols', 'col' ,'C', 'columns', 'Columns']:
            for well in list(chain(*self.column_data.values())):
                ordered_wells[well.name] = well
        else:
            print('Order needs to be either rows or columns')
        
        self.wells = ordered_wells

## Adapted from Opentrons API  opentrons.types##        
class Point(NamedTuple):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def add(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    def substract(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.x - other.x, self.y - other.y, self.z - other.z)

    def multiply(self, other: Union[int, float]):
        if not isinstance(other, (float, int)):
            return NotImplemented
        return Point(self.x * other, self.y * other, self.z * other)

    def absolute(self):
        return Point(abs(self.x), abs(self.y), abs(self.z))

    def __repr__(self) -> str:
        display= "x:{}, y: {}, z:{}".format(self.x, self.y, self.z)
        return display


class Location:
    """A location to target as a motion.

    The location contains a :py:class:`.Point` and possibly an associated
    :py:class:`Labware` or :py:class:`Well` instance.

    """

    def __init__(self, point: Point, labware: Union[Well, Labware]):
        self._point = point
        self._labware = labware
    # todo(mm, 2021-10-01): Figure out how to get .point and .labware to show up
    # in the rendered docs, and then update the class docstring to use cross-references.

    @property
    def point(self) -> Point:
        return self._point

    @property
    def labware(self):
        return self._labware

    def __iter__(self) -> Iterable[Union[Point, Well, Labware]]:
        """Iterable interface to support unpacking. Like a tuple."""
        return iter(( self._point,  self._labware))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Location)
            and other._point == self._point
            and other._labware == self._labware
        )

    def __repr__(self) -> str:
        return f"Location(point={repr(self._point)}, labware={self._labware})"
