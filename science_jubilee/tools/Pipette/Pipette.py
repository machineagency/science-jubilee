# from Platform.Jubilee_controller import JubileeMotionController
from Tool import Tool, ToolStateError, ToolConfigurationError
from labware.Utils import json2dict
from labware.Labware import Well
from typing import List, Dict, Tuple

import logging
logger = logging.getLogger(__name__)

class Pipette(Tool):

    def __init__(self, machine, index, name, brand, model, max_volume,
                  min_volume, zero_position, blowout_position, has_tip,
                  drop_tip_position, mmToVol):
        super().__init__(machine , index, name, brand=brand, model= model,
                         max_volume = max_volume, min_volume= min_volume,
                         zero_position= zero_position,
                         blowout_position=blowout_position, has_tip = has_tip,
                         drop_tip_position= drop_tip_position, mmToVol= mmToVol)
        
    @classmethod
    def from_config(cls, machine, index, name, config_file: str):
        kwargs = json2dict(config_file)
        return cls(machine=machine, index=index, name=name **kwargs)

    def vol2move(self, vol):
        #Function that converts uL to movement
        """
        Converts desired uL to movement on v-axis

        ---------Parameters---------

        vol: float
            The desired amount of liquid expressed in uL

        ---------Returns----------

        v: float
           The corresponding v-axix movement for the desired volume of liquid

        """
        dv = vol / self.mmToVol
        v = self.zero_position - dv

        return v
    @staticmethod
    def _getxyz(well: Well = None, location: Tuple[float] = None):
        if well is not None and location is not None:
            raise ValueError("Specify only one of Well or x,y,z location")
        elif well is not None:
            x, y, z = well.x, well.y, well.z
        else:
            x, y, z = location
        return x,y,z
    
    @staticmethod
    def _getTopBottom(well: Well = None):
        top = well.top
        bottom = well.bottom
        return top, bottom
    
    def prime(self):
        """
        Moves the plunger to the low-point on the v-axis to prepare for further commands
        This position should not engage the pipette tip plunger
        """
        self._machine.move_to(v=self.zero_position, s = 150, wait=True)
        self.is_primed = True

    def _aspirate(self, vol: float, s:int = 200):
        """
        """

        v = self.vol2move(vol)
        if self.is_primed == True:
            self._machine.move_to(v= v, s=s )
        else:
            self.prime()
            self._machine.move_to(v= v, s=s )

    def aspirate(self, vol: float, s:int = 200, well: Well = None,
                 from_bottom :float =10, from_top :float = None,
                 location: Tuple[float] = None):
       
        x, y, z = self._getxyz(well=well, location=location)
        
        if well is not None:
            top, bottom = self._getTopBottom(well=well)

        if from_bottom is not None and well is not None:
            z = bottom+ from_bottom
        elif from_top is not None and well is not None:
            z = top + from_top
            pass
        self._machine.move_to(x=x, y=y, z=z)
        self._aspirate(vol, s=s)


    def _dispense(self,vol: float, s:int = 200):
        """
        """
        v = self.vol2move(vol)

        current_v = self._machine.position()['V'] ## check this syntax
        final_v = current_v + v

        ####  check that 4th item is v-axis position
        assert current_v < self.zero_position, \
            "Pipette does not have anything to dispense"
        assert final_v <= self.zero_position, \
            "The volume to be dispensed is greater than what was aspirated"    

        dv= final_v
        self._machine.move_to(v= dv, s=s )

    def dispense(self, vol: float, s:int = 200, well: Well = None,
                 from_bottom :float =10, from_top :float = None,
                 location: Tuple[float] = None):
       
        x, y, z = self._getxyz(well=well, location=location)
        
        if well is not None:
            top, bottom = self._getTopBottom(well=well)

        if from_bottom is not None and well is not None:
            z = bottom+ from_bottom
        elif from_top is not None and well is not None:
            z = top + from_top
            pass
        self._machine.move_to(x=x, y=y, z=z)
        self._dispense(vol, s=s)

    def transfer(self, vol: float, s:int = 200, source_well :Well = None,
                 destination_well :Well = None, blowout= None):
        
        # get locations
        xs, ys, zs = self._getxyz(well=source_well, location=None)
        xd, yd, zd =self._getxyz(well=destination_well, location=None)

        # top_s, bottom_s = self._getTopBottom(well=source_well)

        # if from_bottom is not None :
        #     z = bottom + from_bottom

        # elif from_top is not None and well is not None:
        #     z = top + from_top

        vol = self.vol2move(vol)
        self._machine.move_to(x= xs, y=ys, z=zs+5) # should not be hardcoded
        self._aspirate(vol, s=s)
        self._machine.move_to(x=xd, y=yd, z=zd+5)
        self._dispense(vol, s=s)
        if blowout is not None:
            self.blowout()
        else:
            pass

        # add mix_before and mix_after



    def blowout(self, s : int = 300):
        """
        """
        self._machine.move_to(v = self.blowout_postion)
        self.prime()

        return 
    
    def _pickup_tip(self, z):
        """
        """
        if self.has_tip == False:
            self._machine.move_to(z=z, param = 'H4')
        else:
            raise ToolConfigurationError('Error: No pipette tip attached to drop')
        

    def pickup_tip(self,  well: Well = None, location: Tuple[float] = None):
        """
        """        
        x, y, z = self._getxyz(well=well, location=location)
        self._machine.move_to(x=x, y=y)
        self._pickup_tip(z)
        # move the plate down( should be + z) for safe movement
        self._machine.move_to(z= self._machine.deck.top_z + 5)
        

    def _drop_tip(self):
        """
        Moves the plunger to eject the pipette tip

        """
        if self.has_tip == True:
            self._machine.move_to(v= self.drop_tip_position, s= 150)
        else:
            raise ToolConfigurationError('Error: No pipette tip attached to drop')

        
    def drop_tip(self, well: Well = None, location: Tuple[float] = None):
        x, y, z = self._getxyz(well=well, location=location)

        if x is not None or y is not None:
            self._machine.move_to(x=x, y=y)
        self._drop_tip()
        self.prime()
        self.has_tip = False

        logger.info(f"Dropped tip at {(x,y,z)}")

    def mix(self, vol: float, n: int, s: int =150):
        v = self.vol2mov(vol)
        self._machine.move(z=-5)### Need to test this!
        for i in range(0,n):
            self.prime()
            self._machine.move_to(v=v, s=s)

        self.prime()

    # def air_gap(self,vol):
        # return
