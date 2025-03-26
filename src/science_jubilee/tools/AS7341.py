import json
import os
import time
import warnings
import serial
from serial.tools import list_ports

from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Union, Dict, Any, List, Optional

class AS7341(Tool):
    """A class representation of the AS7341 spectral sensor.

    :param Tool: The base tool class
    :type Tool: :class:`Tool`
    """
    def __init__(self, index, name, config):
        """Constructor method
        """
        super().__init__(index, name)
        
        self.lineEnding = '\n\r'
        self.baudrate = 115200
        self.sensor_config = None
        self.serial_port = None
        
        self.load_config(config)
        
    def load_config(self, config):
        """Loads the configuration file for the AS7341 sensor tool
        """
        
        config_directory = os.path.join(os.path.dirname(__file__), "configs")
        config_path = os.path.join(config_directory, f"{config}.json")
        if not os.path.isfile(config_path):
            raise ToolConfigurationError(
                f"Error: Config file {config_path} does not exist!"
            )

        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Store the configuration
        self.sensor_config = config
        
        # Check that all necessary information was provided
        if self.sensor_config is None:
            raise ToolConfigurationError(
                "Error: Not enough information provided in configuration file."
            )
    
    def find_seeed(self) -> List[serial.Serial]:
        """Find all Seeed Studio or Espressif devices connected to the system
        
        :return: List of serial ports for connected Seeed devices
        :rtype: List[serial.Serial]
        :raises IOError: If no Seeed devices are found
        """
        # returns com ports
        all_ports = [
            p
            for p in list_ports.comports()
            if p.manufacturer is not None  # may need tweaking to match new arduinos
        ]
        
        seeed_ports = [
            p.device 
            for p in all_ports 
            if 'Seeed' in p.manufacturer or 'Espressif' in p.manufacturer
        ]
        
        # Check if any Seeed devices were found
        if not seeed_ports:
            raise IOError("No Seeed found")
            
        if len(seeed_ports) > 1:
            warnings.warn(f"Multiple Seeeds found - returning {len(seeed_ports)} ports")
            
        # Create Serial objects for each port
        ser_list = [serial.Serial(port, self.baudrate, timeout=1) for port in seeed_ports]
        
        # Return Serial objects
        return ser_list
    
    def connect_seeed(self, ser_port_index: int = 0) -> serial.Serial:
        """Connect to a Seeed device at the specified port index
        
        :param ser_port_index: Index of the serial port to connect to, defaults to 0
        :type ser_port_index: int, optional
        :return: Connected serial port
        :rtype: serial.Serial
        """
        # Find all available Seeed devices
        seeed_devices = self.find_seeed()
        
        # Check if the requested index exists
        if ser_port_index >= len(seeed_devices):
            raise IndexError(f"Serial port index {ser_port_index} out of range. Only {len(seeed_devices)} ports available.")
        
        # Connect to the specified port
        ser_port = seeed_devices[ser_port_index].port
        self.serial_port = serial.Serial(ser_port, self.baudrate, timeout=1)
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()
        
        # Update the configuration to save the connection
        if self.sensor_config:
            self.sensor_config['port'] = ser_port
            # Save the updated configuration
            config_directory = os.path.join(os.path.dirname(__file__), "configs")
            config_path = os.path.join(config_directory, f"{self.sensor_config.get('name', 'as7341')}.json")
            with open(config_path, "w") as f:
                json.dump(self.sensor_config, f, indent=2)
                
        return self.serial_port
    
    def disconnect_seeed(self) -> bool:
        """Disconnect from the currently connected Seeed device
        
        :return: True if disconnection was successful
        :rtype: bool
        """
        if self.serial_port is None:
            warnings.warn("No connected Seeed device to disconnect")
            return False
            
        try:
            self.serial_port.close()
            self.serial_port = None
            
            # Update the configuration to remove the connection
            if self.sensor_config:
                self.sensor_config['port'] = ""
                # Save the updated configuration
                config_directory = os.path.join(os.path.dirname(__file__), "configs")
                config_path = os.path.join(config_directory, f"{self.sensor_config.get('name', 'as7341')}.json")
                with open(config_path, "w") as f:
                    json.dump(self.sensor_config, f, indent=2)
                    
            return True
            
        except Exception as e:
            warnings.warn(f"Error disconnecting from Seeed device: {e}")
            return False
    
    def blink(self, cmd: Union[int, str]) -> None:
        """Send a blink command to the connected Seeed device
        
        :param cmd: The blink command parameter
        :type cmd: Union[int, str]
        :raises ToolStateError: If no serial port is connected
        """
        if self.serial_port is None:
            raise ToolStateError("No serial port connected. Call connect_seeed() first.")
            
        cmd_str = f'blink,{cmd}'
        cmd_str += self.lineEnding
        bcmd = cmd_str.encode()
        
        self.serial_port.write(bcmd)
    
    def measure_spectrum(self, duty_cycle: int = 100) -> Dict[str, Any]:
        """Measure the spectral values from the AS7341 sensor
        
        :param duty_cycle: The duty cycle for the measurement (0-100), defaults to 100
        :type duty_cycle: int, optional
        :return: Dictionary containing the spectral readings from different channels
        :rtype: Dict[str, Any]
        :raises ToolStateError: If no serial port is connected
        :raises ValueError: If duty cycle is out of range
        """
        # Validate duty cycle value
        if not (0 <= duty_cycle <= 100):
            raise ValueError("Duty cycle must be between 0 and 100")
        
        # Check if serial port is connected
        if self.serial_port is None:
            raise ToolStateError("No serial port connected. Call connect_seeed() first.")
        
        # Format the command with duty cycle
        cmd = f'spec,{duty_cycle}'
        cmd += self.lineEnding
        bcmd = cmd.encode()
        
        # Clear buffers
        self.serial_port.reset_output_buffer()
        self.serial_port.reset_input_buffer()
        
        # Send command to the sensor
        self.serial_port.write(bcmd)
        
        # Wait for the sensor to complete measurement
        time.sleep(1.1)
        
        # Read the response
        spec_reading = self.serial_port.readline().strip().decode()
        
        # Parse the reading into a dictionary
        try:
            readings = {}
            values = spec_reading.split()
            
            # Handle different possible response formats
            if ':' in spec_reading:
                # Format like "415nm:123 445nm:456 ..."
                for value in values:
                    channel, reading = value.split(':')
                    readings[channel] = float(reading)
            else:
                # Format like "123 456 789 ..." (raw values in expected order)
                channels = ["415nm", "445nm", "480nm", "515nm", "555nm", "590nm", "630nm", "680nm", "Clear", "NIR"]
                numeric_values = [float(v) for v in values]
                
                # Match channels with values (handle case where lengths don't match)
                for i, channel in enumerate(channels):
                    if i < len(numeric_values):
                        readings[channel] = numeric_values[i]
            
            return readings
            
        except Exception as e:
            raise ToolStateError(f"Error parsing spectral data: {e}. Raw reading: {spec_reading}")
    
    def get_raw_spectrum(self, duty_cycle: int = 100) -> str:
        """Get the raw spectral data string from the AS7341 sensor
        
        :param duty_cycle: The duty cycle for the measurement (0-100), defaults to 100
        :type duty_cycle: int, optional
        :return: Raw string output from the sensor
        :rtype: str
        :raises ToolStateError: If no serial port is connected
        """
        # Validate duty cycle value
        if not (0 <= duty_cycle <= 100):
            raise ValueError("Duty cycle must be between 0 and 100")
        
        # Check if serial port is connected
        if self.serial_port is None:
            raise ToolStateError("No serial port connected. Call connect_seeed() first.")
        
        # Format the command with duty cycle
        cmd = f'spec,{duty_cycle}'
        cmd += self.lineEnding
        bcmd = cmd.encode()
        
        # Clear buffers
        self.serial_port.reset_output_buffer()
        self.serial_port.reset_input_buffer()
        
        # Send command to the sensor
        self.serial_port.write(bcmd)
        
        # Wait for the sensor to complete measurement
        time.sleep(1.1)
        
        # Read and return the raw response
        return self.serial_port.readline().strip().decode()