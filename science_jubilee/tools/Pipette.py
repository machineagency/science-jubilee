# from Platform.Jubilee_controller import JubileeMotionController
import os
from .Tool import Tool, ToolStateError, ToolConfigurationError
from labware.Utils import json2dict, pipette_iterator
from labware.Labware import Labware, Well
from typing import Tuple, Union

import logging
logger = logging.getLogger(__name__)


class Pipette(Tool):

    def __init__(self, machine, index, name, tiprack, brand, model, max_volume,
                  min_volume, zero_position, blowout_position, 
                  drop_tip_position, mm_to_ul):
        super().__init__(machine , index, name, tiprack = tiprack, brand = brand, 
                         model = model, max_volume = max_volume, min_volume = min_volume,
                         zero_position = zero_position, blowout_position = blowout_position,
                         drop_tip_position = drop_tip_position, mm_to_ul = mm_to_ul)
        self.has_tip = False
        self.is_active_tool = False
        self.first_available_tip = None
        self.tool_offset = self._machine.tool_z_offsets[self.index]
        self.is_primed = False 
        

    @classmethod
    def from_config(cls, machine, index, name, config_file: str,
                    path :str = os.path.join(os.path.dirname(__file__), 'configs'),
                    tiprack: Labware = None):
        kwargs = json2dict(config_file, path = path)
        return cls(machine=machine, index=index, name=name, tiprack= tiprack, **kwargs)

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
        dv = vol / self.mm_to_ul
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
        self._machine.move_to(v=self.zero_position, s = 2500, wait=True)
        self.is_primed = True

    def _aspirate(self, vol: float, s:int = 2000):
        """
        """

        v = self.vol2move(vol)
        self._machine.move_to(v= v, s=s )

    def aspirate(self, vol: float, s:int = 2000, well: Well = None,
                 from_bottom :float =10, from_top :float = None,
                 location: Tuple[float] = None):
       
        if self.has_tip is False:
            raise ToolStateError ("Error: tip needs to be attached before aspirating liquid")
        else:
            pass

        x, y, z = self._getxyz(well=well, location=location)
        
        if well is not None:
            top, bottom = self._getTopBottom(well=well)
            self.current_well = well

        if from_bottom is not None and well is not None:
            z = bottom+ from_bottom
        elif from_top is not None and well is not None:
            z = top + from_top
            pass
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        if self.is_primed == True:
            pass
        else:
            self.prime()
        self._machine.move_to(z=z)
        self._aspirate(vol, s=s)


    def _dispense(self,vol: float, s:int = 2000):
        """
        """
        v =  self.vol2move(vol)

        current_v = float(self._machine.get_position()['V']) 
        dv = current_v + v
        
        print(dv)
        
        if current_v > self.zero_position:
            raise ToolStateError("Error: Pipette does not have anything to dispense")
        elif dv > self.zero_position:
            raise ToolStateError ("Error : The volume to be dispensed is greater than what was aspirated")    
        self._machine.move(v= dv, s=s )

    def dispense(self, vol: float, s:int = 2000, well: Well = None,
                 from_bottom :float =10, from_top :float = None,
                 location: Tuple[float] = None):
       
        x, y, z = self._getxyz(well=well, location=location)
        
        if well is not None:
            top, bottom = self._getTopBottom(well=well)
            self.current_well = well

        if from_bottom is not None and well is not None:
            z = bottom+ from_bottom
        elif from_top is not None and well is not None:
            z = top + from_top
            pass
        
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._dispense(vol, s=s)


    def transfer(self, vol: float, s:int = 2000, source_well :Well = None,
                 destination_well :Well = None, blowout= None, mix_before: tuple = None,
                 mix_after: tuple = None, new_tip : str = 'always'):
        
        vol_ = self.vol2move(vol)
        # get locations
        xs, ys, zs = self._getxyz(well=source_well)

        # saves some code if we make a list regardless    
        if type(destination_well) != list:
            destination_well = list(destination_well) 

        if isinstance(destination_well, list):
            for well in destination_well:
                xd, yd, zd =self._getxyz(well=destination_well[well])
                
                
                self._machine.safe_z_movement()
                self._machine.move_to(x= xs, y=ys)
                self._machine.move_to(z =zs+5)
                self.current_well = source_well
                self._aspirate(vol_, s=s)
                
                if mix_before:
                    self.mix(mix_before[0], mix_before[1]) 
                else:
                    pass

                self._machine.safe_z_movement()
                self._machine.move_to(x=xd, y=yd)
                self._machine.move_to(z=zd+5)
                self.current_well = destination_well[well]
                self._dispense(vol_, s=s)
                
                if mix_after:
                    self.mix(mix_after[0], mix_after[1]) 
                else:
                    pass

                if blowout is not None:
                    self.blowout()
                else:
                    pass
                # if new_tip == 'always':

                # need to add new_tip option!


    def blowout(self,  s : int = 2000):
        """
        """

        well = self.current_well
        self._machine.move_to(z = well.top + 5 )
        self._machine.move_to(v = self.blowout_position, s=s)
        self.prime()

        return 
    
    def air_gap(self, vol):
        
        dv = self.vol2move(vol)
        well = self.current_well
        self._machine.move_to(z = well.top + 20)
        self._machine.move(v= -1*dv)

    def _pickup_tip(self, z):
        """
        """
        if self.has_tip == False:
            self._machine.move_to(z=z, s=800, param = 'H4')
        else:
            raise ToolStateError("Error: Pipette already equipped with a tip.")      

    def update_z_offset(self, tip: bool = None):
        
        if isinstance(self.tiprack, list):
            tip_offset = self.tiprack[0].tipLength- self.tiprack[0].tipOverlap
        else:
            tip_offset = self.tiprack.tipLength- self.tiprack.tipOverlap

        if tip == True:
            new_z = self.tool_offset - tip_offset
        else:
            new_z = self.tool_offset + tip_offset

        self._machine.gcode(f'G10 P{self.index} Z{new_z}')
        # self._machine.
        

    def add_tiprack(self, tiprack: Union[Labware, list]):
        if isinstance(tiprack, list):
            for rack in len(tiprack):
                tips = []
                for t in range(96):
                    tips.append(rack[t])
            
            self.tipiterator = pipette_iterator(tips)
            self.tiprack = tiprack
        else:
            self.tipiterator = pipette_iterator(tiprack)
            self.tiprack = tiprack
        
        self.first_available_tip = self.tipiterator.next()


    def pickup_tip(self, tip_ : Well = None):
        """
        """
        if tip_ is None:
            tip = self.first_available_tip
        else:
            tip = tip_

        x, y, z = self._getxyz(well=tip)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._pickup_tip(z)
        self.has_tip = True
        self.update_z_offset(tip= True) ### to do!
        # if tip is not None:
        #     self.first_available_tip =  self.tiprack.next()
        # move the plate down( should be + z) for safe movement
        self._machine.move_to(z= self._machine.deck.safe_z + 10)


    def _drop_tip(self):
        """
        Moves the plunger to eject the pipette tip

        """
        if self.has_tip == True:
            self._machine.move_to(v= self.drop_tip_position, s= 2000)
        else:
            raise ToolConfigurationError('Error: No pipette tip attached to drop')


    def return_tip(self):
        x, y, z = self._getxyz(well=self.first_available_tip)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._drop_tip()
        self.prime()
        self.has_tip = False
        self.update_z_offset(tip=False)


    def drop_tip(self, well: Well = None, location: Tuple[float] = None):
        x, y, z = self._getxyz(well=well, location=location)

        self._machine.safe_z_movement()
        if x is not None or y is not None:
            self._machine.move_to(x=x, y=y)
        self._drop_tip()
        self.prime()
        self.has_tip = False
        self.update_z_offset(tip=False)

        self.first_available_tip = self.tipiterator.next()
        # logger.info(f"Dropped tip at {(x,y,z)}")

    def mix(self, vol: float, n: int, s: int =2000):
        
        v = self.vol2mov(vol)
        
        self._machine.move(z= -5) 
        for i in range(0,n):
            self.prime()
            self._machine.move_to(v=v, s=s)

        self.prime()
