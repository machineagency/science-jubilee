from science_jubilee.labware.Labware import Labware, Well, Location
from typing import Tuple, Union

def getxyz(location: Union[Well, Tuple, Location]):
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