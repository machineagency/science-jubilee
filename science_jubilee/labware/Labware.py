import os
import json

import numpy as np

from dataclasses import dataclass
from itertools import chain
from typing import List, Dict, Tuple, Union, Iterable, NamedTuple


@dataclass
class Well:
    """A class representing a well of a labware.

    Each Well is associated with a specific name, depth, total liquid volume, shape, diameter,
    x, y, and z dimension, y-dimension, as well as its coordinates and any applied offset

    :return: A :class:`Well` object with various information about the geometry of the well and its position in the labware
    :rtype: :class:`Well`
    """
    name: str 
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
        """Offsets the x-position of the each well with respect to the deck-slot coordinates
        
        :return: The x-coordinate of the well
        :rtype: float
        """
        if self.offset is not None:
            return self._x + self.offset[0]
        else:
            return self._x

    @x.setter
    def x(self, new_x):
        """Setter for the offsetted x-position of each well with respect to the deck-slot coordinates

        :param new_x: the new y-coordinate of the well
        :type new_x: float
        """        
        self._x = new_x

    @property
    def y(self):
        """Offsets the y-position of the each well with respect to the deck-slot coordinates
        
        :return: The y-coordinate of the well
        :rtype: float
        """
        if self.offset is not None:
            return self._y + self.offset[1]
        else:
            return self._y

    @y.setter
    def y(self, new_y):
        """Setter for the offsetted y-position of each well with respect to the deck-slot coordinates

        :param new_y: The new y-coordinate of the well
        :type new_y: float
        """        

        self._y = new_y

    @property
    def z(self):
        """Offsets the z-position of each well with respect to the deck-slot coordinates

        :return: The z-coordinate of the well
        :rtype: float
        """
        if self.offset is not None and len(self.offset) ==3 :
            return self._z + self.offset[2]
        else:
            return self._z

    @z.setter
    def z(self, new_z):
        """Setter for the offsetted z-position of each well with respect to the deck-slot coordinates

        :param new_z: The new z-coordinate of the well
        :type new_z: flaot
        """
        self._z = new_z

    @property
    def top_(self):
        """Defines the top-most point of the well
        
        :return: The z-coordinate of the top of the well
        :rtype: float
        """
        return self.z + self.depth

    @property
    def bottom_(self):
        """Defines the bottom-most point of the well
        
        :return: The z-coordinate of the bottom of the well
        :rtype: float
        """
        return self.z
    
    def bottom(self, z: float, check = False):        
        """Allows the user to dinamically indicate a new Z location relative to the 
        bottom of the well. 

        :param z: the distance in mm to offset the coordinates from the bottom of the well. Should be + 
        :type z: float
        :param check: the 'z' parameters can either be + or -. If negative, an assert error is raised to
            avoid collision with the labware. However, there might be instances of custom labware where the bottom of the well
            is purposely set as higher during the generation of its config .json file., defaults to False
        :type check: bool, optional
        :return: A :class:`Location` which contains information about the new coordinates generated and the 
            :class:`Well` object
        :rtype: :class:`Location`
        """
        from_bottom_z = self.bottom_ +z
        if check:
            pass
        else:
            assert z >=0, "Indicated location is lower than the bottom of the labware and"\
        " could result in crash. Input a positive 'z' value "
         
        coord = (self.x, self.y, from_bottom_z)

        return Location(coord, self)
  
    def top(self, z: float ):
        """Allows the user to dinamically indicate a new Z location relative to the 
        top of the well.

        :param z: the distance in mm to offset the coordinates from the top of the well.Can be either + or -
        :type z: float
        :return: A :class:`Location` which contains information about the new coordinates generated and the 
            :class:`Well` object.
        :rtype: :class:`Location`
        """
        from_top_z = self.top_ + z
        assert from_top_z > self.bottom_, "Indicated location is lower than the bottom of the labware."
        coord = (self.x, self.y, from_top_z)

        return Location(coord, self)


@dataclass(repr=False)
class WellSet:
    """A class defining a set of wells expressed as a dictionary in which each keys is the
        the :attribute:`Well.name` object and the value is the :class:`Well` object itself. 
    """
    wells: Dict[str, Well]
    
    def __repr__(self):  
        """Displays the wellset as a :list: of wells and the deck-slot nunmber

        :return: A :list: of :class:`Well` objects diplayed by their :attribute:`Well.name` 
        :rtype: :class:`Row`
        """ 
        return str(f'{list(self.wells.keys())}')

    def __getitem__(self, id_:Union[str, int]):
        """Allows the user to select a :class:`Well` object by either their :attribute:`Well.name` or 
            their index in a :list:

        :param id_: The :attribute:`Well.name` or index representing a :class:`Well` in the labware
        :type id_: Union[str, int]
        :return: The :class:`Well` object 
        :rtype: :class:`Well`
        """
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
    """A class representing a row of a labware, for example 'A', 'B', etc

    :param WellSet: A dictionary of :class:`Well` objects in which each keys is the the :attribute:`Well.name` object and the value is the :class:`Well` object itself.
    :type WellSet: Dict[str, Well]
    """
    identifier: str  


@dataclass(repr=False)
class Column(WellSet):
    """A class representing a column of a labware, for example 1, 2, etc.

    :param WellSet: A dictionary of :class:`Well` objects in which each keys is the the :attribute:`Well.name` object and the value is the :class:`Well` object itself.
    :type WellSet: Dict[str, Well]
    """
    identifier: int  


class Labware(WellSet):
    """A class representing a basic laboratory labware made up of a set of wells/pipette tips. 

    :param labware_filename: The name of the config `.json` 
    :type labware_filename: str
    :param offset: Coordinates to use to offset all the wells in a labware for easier handling of coordinates. 
        For example this is called by the :method:`Deck.load_labware` when assignign a labware to a deck slot, defaults to None
    :type offset: Tuple[float], optional
    :param order: Option to order the wells of a labware either by `row` or `columns`, defaults to 'rows'
    :type order: str, optional
    :param path: Path to the folder containing the configuration `.json` files for the labware,
            defaults to the 'labware_definition/' in the science_jubilee/labware directory.
    :type path: str, optional
    """

    def __init__(self, labware_filename: str, offset: Tuple[float] = None, order : str = 'rows',
                 path :str = os.path.join(os.path.dirname(__file__), 'labware_definition')):
        """ Initializes a :class:`Labware` object by loading its configuration file and creating a dictionary of :class:`Well` objects.
         
        :param labware_filename: The name of the config `.json` 
        :type labware_filename: str
        :param offset: Coordinates to use to offset all the wells in a labware for easier handling of coordinates. 
            For example this is called by the :method:`Deck.load_labware` when assignign a labware to a deck slot, defaults to None
        :type offset: Tuple[float], optional
        :param order: Option to order the wells of a labware either by `row` or `columns`, defaults to 'rows'
        :type order: str, optional
        :param path: Path to the folder containing the configuration `.json` files for the labware,
                defaults to the 'labware_definition/' in the science_jubilee/labware directory.
        :type path: str, optional
        """
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
        """Displayed representation of a :class:`Labware` object indicating the type of labware and
            its name. Additionally, it will show the :attribute:`Deck.slots` number if the labware has been
            already assigned to it. 
        """
        display = self.metadata()['displayCategory'] + ': ' + self.parameters()['loadName'] 
        if self.slot is not None:
            display = display + ' ' + f" on {self.slot}"
        return display

    def _create_rows_and_columns(self):
        """Creates a dictionary of :class:`Row` and :class:`Column` and :class:`Well` objects from the data in the config `.json` file.

        :return: A dictionary of :class:`Row` and :class:`Column` and :class:`Well` objects
        :rtype: :class:`Row`, :class:`Column`, :class:`Well`
        """
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
        """Fucntions to fetch the :class:`Well.name` of the indicated row.

        :param row_id: The name of a row of the labware, usually indicated by a capital letter (e.g., A, B, etc.)
        :type row_id: str
        :return: A list of :class:`Well` objects diplayed by their :attribute:`Well.name` 
        :rtype: :class:`Row`
        """
        return self.row_data.get(row_id)

    def get_column(self, col_id: int) -> Column:
        """Fucntions to fetch the :class:`Well.name` of the indicated column.

        :param col_id: The name of a column of the labware, usually indicated by an integer number (e.g., 1, 2, etc.)
        :type col_id: str
        :return: A list of :class:`Well` objects diplayed by their :attribute:`Well.name` 
        :rtype: :class:`Column`
        """
        return self.column_data.get(col_id)

    @property
    def shape(self):
        """Returns the shape of the labware as a tuple of (rows, columns)

        :return: A tuple of (rows, columns)
        :rtype: Tuple[int, int]
        """
        return (len(self.row_data), len(self.column_data))

    @property
    def ordering(self) -> List[List[str]]:
        """Returns the ordering of the wells in the labware as a list of lists. Each list represents a row of the labware.

        :return: A list of lists of :class:`Well.name` objects
        :rtype: List[List[str]]
        """
        return self.data.get("ordering", [])

    @property
    def brand(self) -> dict:
        """Returns the brand of the labware as a strin

        :return: A string with the brand of the labware
        :rtype: str
        """
        return self.data.get("brand", {})['brand']

    def metadata(self) -> dict:
        """Returns the metadata of the labware as a dictionary

        The metadata of a labware will generally contain the display name, the type of labware, and the units of volume.
        These can also be found as attributes of the :class:`Labware` object.

        :return: A dictionary with the metadata of the labware
        :rtype: dict
        """
        return self.data.get("metadata", {})

    @property
    def display_name(self):
        """Returns the display name of the labware as a string

        :return: A string with the display name of the labware
        :rtype: str
        """
        return self.metadata()["displayName"]

    @property
    def labware_type(self):
        """Returns the type of labware as a string

        The type fo labware will generally either be a tiprack, wellplate, reservoir, etc.

        :return: A string with the type of labware
        :rtype: str
        """
        return self.metadata()["displayCategory"]

    @property
    def volume_units(self):
        """Returns the units of volume of the labware as a string

        The volume units will be either uL or mL.

        :return: A string with the units of volume of the labware
        :rtype: str
        """
        return self.metadata()["displayVolumeUnits"]

    @property
    def dimensions(self) -> dict:
        """Returns the dimensions of the labware as a dictionary

        :return: A dictionary with the x,y, and z dimensions of the labware
        :rtype: dict
        """
        return self.data.get("dimensions", {})

    def parameters(self) -> dict:
        """Returns the parameters describing certain features of the labware as a dictionary

        The parameters genereally include whether the shape of the labware is regular or irregular, if it is a tiprack,
        and other Opentrons specific parameters as we are using their 'Custom Labware Page' to generate the .json config files. 
        
        :return: A dictionary with the parameters of the labware
        :rtype: dict
        """
        return self.data.get("parameters", {})

    @property
    def is_tip_rack(self):
        """Returns a boolean indicating if the labware is a tiprack

        :return: True if the labware is a tiprack, False otherwise
        :rtype: bool
        """
        return self.parameters()["isTiprack"]
    
    @property
    def load_name(self):
        """Returns the name of the labware as a string

        :return: A string with the name of the labware
        :rtype: str
        """
        return self.parameters()["loadName"]

    @property
    def tip_length(self):
        """Returns the length of the tip of the labware as a float if the labware is a tiprack, otherwise returns None
        
        :return: A float with the length of the tip of the labware or None otherwise
        :rtype: float
        """
        try:
            return self.parameters()["tipLength"]
        except:
            pass

    @property
    def tip_overlap(self):
        """Returns the overlap of the tip of the labware as a float if the labware is a tiprack, otherwise returns None

        :return: A float with the overlap of the tip of the labware or None otherwise 
        :rtype: float
        """
        try:
            return self.parameters()["tipOverlap"]
        except:
            pass

    @property
    def offset(self):
        """Returns the offset of the labware as a tuple of floats

        :return: A tuple of floats with the offset of the labware
        :rtype: Tuple[float]
        """
        return self._offset

    @offset.setter
    def offset(self, new_offset):
        """Sets the offset of the labware to the indicated values and updates the offset of each well in the labware

        :param new_offset: A tuple of floats with the new offset of the labware
        :type new_offset: Tuple[float]
        """
        self._offset = new_offset
        if new_offset is not None:
            for w in self:
                w.offset = new_offset
    
    def add_slot(self, slot_):
        """Add name of deck slot after labware has been loaded
        
        :param slot_: The name of the deck slot
        :type slot_: str
        """
        self.slot = slot_
    
    def withWellOrder(self, order) -> list:
        """Reorders the wells by rows or by columns. Automatically updates the :attribute:`Labware.wells`
        
        :param order: The order in which to reorder the wells. Can be either 'rows' or 'columns'
        :type order: str
        :return: A list of :class:`Well` objects diplayed by their :attribute:`Well.name`
        :rtype: list
        """
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

    @staticmethod
    def _getxyz(location: Union[Well, Tuple, 'Location']):
        """Helper function to extract the x, y, z coordinates of a location object.

        :param location: The location object to extract the coordinates from. This can either be a 
            :class:`Well`, a :tuple: of x, y, z coordinates, or a :class:`Location` object
        :type location: Union[Well, Tuple, Location]
        :raises ValueError: If the location is not a :class:`Well`, a :class:`tuple`, or a :class:`Location` object
        :return: The x, y, z coordinates of the location
        :rtype: float, float, float
        """
        if type(location) == Well:
            x, y, z = location.x, location.y, location.z
        elif type(location) == Tuple:
            x, y, z = location
        elif type(location)==Location:
            x,y,z= location._point
        else:
            raise ValueError("Location should be of type Well or Tuple")
        
        return x,y,z

## Adapted from Opentrons API  opentrons.types##        
class Point(NamedTuple):
    """A point in the Jubilee 3D coordinate system.

    :param NamedTuple: A list-like container with a fixed number of elements
    :type NamedTuple: :class:`NamedTuple`
    :return: A tuple of coordinates (x,y,z)
    :rtype: :class:`Point`
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def add(self, other):
        """Adds the coordinates of two points

        :param other: A tuple of coordinates (x,y,z)
        :type other: :class:`Point`
        :return: A new :class:`Point` object 
        :rtype: :class:`Point`
        """
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    def substract(self, other):
        """Substracts the coordinates of two points
        
        :param other: A tuple of coordinates (x,y,z)
        :type other: :class:`Point`
        :return: A new :class:`Point` object 
        :rtype: :class:`Point`
        """
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.x - other.x, self.y - other.y, self.z - other.z)

    def multiply(self, other: Union[int, float]):
        """Multiplies the coordinates of a point by a scalar

        :param other: A scalar to multiply the coordinates of a point
        :type other: Union[int, float]
        :return: A new :class:`Point` object scaled by the value indicated as the function parameter
        :rtype: :class:`Point`
        """        

        if not isinstance(other, (float, int)):
            return NotImplemented
        return Point(self.x * other, self.y * other, self.z * other)

    def absolute(self):
        """Returns the absolute value of the coordinates of a point.

        :return: The absolute values of a :class:`Point` object
        :rtype: :class:`Point` 
        """        
        return Point(abs(self.x), abs(self.y), abs(self.z))

    def __repr__(self) -> str:
        """Returns a string representation of the coordinates of a point.

        :return: A string representation of the coordinates of a point
        :rtype: str
        """

        display= "x:{}, y: {}, z:{}".format(self.x, self.y, self.z)
        return display


class Location:
    """A location to target as a motion.

    The location contains a :class:`Point` and possibly an associated
    :class:`Labware` or :class:`Well` instance.
    """

    def __init__(self, point: Point, labware: Union[Well, Labware]):

        self._point = point
        self._labware = labware
    
    @property
    def point(self) -> Point:
        """The coordinates (x,y,z) of a Well or a Labware

        :return: A tuple of coordinates (x,y,z)
        :rtype: :class:`Point`
        """
        return self._point

    @property
    def labware(self):
        """The :class:`Well` object associated with the coordinates (x,y,z)

        :return: A :class:`Well` object
        :rtype: :class:`Well`        
        """
        return self._labware

    def __iter__(self) -> Iterable[Union[Point, Well, Labware]]:
        """Iterable interface to support unpacking of :class:`Location` objects.
        
        :return: An interable of :class:`Location` objects
        :rtype: Iterable[Union[Point, Well, Labware]]
        """
        return iter(( self._point,  self._labware))

    def __eq__(self, other: object) -> bool:
        """Comparison between two :class:`Location` objects.

        :param other: A :class:`Location` object
        :type other: :class:`Location`
        :return: True if the two :class:`Location` objects are equal, False otherwise
        :rtype: bool
        """
        return (
            isinstance(other, Location)
            and other._point == self._point
            and other._labware == self._labware
        )

    def __repr__(self) -> str:
        """Returns a string representation of the :class:`Location` object.

        :return: A string representation of the :class:`Location` object
        :rtype: str
        """
        return f"Location(point={repr(self._point)}, labware={self._labware})"
