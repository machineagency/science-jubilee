# from Platform.Jubilee_controller import JubileeMotionController
import json
import logging
import os

from labware.Labware import Labware, Well
from .Tool import Tool, ToolStateError, ToolConfigurationError
from typing import Tuple, Union


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
        config = os.path.join(path,config_file)
        kwargs = json.load(config)
        return cls(machine=machine, index=index, name=name, tiprack= tiprack, **kwargs)
   
    @staticmethod
    def _getxyz(location: Union[Well, Tuple]):
        if type(location) == Well:
            x, y, z = location.x, location.y, location.z
        elif type(location) == Tuple:
            x, y, z = location
        else:
            raise ValueError("Location should be of type Well or Tuple")
        
        return x,y,z
    
    @staticmethod
    def _getTopBottom(location: Well):
        top = location.top
        bottom = location.bottom
        return top, bottom
        
    def vol2move(self, vol):
        #Function that converts uL to movement
        """
        Converts desired uL to movement on v-axis

        ---------Parameters---------

        vol: float
            The desired amount of liquid expressed in uL

        ---------Returns----------

        dv: float
           The corresponding v-axix movement for the desired volume of liquid

        """
        dv = vol / self.mm_to_ul

        return dv
    
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

        dv = self.vol2move(vol)*-1
        pos = self._machine.get_position()
        end_pos = float(pos['V']) + dv
        self._machine.move_to(v=end_pos, s=s )

    def aspirate(self, vol: float, location : Union[Well, Tuple], s:int = 2000,
                 from_bottom :float =10, from_top :float = None):
       
        if self.has_tip is False:
            raise ToolStateError ("Error: tip needs to be attached before aspirating liquid")
        else:
            pass

        x, y, z = self._getxyz(location)
        
        if type(location) == Well:
            self.current_well = location

            top, bottom = self._getTopBottom(location)
            if from_bottom is not None :
                z = bottom+ from_bottom
            elif from_top is not None:
                z = top + from_top
            else:
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
        dv = self.vol2move(vol)
        pos = self._machine.get_position()
        end_pos = float(pos['V']) + dv
        
        if end_pos > self.zero_position:
            raise ToolStateError("Error: Pipette does not have anything to dispense")
        elif dv > self.zero_position:
            raise ToolStateError ("Error : The volume to be dispensed is greater than what was aspirated")    
        self._machine.move(v= end_pos, s=s )

    def dispense(self, vol: float, location :Union[Well, Tuple], s:int = 2000, 
                 from_bottom :float =10, from_top :float = None):
       
        x, y, z = self._getxyz(location)
        
        if type(location) == Well:
            self.current_well = location

            top, bottom = self._getTopBottom(location)
            if from_bottom is not None :
                z = bottom+ from_bottom
            elif from_top is not None:
                z = top + from_top
            else:
                pass
        
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._dispense(vol, s=s)


    def transfer(self, vol: float, source_well: Union[Well, Tuple],
                 destination_well :Union[Well, Tuple] , s:int = 2000,
                 blowout= None, mix_before: tuple = None,
                 mix_after: tuple = None, new_tip : str = 'always'):
        
        vol_ = self.vol2move(vol) -1
        # get locations
        xs, ys, zs = self._getxyz(source_well)

        # saves some code if we make a list regardless    
        if type(destination_well) != list:
            destination_well = list(destination_well) 

        if isinstance(destination_well, list):
            for well in destination_well:
                xd, yd, zd =self._getxyz(destination_well[well])
                
                
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

                #TODO: need to add new_tip option!


    def blowout(self,  s : int = 2000):
        """
        """

        well = self.current_well
        self._machine.move_to(z = well.top + 5 )
        self._machine.move_to(v = self.blowout_position, s=s)
        self.prime()

        return 
    
    def air_gap(self, vol):
        
        dv = self.vol2move(vol)*-1
        well = self.current_well
        self._machine.move_to(z = well.top + 20)
        self._machine.move(v= -1*dv)

    def mix(self, vol: float, n: int, s: int =2000):
        
        v = self.vol2mov(vol)*-1
        
        self._machine.move(z= -5) 
        for i in range(0,n):
            self.prime()
            self._machine.move_to(v=v, s=s)

        self.prime()   

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

    def _pickup_tip(self, z):
        """
        """
        if self.has_tip == False:
            self._machine.move_to(z=z, s=800, param = 'H4')
        else:
            raise ToolStateError("Error: Pipette already equipped with a tip.")      
        
    def pickup_tip(self, tip_ : Union[Well, Tuple]):
        """
        """
        if tip_ is None:
            tip = self.first_available_tip
        else:
            tip = tip_

        x, y, z = self._getxyz(tip)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._pickup_tip(z)
        self.has_tip = True
        self.update_z_offset(tip= True) ### to do!
        # if tip is not None:
        #     self.first_available_tip =  self.tiprack.next()
        # move the plate down( should be + z) for safe movement
        self._machine.move_to(z= self._machine.deck.safe_z + 10)

        #TODO: This should probably iterate the next available tip so that if you use a tip then replace it, you have to manually specify to go use that tip again rather than it just getting picked up. 

    def return_tip(self):
        x, y, z = self._getxyz(self.first_available_tip)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._drop_tip()
        self.prime()
        self.has_tip = False
        self.update_z_offset(tip=False)

    def _drop_tip(self):
        """
        Moves the plunger to eject the pipette tip
        """
        if self.has_tip == True:
            self._machine.move_to(v= self.drop_tip_position, s= 2000)
        else:
            raise ToolConfigurationError('Error: No pipette tip attached to drop')

    def drop_tip(self, location: Union[Well, Tuple] ):
        x, y, z = self._getxyz(location)

        self._machine.safe_z_movement()
        if x is not None or y is not None:
            self._machine.move_to(x=x, y=y)
        self._drop_tip()
        self.prime()
        self.has_tip = False
        self.update_z_offset(tip=False)

        self.first_available_tip = self.tipiterator.next()
        # logger.info(f"Dropped tip at {(x,y,z)}")


class pipette_iterator():

    def __init__(self, tiprack):
        self.tiprack = tiprack
        self.index = 0

    def next(self):
        try:
            result = self.tiprack[self.index]
            self.index += 1
        except IndexError:
            raise StopIteration
        return result

    def prev(self):
        self.index -= 1
        if self.index < 0:
            raise StopIteration
        return self.tiprack[self.index]

    def __iter__(self):
        return self
