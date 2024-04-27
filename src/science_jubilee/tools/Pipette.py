import json
import logging
import os

from itertools import dropwhile, takewhile
from science_jubilee.labware.Labware import Labware, Well, Location
from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool

from typing import Tuple, Union, Iterator, List


logger = logging.getLogger(__name__)

def tip_check(func):
    """Decorator to check if the pipette has a tip attached before performing an action.
    """
    def wrapper(self, *args, **kwargs):
        if self.has_tip == False:
            raise ToolStateError ("Error: No tip is attached. Cannot complete this action")
        else:
            func(self,*args, **kwargs)
    return wrapper

class Pipette(Tool):
    """ A class representation of an Opentrons OT2 pipette.
    """
    def __init__(self,  index, name, brand, model, max_volume,
                  min_volume, zero_position, blowout_position, 
                  drop_tip_position, mm_to_ul):
        """ Initialize the pipette object

        :param index: The tool index of the pipette on the machine
        :type index: int
        :param name: The name associated with the tool (e.g. 'p300_single')
        :type name: str
        :param brand: The brand of the pipette
        :type brand: str
        :param model: The model of the pipette
        :type model: str
        :param max_volume: The maximum volume of the pipette in uL
        :type max_volume: float
        :param min_volume: The minimum volume of the pipette in uL
        :type min_volume: float
        :param zero_position: The position of the plunger before using a :method:`aspirate` step
        :type zero_position: float
        :param blowout_position: The position of the plunger for running a :method:`blowout` step
        :type blowout_position: float
        :param drop_tip_position: The position of the plunger for running a :method:`drop_tip` step
        :type drop_tip_position: float
        :param mm_to_ul: The conversion factor for converting motor microsteps in mm to uL
        :type mm_to_ul: float
        """        
        super().__init__(index, name, brand = brand, 
                         model = model, max_volume = max_volume, min_volume = min_volume,
                         zero_position = zero_position, blowout_position = blowout_position,
                         drop_tip_position = drop_tip_position, mm_to_ul = mm_to_ul)
        self.has_tip = False
        self.current_well = None
        self.trash = None
        self.is_primed = False
        

    @classmethod
    def from_config(cls, index, name, config_file: str,
                    path :str = os.path.join(os.path.dirname(__file__), 'configs')):
        
        """Initialize the pipette object from a config file

        :param index: The tool index of the pipette on the machine
        :type index: int
        :param name: The tool name
        :type name: str
        :param config_file: The name of the config file containign the pipette parameters
        :type config_file: str
        :param path: The path to the labware configuration `.json` files for the labware,
                defaults to the 'labware_definition/' in the science_jubilee/labware directory.
        :returns: A :class:`Pipette` object
        :rtype: :class:`Pipette`
        """        
        config = os.path.join(path,config_file)
        with open(config) as f:
            kwargs = json.load(f)

        return cls(index, name, **kwargs)

    def post_load(self):
        """Prime the Pipette after loading it onto the Machine sot hat it is ready to use"""
        self.prime()

    
    def vol2move(self, vol):
        """Converts desired volume in uL to a movement of the pipette motor axis

        :param vol: The desired amount of liquid expressed in uL
        :type vol: float
        :return: The corresponding motor movement in mm
        :rtype: float
        """        
        dv = vol * self.mm_to_ul # will need to change this value

        return dv
    
    def prime(self, s=2500):
        """Moves the plunger to the low-point on the pipette motor axis to prepare for further commands
        Note::This position should not engage the pipette tip plunger

        :param s: The speed of the plunger movement in mm/min
        :type s: int
        """
        self._machine.move_to(v=self.zero_position, s = s, wait=True)
        self.is_primed = True

    @requires_active_tool
    def _aspirate(self, vol: float, s:int = 2000):
        """Moves the plunger upwards to aspirate liquid into the pipette tip

        :param vol: The volume of liquid to aspirate in uL
        :type vol: float
        :param s: The speed of the plunger movement in mm/min
        :type s: int
        """
        if self.is_primed == True:
            pass
        else:
            self.prime()

        dv = self.vol2move(vol)*-1
        pos = self._machine.get_position()
        end_pos = float(pos['V']) + dv

        self._machine.move_to(v=end_pos, s=s )
    
    @requires_active_tool
    @tip_check
    def aspirate(self, vol: float, location : Union[Well, Tuple, Location], s:int = 2000):
        """Moves the pipette to the specified location and aspirates the desired volume of liquid

        :param vol: The volume of liquid to aspirate in uL
        :type vol: float
        :param location: The location from where to aspirate the liquid from.
        :type location: Union[Well, Tuple, Location]
        :param s: The speed of the plunger movement in mm/min, defaults to 2000
        :type s: int, optional
        :raises ToolStateError: If the pipette does not have a tip attached
        """
        x, y, z = Labware._getxyz(location)
        
        if type(location) == Well:
            self.current_well = location
        elif type(location) == Location:
            self.current_well = location._labware
        else:
            pass
    
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._aspirate(vol, s=s)

    @requires_active_tool
    @tip_check
    def _dispense(self,vol: float, s:int = 2000):
        """Moves the plunger downwards to dispense liquid out of the pipette tip

        :param vol: The volume of liquid to dispense in uL
        :type vol: float
        :param s: The speed of the plunger movement in mm/min
        :type s: int

        Note:: Ideally the user does not call this functions directly, but instead uses the :method:`dispense` method
        """
        dv = self.vol2move(vol)
        pos = self._machine.get_position()
        end_pos = float(pos['V']) + dv
        
        #TODO: Figure out why checks break for transfer, work fine for manually aspirating and dispensing
        #if end_pos > self.zero_position:
        #    raise ToolStateError("Error: Pipette does not have anything to dispense")
        #elif dv > self.zero_position:
        #    raise ToolStateError ("Error : The volume to be dispensed is greater than what was aspirated") 
        self._machine.move_to(v = end_pos, s=s )

    @requires_active_tool
    @tip_check
    def dispense(self, vol: float, location :Union[Well, Tuple, Location], s:int = 2000):
        """Moves the pipette to the specified location and dispenses the desired volume of liquid

        :param vol: The volume of liquid to dispense in uL
        :type vol: float
        :param location: The location to dispense the liquid into. 
        :type location: Union[Well, Tuple, Location]
        :param s: The speed of the plunger movement in mm/min, defaults to 2000
        :type s: int, optional
        :raises ToolStateError: If the pipette does not have a tip attached
        """
        x, y, z = Labware._getxyz(location)
        
        if type(location) == Well:
            self.current_well = location
            if z == location.z:
                z= z+10
            else:
                pass
        elif type(location) == Location:
            self.current_well = location._labware
        else:
            pass
        
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=z)
        self._dispense(vol, s=s)

    @requires_active_tool
    def transfer(self, vol: Union[float, list[float]], source_well: Union[Well, Tuple, Location],
                 destination_well :Union[Well, Tuple, Location] , s:int = 3000,
                 blowout= None, mix_before: tuple = None,
                 mix_after: tuple = None, air_gap : float = 0,
                 new_tip : str = 'always'):
        
        """Transfers the desired volume of liquid from the source well to the destination well

        This is a combination of the :method:`aspirate` and :method:`dispense` steps.
        
        :param vol: The volume of liquid to transfer in uL
        :type vol: float
        :param source_well: The location from where to aspirate the liquid from. 
        :type source_well: Union[Well, Tuple, Location]
        :param destination_well: The location to dispense the liquid into. 
        :type destination_well: Union[Well, Tuple, Location]
        :param s: The speed of the plunger movement in mm/min, defaults to 3000
        :type s: int, optional
        :param blowout: The location to blowout any remainign liquid in the pipette tip
        :type blowout: Union[Well, Tuple, Location], optional
        :param mix_before: The number of times to mix before dispensing and the volume to mix
        :type mix_before: tuple, optional
        :param mix_after: The number of times to mix after dispensing and the volume to mix
        :type mix_after: tuple, optional
        :param new_tip: Whether or not to use a new tip for the transfer. Can be 'always', 'never', or 'once' 
        :type new_tip: str, optional
        :param air_gap: The volume of air to aspirate after aspirating the liquid, defaults to None
        :type air_gap: float, optional

        Note:: :param new_tip: still not implemented at the moment (2023-11-16) 
        """
        #TODO: check that tip picked up and get a new one if not

        if self.is_primed == True:
            pass
        else:
            self.prime()

        if new_tip == 'never':
            assert self.has_tip == True, "Error: Pipette should have a tip before transfer with new_tip = 'never'"    
        else:
            assert self.has_tip == False, f"Error: Pipette should not have a tip before transfer with new_tip = '{new_tip}'"
        if air_gap > 0:
            assert air_gap < self.max_volume,\
                "Error: Air gap volume should be less than Pipette max volume."
        assert self.trash != None, "Error: Trash location not set, do so before continuing."
        # saves some code if we make a list regardless    
        if type(destination_well) != list:
            destination_well = [destination_well] #make it into a list
                
        if type(source_well) != list:
            source_well = [source_well] #make it into a list  

        total_transfers = max(len(source_well), len(destination_well))  
        volumes = self._create_volume_list(vol, total_transfers)
        source_well, destination_well = self._extend_source_target_lists(source_well, destination_well)
        targets = zip(source_well, destination_well)
        iterations= self._expand_for_volume_contraints(volumes, targets, self.max_volume-air_gap)    

        ## TODO: maybe add TiTracker to pipette class
        TT = self.TipTracker
        TT_dict = TT._tip_stock_mapping

        for step_vol, (source, dest) in iterations:
            # skip if the volume is zero
            if step_vol == 0:
                continue
            else:
                if type(source) == Well:
                    src = source
                elif type(source) == Location:
                    src = source._labware
                
                # get coordinates for source and destination wells
                xs, ys, zs = Labware._getxyz(source)
                xd, yd, zd = Labware._getxyz(dest)

                source_name = f'{src.name}_{src.slot}'
                
                # --------------- Tip Strategy ----------------
                if new_tip == 'never':
                    pass
                elif new_tip == 'once':
                    if source_name in TT_dict.keys():
                        tip = TT_dict[source_name]
                    else:
                        tip = TT.next_tip()
                        TT.assign_tip_to_stock(tip, source_name)
                else:
                    tip = TT.next_tip()
                
                self.pickup_tip(tip)
                TT.use_tip(tip) # note on the TipTracker class that tip is being used

                # --------------- Aspirate ----------------

                self._machine.safe_z_movement()
                self._machine.move_to(x= xs, y=ys)
                
                self.current_well = src
                
                self._machine.move_to(z = zs)
                self._aspirate(step_vol, s=s)
                
                if air_gap > 0:
                    self.air_gap(air_gap) # the check for this is in the _create_volume_list method
                
                #mix before moving to destination well
                if mix_before:
                    self.mix(mix_before[0], mix_before[1]) 
                else:
                    pass
                
                # --------------- Dispense  ----------------

                self._machine.safe_z_movement()
                self._machine.move_to(x=xd, y=yd)
                if type(dest)==Well:
                    self.current_well = dest
                elif type(dest)==Location:
                    self.current_well = dest._labware
                self._machine.move_to(z=zd)
                self._dispense(step_vol, s=s)

                #mix after dispensing into destination well
                # check if user indicated a specific well to mix after dispensing
                if mix_after:
                    if len(mix_after) == 3:
                        stock_to_mix = mix_after[2]
                        if type(stock_to_mix) == Location:
                            stock_to_mix = stock_to_mix._labware
                        elif type(stock_to_mix) == Well:
                            pass
                        if src == stock_to_mix:
                            self.mix(mix_after[0], mix_after[1])
                        else:
                            pass
                    elif mix_after:
                        self.mix(mix_after[0], mix_after[1])
                    else:
                        pass
                
                #blow_out if indicated
                if blowout:
                    self.blowout()
                else:
                    pass
                
                # --------------- Tip Strategy ----------------
                if new_tip == 'always':
                    self.drop_tip()
                elif new_tip == 'once':
                    if mix_after:
                        if len(mix_after)==3 and src == stock_to_mix:
                            self.drop_tip()
                            TT_dict.pop(source_name)
                        else:
                            self.return_tip(tip)
                    else:
                        self.return_tip(tip)
                else:
                    pass
    
    def _create_volume_list(self, volume, total_xfers):
        """Creates a list of volumes to transfer
        
        :param volume: The volume of liquid to transfer
        :type volume: Union[float, list[float]]
        :param total_xfers: The total number of transfer steps to perform
        :type total_xfers: int
        :return: A list of volumes to transfer

        Note: This function was taken from the Opentrons API and modified to work with the Pipette class of Science_Jubilee
        """

        if isinstance(volume, (float, int)):
            vol_list = [self.vol2move(volume)] * total_xfers
            return [volume] * total_xfers
        elif isinstance(volume, list):
            if not len(volume) == total_xfers:
                raise RuntimeError(
                    "List of volumes should be equal to number " "of transfers"
                )
            else:
                vol_list = [self.vol2move(v) for v in volume]
                return vol_list
        else:
            if not isinstance(volume, List):
                raise TypeError(
                    "Volume expected as a number or List or"
                    " tuple but got {}".format(volume)
                )
            return vol_list

    @staticmethod
    def _extend_source_target_lists(
        sources: List[Union[Well, Location]],
        targets: List[Union[Well, Location]],
    ):
        """Extend source or target list to match the length of the other
        
        :param sources: The list of source wells
        :type sources: List[Union[Well, Location]]
        :param targets: The list of target wells
        :type targets: List[Union[Well, Location]]
        :return: The extended source and target lists
        :rtype: Tuple[List[Union[Well, Location]], List[Union[Well, Location]]]

        Note: This function was taken from the Opentrons API and modified to work with the Pipette class of Science_Jubilee
        """
        if len(sources) < len(targets):
            if len(targets) % len(sources) != 0:
                raise ValueError("Source and destination lists must be divisible")
            sources = [
                source
                for source in sources
                for i in range(int(len(targets) / len(sources)))
            ]
        elif len(sources) > len(targets):
            if len(sources) % len(targets) != 0:
                raise ValueError("Source and destination lists must be divisible")
            targets = [
                target
                for target in targets
                for i in range(int(len(sources) / len(targets)))
            ]
        return sources, targets    

    @staticmethod
    def _expand_for_volume_contraints( volumes: Iterator[float], targets: Iterator, max_volume:float):
        """ Expands the volumes and targets to ensure that the volume does not exceed the maximum volume of the pipette

        :param volumes: An iterator of the volumes to transfer
        :type volumes: Iterator[float]
        :param targets: An iterator of the targets to transfer the volumes to
        :type targets: Iterator
        :param max_volume: The maximum volume of the pipette in uL
        :type max_volume: float
        :return: An iterator of the volumes and targets to transfer
        :rtype: Iterator

        Note: This function was taken from the Opentrons API and modified to work with the Pipette class of Science_Jubilee
        """    
        for volume, target in zip(volumes, targets):
            while volume > max_volume*2:
                yield max_volume, target
                volume -= max_volume
            
            if volume > max_volume:
                volume /= 2
                yield volume, target
            yield volume, target

    @requires_active_tool
    @tip_check
    def blowout(self,  s : int = 6000):
        """Blows out any remaining liquid in the pipette tip

        :param s: The speed of the plunger movement in mm/min, defaults to 3000
        :type s: int, optional
        """

        well = self.current_well
        self._machine.move_to(z = well.top_ + 2 )
        self._machine.move_to(v = self.blowout_position, s=s)
        self.prime()
    
    @requires_active_tool
    @tip_check
    def air_gap(self, vol):
        """Moves the plunger upwards to aspirate air into the pipette tip

        :param vol: The volume of air to aspirate in uL
        :type vol: float
        """
        #TODO: Add a check to ensure compounded volume does not exceed max volume of pipette
        
        dv = self.vol2move(vol)*-1
        well = self.current_well
        self._machine.move_to(z = well.top_ + 20)
        self._machine.move(v= -1*dv)

    @requires_active_tool
    @tip_check
    def mix(self, vol: float, n: int, s: int = 5500):
        """Mixes liquid by alternating aspirate and dispense steps for the specified number of times

        :param vol: The volume of liquid to mix in uL
        :type vol: float
        :param n: The number of times to mix
        :type n: int
        :param s: The speed of the plunger movement in mm/min, defaults to 5000
        :type s: int, optional
        """
        v = self.vol2move(vol)*-1

        self._machine.move_to(z = self.current_well.top_+ 1)
        self.prime()
        
        # TODO: figure out a better way to indicate mixing height position that is not hardcoded
        self._machine.move_to(z= self.current_well.bottom_ + 1) 
        for i in range(0,n):
            self._aspirate(vol, s=s)
            self.prime(s=s)   

## In progress (2023-10-12) To test
    @requires_active_tool
    @tip_check
    def stir(self, n_times: int = 1, height: float= None):
        """Stirs the liquid in the current well by moving the pipette tip in a circular motion

        :param n_times: The number of times to stir the liquid, defaults to 1
        :type n_times: int, optional
        :param height: The z-coordinate to move the tip to during the stir step, defaults to None
        :type height: float, optional
        :raises ToolStateError: If the pipette does not have a tip attached before stirring or if the pipette is not in a well
        """
        z= self.current_well.z + 0.5  # place pieptte tip close to the bottom
        pos =  self._machine.get_position()
        x_ = float(pos['X']) 
        y_ = float(pos['Y'])
        z_ = float(pos['Z'])  

        # check position first
        if x_ != round(self.current_well.x) and y_ != round(self.current_well.y, 2):
            raise ToolStateError("Error: Pipette shuold be in a well before it can stir")  
        elif z_ != round(z,2):
            self._machine.move_to(z=z)

        radius = self.current_well.diameter/2 -(self.current_well.diameter/6) # adjusted so that it does not hit the walls fo the well 

        for n in range(n_times):
            x_sp = self.current_well.x
            y_sp = self.current_well.y
            I = -1*radius
            J = 0 # keeping same y so relative y difference is 0
            if height:
                Z = z + height
                self._machine.gcode(f'G2 X{x_sp} Y{y_sp} Z{Z} I{I} J{J}')
                self._machine.gcode(f'M400') # wait until movement is completed
                self._machine.move_to(z=z) 
            else:
                self._machine.gcode(f'G2 X{x_sp} Y{y_sp} I{I} J{J}')
                self._machine.gcode(f'M400') # wait until movement is completed

    def update_z_offset(self, tip: bool = None):
        """Shift the z-offset of the tool to account for the tip length

        :param tip: Parameter to indicated whether to add or remove the tip offset, defaults to None
        :type tip: bool, optional
        """
        if isinstance(self.tiprack, list):
            tip_offset = self.tiprack[0].tip_length - self.tiprack[0].tip_overlap
        else:
            tip_offset = self.tiprack.tip_length - self.tiprack.tip_overlap

        if tip == True:
            new_z = self.tool_offset - tip_offset
        else:
            new_z = self.tool_offset

        self._machine.gcode(f'G10 P{self.index} Z{new_z}')

    def add_tiprack(self, tiprack: Union[Labware, list]):
        """Associate a tiprack with the pipette tool

        :param tiprack: The tiprack to associate with the pipette 
        :type tiprack: Union[Labware, list]
        """
        if type(tiprack) != list:
            tiprack = [tiprack]
        
        tips = []
        for rack in tiprack:
            for t in range(96):
                tips.append(rack[t])
        
        self.tips = tips
        self.TipTracker = TipTracker(tips) 
        self.tiprack = tiprack

    @requires_active_tool
    def _pickup_tip(self, z):
        """Moves the Jubilee Z-axis upwards to pick up a pipette tip and stops once the tip sensor is triggered

        :param z: The z-coordinate to move the pipette to
        :type z: float
        :raises ToolStateError: If the pipette already has a tip attached
        """
        if self.has_tip == False:
            # self._machine.move_to(z=z-10 , s=1200) # test this- we might benefit from a faster approach to pickingup pipette and then slowing down
            self._machine.move_to(z=z, s=800, param = 'H4')
        else:
            raise ToolStateError("Error: Pipette already equipped with a tip.")  
        #TODO: Should this be an error or a warning?     

    @requires_active_tool    
    def pickup_tip(self, tip_ : Union[Well, Tuple] = None):
        """Moves the pipette to the specified location and picks up a tip

        This function can either take a specific tip or if not specified, will pick up the next available 
        tip in the tiprack associated with the pipette.
        
        :param tip_: The location of the pipette tip to pick up, defaults to None
        :type tip_: Union[Well, Tuple], optional
        """
        if tip_ is None:
            tip = self.TipTracker.next_tip()
            self.TipTracker.use_tip(tip)
        else:
            tip = tip_
            tip_.set_has_tip(False)
            tip_.set_clean_tip(False)

        x, y, z = Labware._getxyz(tip)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._pickup_tip(z)
        self.has_tip = True
        self.update_z_offset(tip= True)
        # # move the plate down( should be + z) for safe movement
        self._machine.move_to(z= self._machine.deck.safe_z + 10)

    @requires_active_tool
    def return_tip(self, location: Well = None):
        """Returns the pipette tip to the either the specified location or to where the tip was picked up from

        :param location: The location to return the tip to, defaults to None (i.e. return to where the tip was picked up from)
        :type location: :class:`Well`, optional
        """
        if location is None:
            w = self.TipTracker.previous_tip()
            x, y, z = Labware._getxyz(w)
        else:
            if type(location) == Well:
                w = location
            elif type(location) == Location:
                w = location._labware

            x, y, z = Labware._getxyz(location)

        self.TipTracker.return_tip(w) # this will still setthe pipette tip as not clean!

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        # z moves up/down to make sure tip actually makes it into rack 
        self._machine.move_to(z = w.bottom_ + 20)
        self._drop_tip()
        self.prime()
        self._machine.move_to(z = w.bottom_ + 30)
        self.has_tip = False
        self.update_z_offset(tip=False)

    @requires_active_tool
    @tip_check
    def _drop_tip(self):
        """Moves the plunger to eject the pipette tip

        :raises ToolConfigurationError: If the pipette does not have a tip attached
        """
        self._machine.move_to(v= self.drop_tip_position, s= 5000)


    @requires_active_tool
    @tip_check
    def drop_tip(self, location: Union[Well, Tuple]= None):
        """Moves the pipette to the specified location and drops the pipette tip

        :param location: The location to drop the tip into
        :type location: Union[:class:`Well`, tuple]
        """        

        if location is None and self.trash:
            x, y, z = Labware._getxyz(self.trash)
        elif location is not None:
            x, y, z = Labware._getxyz(location)
        else:
            raise ToolConfigurationError("Error: No location specified to drop tip into. Either specify a location or set the trash location for the Pipette")

        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._drop_tip()
        self.prime()
        self.has_tip = False
        self.update_z_offset(tip=False)

        # logger.info(f"Dropped tip at {(x,y,z)}")


class TipTracker:
    """A class to track the usage of pipette tips and their location in the tiprack

    :param tips: The list of tips in the tiprack
    :type tips: list[:class:`Well`]
    :param start_well: The starting well to begin tracking the tips from, defaults to None
    :type start_well: :class:`Well`, optional

    Note: This function was taken from the Opentrons API and modified to work with the Pipette class of Science_Jubilee
    """

    def __init__(self, tips, start_well=None):
        
        self._wells = tips[start_well:]
        self._available_clean_tips = tips
        self._tip_stock_mapping = {}
        
    def next_tip(self, start_well=None):
        if start_well:
            start_index = self._wells.index(start_well)
            available_wells = list(dropwhile(lambda w: not w.has_tip, self._available_clean_tips[start_index:]))
        else:
            available_wells = list(dropwhile(lambda w: not w.has_tip, self._available_clean_tips))
        
        assert available_wells, "No more available tips"

        clean_tips = list(dropwhile(lambda w: not w.clean_tip == True, available_wells))        
        if clean_tips:
            self._available_clean_tips = clean_tips
        else:   
            self._available_clean_tips = []

        first_available_well = clean_tips[0]
        return first_available_well
    
    def use_tip(self, tip_well):
        tip_well.set_has_tip(False)
        tip_well.set_clean_tip(False)
    
    def previous_tip(self):

        drop_leading_filled = list(dropwhile(lambda w: w.has_tip, self._wells))
        first_gap = list(takewhile(lambda w: not w.has_tip, drop_leading_filled))
        try:
            return first_gap[-1]
        except IndexError:
            return None
    
    def return_tip(self, well=None):
        if well.has_tip:
            raise AssertionError(f"Well {repr(well)} has a tip")
        else:
            well.set_has_tip(True)

    def assign_tip_to_stock(self, tip_well, stock_well):
               
        if stock_well in self._tip_stock_mapping.keys():
            pass
        else:
            self._tip_stock_mapping[stock_well] = tip_well
