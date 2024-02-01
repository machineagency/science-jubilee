import adafruit_mcp4725
import board
import busio
import digitalio
import logging
import serial
import time


from science_jubilee.labware.Labware import Labware, Well, Location
from science_jubilee.tools.Tool import Tool, requires_active_tool
from typing import Tuple, Union


logger = logging.getLogger(__name__)



class Sonicator(Tool):
    """A class representation for a Qsonica Sonicator tool."""
    def __init__(self,  index, name, mode:str, port:str = None):
        """Initialize a Sonicator object.
        
        :param index: index of the tool
        :type index: int
        :param name: name of the tool
        :type name: str
        :param mode: mode of the sonicator. Either Raspberry Pi 'Pico' or 'Hat'
        :type mode: str
        :param port: if using a Raspberry Pi pico, the usb port used to communicate with the Pico microcontroller need to be provided, this is computer dependent.
        :type port: str
        """
        super().__init__(index, name)
        self.tool_offset = self._machine.tool_z_offsets[self.index]
        self.interface_mode = mode # either Raspberry Pi Pico or Raspberry Pi Hat
        if mode == 'Pico':
            assert port is not None, \
                "Error: port must be specified for serial interface with Pico microcontroller"
        elif mode == 'Hat':
            # initialize board pins
            self._raspberrypi_hat()
            pass

    def _raspberrypi_hat(self):
        """Initialize the pins used on the Raspberry Pi Hat."""

        # define DAC pins for I2C communication 
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.dac = adafruit_mcp4725.MCP4725(self.i2c, address=0x60)
        self.sonicator_enable = digitalio.DigitalInOut(board.D4)
        self.sonicator_enable.direction = digitalio.Direction.OUTPUT
        self.sonicator_enable.value = False # turns off D4 pin to ensure sonicator is off
        self.dac.normalized_value = 0.0 # sets DAC to 0.0 to ensure sonicator is off 

    def _raspberrypi_pico(self, port:str):
        """Initialize serial interface with Raspberry Pi Pico microcontroller.
        
        :param port: port to connect to the Pico microcontroller, this is computer dependent.
        :type port: str
        """
        ser = serial.Serial(port, baudrate=115200, timeout=1)
        ser.flush() # let's clean buffer before we start communication
        self.serial_interface = ser

    def _set_sonication_power(self, power:float):
        """Set the power of the sonicator to a value between 0.4 and 1.0.
        
        :param power: power level to set the sonicator to. Must be between 0.4 and 1.0.
        :type power: float
        """
        assert 0.4 <= power <= 1.0, \
            f"Error: power must be between 0.4 and 1.0. Value specified is: {power}"
        if self.interface_mode == 'Pico':
            self.serial_interface.write(f'DAC:{power}\n'.encode('utf-8'))
            while self.ser.out_waiting > 0: # wait for message to be sent
                pass
        elif self.interface_mode == 'Hat':
            self.dac.normalized_value = power
    
    @requires_active_tool
    def _sonication_on(self):
        """Turn on the sonicator."""
        if self.interface_mode == 'Pico':
            self.serial_interface.write(b'SONICATOR_ON\n')
            while self.ser.out_waiting > 0:
                pass
        elif self.interface_mode == 'Hat':
            self.sonicator_enable.value = True

    def _sonication_off(self):
        """Turn off the sonicator."""
        if self.interface_mode == 'Pico':
            self.serial_interface.write(b'SONICATOR_OFF\n')
            while self.ser.out_waiting > 0:
                pass
        elif self.interface_mode == 'Hat':
            self.sonicator_enable.value = False


    def _sonicate(self, exposure_time: float = 1.0, power: float = 0.4,
                 pulse_duty_cycle: float = 0.5, pulse_interval: float = 1.0, verbose:bool = False):
        """Enable the sonicator at the power level for the exposure time.
        
        :param exposure_time: total time to sonicate for, defaults to 1.0
        :type exposure_time: float, optional
        :param power: power level to sonicate at, defaults to 0.4
        :type power: float, optional
        :param pulse_duty_cycle: duty cycle of the sonicator pulse, defaults to 0.5
        :type pulse_duty_cycle: float, optional
        :param pulse_interval: interval between pulses, defaults to 1.0
        :type pulse_interval: float, optional
        :param verbose: whether or not to print out the time elapsed, defaults to False
        :type verbose: bool, optional
        """
        # Quick sanity checks
        assert 0 <= power <= 1.0, \
            f"Error: power must be between 0.0 and 1.0. Value specified is: {power}"
        assert 0 <= pulse_duty_cycle <= 1.0, \
            f"Error: pulse_duty_cycle must be between 0.0 and 1.0. Value specified is: {pulse_duty_cycle}"
        assert pulse_interval > 0, \
            f"Error: pulse_interval must be positive. Value specified is: {pulse_interval}."
        assert pulse_interval <= exposure_time, \
            f"Error: pulse_interval cannot exceed exposure time. Value specified is: {pulse_interval}, " \
            f"but total exposure time is {exposure_time}."

        # Set the power level for the sonicator through the DAC.
        self._set_sonication_power(power)
        on_interval = pulse_duty_cycle * pulse_interval
        off_interval = (1 - pulse_duty_cycle) * pulse_interval

        start_time = time.perf_counter()
        stop_time = exposure_time + start_time
        while True:
            # On interval.
            curr_time = time.perf_counter()
            if curr_time + on_interval < stop_time:
                if verbose:
                    print(f"{time.perf_counter() - start_time :.2f} | Sonicator on.")
                else:
                    pass
                self._sonication_on()
                time.sleep(on_interval)
            elif stop_time > curr_time: # last time to sleep.
                if verbose:
                    print(f"{time.perf_counter() - start_time :.2f} | Sonicator on.")
                else:
                    pass
                self._sonication_on()
                time.sleep(stop_time - curr_time)

            # Off interval.
            curr_time = time.perf_counter()
            if curr_time + off_interval < stop_time:
                if verbose:
                    print(f"{time.perf_counter() - start_time :.2f} | Sonicator off.")
                else:
                    pass
                self._sonication_off()
                time.sleep(off_interval)
            elif stop_time > curr_time: # last time to sleep.
                if verbose:
                    print(f"{time.perf_counter() - start_time :.2f} | Sonicator off.")
                else:
                    pass
                self._sonication_off()
                time.sleep(stop_time - curr_time)
                break
            else:
                if verbose:
                    print(f"{time.perf_counter() - start_time :.2f} | Sonicator off.")
                else:
                    pass
                break
        
        print(f"{time.perf_counter() - start_time :.2f} | Finished sonicating.")
        self._sonication_off()
        self._set_sonication_power(0.0)

    @requires_active_tool
    def sonicate_well(self, location:Union[Well, Tuple, Location],
                        plunge_depth: float, sonication_time: float,
                        power: float, pulse_duty_cycle: float, pulse_interval: float,
                        verbose:bool = False, *args):
        """Sonicate one well at a specified depth for a given time.
        
        :param location: location of the well to sonicate
        :type location: Union[Well, Tuple, Location]
        :param plunge_depth: depth (in mm) to plunge from the top of the plate.
        :type plunge_depth: float
        :param sonication_time: time (in sec) to sonicate for
        :type sonication_time: float
        :param power: sonicator power level ranging from 0.4 (default, min) through 1.0 (max).
        :type power: float
        :param pulse_duty_cycle: duty cycle of the sonicator pulse, defaults to 0.5
        :type pulse_duty_cycle: float, optional
        :param pulse_interval: interval between pulses, defaults to 1.0
        :type pulse_interval: float, optional
        :param verbose: whether or not to print out the time elapsed, defaults to False
        :type verbose: bool, optional
        :param args: if location is of type Tuple, the depth of the well needs to be specified  
        :type args: tuple
        :raises ValueError: if the plunge depth is too deep
        
         Note: sonicator does not turn on below power level of 0.4.
        """

        #Check that plunger depth is compatible with labware dimensions
        if type(location) == Well:
            plate_height = location.top_
        elif type(location)==Location:
            plate_height= location[1].top_
        elif type(location) == Tuple:
            try:
                plate_height = args['depth']
            except ValueError:
                print('If location is of type {}, parameter "depth" needs to be indicated'.format(type(location)))        


        plunge_height = plate_height - plunge_depth
        # Sanity check that we're not plunging too deep. Plunge depth is relative.
        
        if plunge_height < 0:
            raise ValueError("Error: plunge depth is too deep.")

        
        x, y, z  = Labware.__getxyz(location)

        self._machine.safe_z_movement()
        self._machine.move_to(x=x,y=y) # Position over the well at safe z height.
        self._machine.move_to(z=plunge_height, wait=True)
        print(f"Sonicating for {sonication_time} seconds!!")
        self._sonicate(sonication_time, power, pulse_duty_cycle, pulse_interval, verbose=verbose)
        print("done!")
        self._machine.safe_z_movement()
   
   
   # TODO: Implement autocleaning
        # if autoclean:
            # self.cleanining_protocol()
 
    # def cleanining_protocol(self, protocol_config: str, paht:str = None):

