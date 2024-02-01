import json
import logging
import os
import time

# this is the Ocean Optics SDK, which is (very unfortunately) not open-source
from oceandirect.OceanDirectAPI import OceanDirectAPI, Spectrometer

from science_jubilee.labware.Labware import Labware, Well, Location
from science_jubilee.tools.Tool import Tool, ToolStateError, ToolConfigurationError, requires_active_tool
from typing import Tuple, Union

import matplotlib.pyplot as plt
import numpy as np


class SpectroscopyTool(OceanDirectAPI, Spectrometer):
    """ A class representation for an Ocean Optics Spectrometer, Light source, and Probe

       For that we wil be unfortunately using their own SDK package, which is NOT
       open-source.  """

    def __init__(self, name, index):
        self.connection = OceanDirectAPI()
        self.spectrometer = self._open_device()
        self.name = name
        self.index = index
        self.current_well = None
        self._dark_spectrum = False
        
    @classmethod
    def from_config(cls, index, name, config_file: str,
                    path :str = os.path.join(os.path.dirname(__file__), 'configs')):
        
        """Initialize the pipette object from a config file

        :param index: The tool index of the spectroscopic probe on the machine
        :type index: int
        :param name: The tool name
        :type name: str
        :param config_file: The name of the config file containign the tool parameters
        :type config_file: str
        :param path: The path to the labware configuration `.json` files for the labware,
                defaults to the 'labware_definition/' in the science_jubilee/labware directory.
        :returns: A :class:`Spectroscopic_tool` object
        :rtype: :class:`Spectroscopic_tool`
        """        
        config = os.path.join(path,config_file)
        with open(config) as f:
            kwargs = json.load(f)

        return cls(index, name, **kwargs) 
    
    @property
    def _api_version(self):
        """ The version of the Ocean Insight SDK """
        (major, minor, point) = self.connection.get_api_version_numbers()
        API_vers=  "%d.%d.%d" % (major, minor, point)
        return API_vers

    @property
    def _usb_device(self):
        devices_found = self.connection.find_usb_devices()
        return devices_found

    @property 
    def _device_id(self):
        """The ID of the spectrometer
        """
        ids= self.connection.get_device_ids()
        return ids
    
    def _open_device(self):
        """ Connects to the spectrometer device """
        devices =[]
        for i in self.device_id:
            dev = self.connection.open_device(i)
            devices.append(dev)

        tot_dev = len(devices)
        if tot_dev == 1:
            self.spectrometer = devices[0]
            return devices[0]
        else:
            print("Careful, more than one (%d) Ocean Insight device is currently"+
                    "connected to this device." % tot_dev)
            return devices

    @property
    def _model(self):
        """The spectrometer model"""
        model = self.spectrometer.get_model()
        return model

    @property
    def _serial_number(self):
        """The spectrometer serial number"""
        sn = self.spectrometer.get_serial_number()
        return sn 
    
    @property
    def _integration_time(self):
       it = self.spectrometer.get_integration_time()
       return it
    
    def integration_time(self,t:float, units:str = 'ms'):
       """Sets the integration time for the spectrometer.
        
        :param t: integration time
        :type t: float
        :param units: units of integration time, defaults to 'ms'
        :type units: str, optional 
        """
       tint_min = self.spectrometer.get_minimum_integration_time()
       tint_max = self.spectrometer.get_maximum_integration_time()
       assert tint_min <= t <= tint_max, \
            'Indicate integration time between %d and %d ms' %(tint_min, tint_max)
       
       self._integration_time_units = units

       # check provided integration time units are supported by the code
       supported_units  = ['us', 'ms', 's']
       assert units in supported_units, \
        'Indicate integration time in one of the supported units: %s, %s, %s' \
           %(supported_units[0], supported_units[1], supported_units[2])
       if units == 'ms':
          time= t*10e3
       elif units == 's':
          time= t*10e6
       else:
          time = t

       self.spectrometer.set_integration_time(time)
       print('The integration time was set to: %d %s' %(time, units))
       
       return 
    
    @property
    def wavelengths(self):
        """Return list containing the wavelengths of the spectrometer.

        :return: A list of wavelengths
        :rtype: list
        """
        wlt = self.spectrometer.wavelenghts
        return wlt

    def scans_to_average(self, n:int):
        """Set the number of scans to average together to compose a single spectrum.
        
        :param n: number of scans to average
        :type n:int

        """           
        self.spectrometer.set_scans_to_average(n)

        return print('The number of scans to average was set to: %d' %n)
    
    def boxcar_width(self, w:int= None):  
        """Unit used to smooth the spectrum.
         
        The boxcar width is the number of adjacent pixels that are averaged together to smooth the spectrum.
        Pixel average = 2* boxcar_width + 1

        :param w: boxcar width
        :type w: int
        """
        if w is not None:
            self.spectrometer.set_boxcar_width(w)
        else:
            w = self.spectrometer.get_boxcar_width()

        print('The boxcar width was set to: %d' %w)
        return 

    def lamp_shutter(self, open=True):
        """Opens or closes light source shutter, if feature is available on light source.)

        :param state: True opens the shutter/False closes it, defaults to False
        :type state: bool, optional
        """
        # need to add a try statement as not all light-sources have a shutter
        try:
            self.spectrometer.Advanced.set_enable_lamp(open)
            print(f"Light shutter was set to {self.device.get_enable_lamp()}")
        except:
            # logging.warning('No light source shutter available')
            print('No such feature on current device')
        return

    def _take_spectrum(self, shutter= 'Open'):
        """Collect a spectrum with the specified experimental parameters"""
        
        if shutter== 'Open' or 'open':
            self.lamp_shutter(open=True)
        else:
            self.lamp_shutter(open=False)

        spectrum = self.spectrometer.get_formatted_spectrum()
        return spectrum

    def dark_spectrum(self, int_time:float, scan_num:int, boxcar_w:int= None,
                      save:bool = False, path:str = None, filename:str = None):
        """Collect a dark spectrum with the specified experimental parameters. 
        
        A dark spectrum is collected when no light is incident on the detector.
        This shuold later be used to correct the actual spectrum for dark counts (i.e. thermal noise). 
        Note: these shuold be the same as the ones used for the actual spectrum.
        
        :param int_time: integration time
        """

        self.integration_time(int_time)
        self.scans_to_average(scan_num)
        self.boxcar_width(boxcar_w)
        self.lamp_shutter(open=False)
        
        dark = self._take_spectrum(shutter='close')

        self._dark_spectrum = True
        self._dark = dark

        if save is True:
            self.save_to_file(dark =True, path=path, filename=filename)

        return dark

    def _collect_raw_spectrum(self,int_time:float, scan_num:int,
                              boxcar_w:int, int_time_units:str ='ms'):
        """Collect a spectrum with the specified experimental parameters
        
        :param int_time: integration time 
        :type int_time: float
        :param scan_num: number of scans to average
        :type scan_num: int
        :param boxcar_w: boxcar width for smoothing the spectrum, defaults to None
        :type boxcar_w: int, optional
        :param int_time_units: units of integration time, defaults to 'ms'
        :type int_time_units: str, optional
        :return: spectrum
        :rtype: numpy array
        """

      
        self.integration_time(int_time, units = int_time_units)
        self.scans_to_average(scan_num)
        self.boxcar_width(boxcar_w)
        
        if self._dark_spectrum is False:
            self.dark_spectrum(int_time, scan_num, boxcar_w)
        else:
            pass

        spectrum = self._take_spectrum(shutter='Open')

        return spectrum

    def collect_spectrum(self, location : Union[Well, Tuple, Location], 
                         int_time, scan_num, boxcar_w,
                         int_time_units ='ms', save:bool = False,
                         filename:str = None, path:str = None):
        """Collect spectrum at the specified location on the labware"""

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
        intensities = self._collect_raw_spectrum(int_time, scan_num, boxcar_w, 
                                   int_time_units= int_time_units)
        
        if save is True:
            self.save_to_file(dark =False, path=path, filename=filename)

        return intensities
    
    def save_to_file(self, dark:bool = False, path:str = None, filename:str = None):
        """ Save the spectrum to a file """

        metadata = {
            "Date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Tool": self.name,
            "Index": self.index,
            "Model": self._model,
            "Serial Number": self._serial_number,
            "API Version": self._api_version,
            "USB Device": self._usb_device,
            "Device ID": self._device_id,
            "Integration Time": self._integration_time
        }
        
        raw_data = {'wavelegth': self.wavelengths,
                    'intensity': self._take_spectrum()}

        if filename is None:
            if dark is True:
                filename = f"dark_spectrum_{time.strftime('%Y%m%d-%H%M%S')}.txt"
            else:
                filename = f"slot{self.current_well.slot}_{self.current_well.name}_spectrum_{time.strftime('%Y%m%d-%H%M%S')}.txt"
        else:
            pass
        # add well location information to metadata as well if not the 'dark' spectrum 
        if dark is not True:
            metadata['Well'] = self.current_well.name
            metadata['Slot'] = self.current_well.slot
            data_handling = MeasurementManager(metadata, raw_data)
            data_handling.generate_file(filename, path)
        
        print(f"Spectrum saved to {path}/{filename}")
        return


class MeasurementManager:
    """ A class to manage the measurements taken by the SpectroscopyTool """

    def __init__(self, metadata, raw_data):
        self.raw_data = raw_data
        self.wavelength = raw_data["wavelength"]
        self.intensity = raw_data["intensity"]
        self.metadata = metadata 

    def pretty_print(self):
        print("---- METADATA ----")
        for key, value in self.metadata.items():
            print(f"{key}: {value}")
        print("\n---- RAW DATA ----")
        print(self.raw_data)

    def generate_file(self, filename, path):
        if not filename.endswith(".txt"):
            filename += ".txt"
        filepath = os.path.join(path, filename)

        with open(filepath, "w") as file:
            # Write metadata section
            file.write("---- METADATA ----\n")
            for key, value in self.metadata.items():
                file.write(f"{key}: {value}\n")
            file.write("\n")

            # Write raw data section
            file.write("---- RAW DATA ----\n")
            for wavelength, intensity in zip(self.wavelengths, self.intensities):
                file.write(f"{wavelength}\t{intensity}\n")
    
    def read_file(filepath):
        metadata = {}
        measurements = []

        with open(filepath, "r") as file:
            section = None
            for line in file:
                line = line.strip()
                if line.startswith("---- METADATA ----"):
                    section = "metadata"
                elif line.startswith("---- RAW DATA ----"):
                    section = "raw_data"
                elif section == "metadata":
                    key, value = line.split(": ")
                    metadata[key] = value
                elif section == "raw_data":
                    wavelength, intensity = line.split("\t")
                    measurements.append((float(wavelength), float(intensity)))

        return metadata, measurements