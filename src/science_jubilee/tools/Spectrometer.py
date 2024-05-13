import json
import logging
import os
from datetime import date
from typing import Tuple, Union

import matplotlib.pyplot as plt
import numpy as np

# this is the Ocean Optics SDK, which is (very unfortunately) not open-source
try:
    from oceandirect.OceanDirectAPI import OceanDirectAPI
except ImportError:
    raise ImportError(
        "The Ocean Optics SDK is not installed. Please install it from the Ocean Insight website."
    )

from science_jubilee.labware.Labware import Labware, Location, Well
from science_jubilee.tools.Tool import Tool, requires_active_tool


class SpectroscopyTool(Tool, OceanDirectAPI):
    """A class representation for an Ocean Optics Spectrometer, Light source, and Probe

    For that we wil be unfortunately using their own SDK package, which is NOT
    open-source."""

    def __init__(self, index, name):
        self.connection = OceanDirectAPI()
        self.spectrometer = self._open_device()
        self.name = name
        self.index = index
        self.current_well = None
        self._dark_spectrum = False
        self.reference_spectrum = None

    @property
    def _api_version(self):
        """The version of the Ocean Insight SDK"""
        (major, minor, point) = self.connection.get_api_version_numbers()
        API_vers = "%d.%d.%d" % (major, minor, point)
        return API_vers

    @property
    def _usb_device(self):
        devices_found = self.connection.find_usb_devices()
        return devices_found

    @property
    def _device_id(self):
        """The ID of the spectrometer"""
        usb = self._usb_device
        ids = self.connection.get_device_ids()
        return ids

    def _open_device(self):
        """Connects to the spectrometer device"""
        devices = []
        idx = self._device_id
        for i in idx:
            dev = self.connection.open_device(i)
            devices.append(dev)

        tot_dev = len(devices)
        if tot_dev == 1:
            self.spectrometer = devices[0]
            return devices[0]
        else:
            print(
                "Careful, more than one (%d) Ocean Insight device is currently"
                + "connected to this device." % tot_dev
            )
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

    def integration_time(self, t: float, units: str = "ms"):
        """Sets the integration time for the spectrometer.

        :param t: integration time
        :type t: float
        :param units: units of integration time, defaults to 'ms'
        :type units: str, optional
        """
        self._integration_time_units = units

        # check provided integration time units are supported by the code
        supported_units = ["us", "ms", "s"]
        assert (
            units in supported_units
        ), "Indicate integration time in one of the supported units: %s, %s, %s" % (
            supported_units[0],
            supported_units[1],
            supported_units[2],
        )
        if units == "ms":
            time = t * 10e3
        elif units == "s":
            time = t * 10e6
        else:
            time = t

        tint_min = self.spectrometer.get_minimum_integration_time()
        tint_max = self.spectrometer.get_maximum_integration_time()
        assert (
            tint_min <= time <= tint_max
        ), "Indicate integration time between %d and %d ms" % (tint_min, tint_max)

        time = int(time)

        self.spectrometer.set_integration_time(time)
        print("The integration time was set to: %d %s" % (time, units))

        return

    @property
    def wavelengths(self):
        """Return list containing the wavelengths of the spectrometer.

        :return: A list of wavelengths
        :rtype: list
        """
        wlt = self.spectrometer.wavelengths
        return wlt

    def scans_to_average(self, n: int):
        """Set the number of scans to average together to compose a single spectrum.

        :param n: number of scans to average
        :type n:int

        """
        self.spectrometer.set_scans_to_average(n)

        return print("The number of scans to average was set to: %d" % n)

    def boxcar_width(self, w: int = None):
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

        print("The boxcar width was set to: %d" % w)
        return

    def lamp_shutter(self, open=True):
        """Opens or closes light source shutter, if feature is available on light source.)

        :param open: True opens the shutter/False closes it, defaults to False
        :type state: bool, optional
        """
        # need to add a try statement as not all light-sources have a shutter
        if open == True:
            state = "Open"
        else:
            state = "Close"

        self.spectrometer.Advanced.set_enable_lamp(open)

        if self.spectrometer.Advanced.get_enable_lamp() == open:
            print(f"Light shutter was set to {state}")
        else:
            print("No such feature on current device")
        # except:
        #     # logging.warning('No light source shutter available')
        #     print('No such feature on current device')
        return

    def _take_spectrum(self, open=True):
        """Collect a spectrum with the specified experimental parameters"""

        self.lamp_shutter(open=open)

        spectrum = self.spectrometer.get_formatted_spectrum()

        return spectrum

    def dark_spectrum(
        self,
        int_time: float,
        scan_num: int,
        boxcar_w: int = None,
        save: bool = False,
        path: str = None,
        filename: str = None,
    ):
        """Collect a dark spectrum with the specified experimental parameters.

        A dark spectrum is collected when no light is incident on the detector.
        This shuold later be used to correct the actual spectrum for dark counts (i.e. thermal noise).
        Note: these shuold be the same as the ones used for the actual spectrum.

        :param int_time: integration time
        """

        self.integration_time(int_time)
        self.scans_to_average(scan_num)
        self.boxcar_width(boxcar_w)

        dark = self._take_spectrum(open=False)

        self._dark_spectrum = True
        self._dark = dark

        if save is True:
            self.save_to_file(dark, dark=True, path=path, filename=filename)

        return dark

    def _collect_raw_spectrum(
        self, int_time: float, scan_num: int, boxcar_w: int, int_time_units: str = "ms"
    ):
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

        self.integration_time(int_time, units=int_time_units)
        self.scans_to_average(scan_num)
        self.boxcar_width(boxcar_w)

        if self._dark_spectrum is False:
            self.dark_spectrum(int_time, scan_num, boxcar_w)
        else:
            pass

        spectrum = self._take_spectrum(open=True)

        return spectrum

    @requires_active_tool
    def collect_spectrum(
        self,
        location: Union[Well, Tuple, Location],
        int_time,
        scan_num,
        boxcar_w,
        int_time_units="ms",
        save: bool = False,
        filename: str = None,
        path: str = None,
    ):
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
        intensities = self._collect_raw_spectrum(
            int_time, scan_num, boxcar_w, int_time_units=int_time_units
        )

        if save is True:
            self.save_to_file(intensities, dark=False, path=path, filename=filename)

        return intensities

    def save_to_file(
        self, data, dark: bool = False, path: str = None, filename: str = None
    ):
        """Save the spectrum to a file"""

        metadata = {
            "Date": date.today().strftime("%Y%m%d"),
            "Tool": self.name,
            "Index": self.index,
            "Model": self._model,
            "Serial Number": self._serial_number,
            "API Version": self._api_version,
            "USB Device": self._usb_device,
            "Device ID": self._device_id,
            "Integration Time": self._integration_time,
        }

        raw_data = {"wavelength": self.wavelengths, "intensity": data}

        if filename is None:
            if dark is True:
                filename = f"dark_spectrum_{metadata['Date']}.txt"
            else:
                filename = f"slot{self.current_well.slot}_{self.current_well.name}_spectrum_{metadata['Date']}.txt"
        else:
            pass

        if path is None:
            path = "./"
        else:
            pass
        # add well location information to metadata as well if not the 'dark' spectrum
        if dark is not True:
            metadata["Well"] = self.current_well.name
            metadata["Slot"] = self.current_well.slot
            data_handling = MeasurementManager(metadata, raw_data)
            data_handling.generate_file(filename, path)

        print(f"Spectrum saved to {path}/{filename}")
        return

    def read_from_file(self, filepath, scale=True, reference_spectrum=None):

        metadata, measurements = MeasurementManager.read_file(filepath)

        if scale == True:
            if reference_spectrum == None and self.reference_spectrum == None:
                print("Reference spectrum must be provided for scaling.")
                return
            elif reference_spectrum == None and self.reference_spectrum != None:
                reference_spectrum = self.reference_spectrum
            else:
                pass
            measurements["Intensity"] = self.scale_intensity(
                measurements["Intensity"], reference_spectrum
            )
        return metadata, measurements

    @staticmethod
    def scale_intensity(data: list, reference_spectrum: list):

        assert len(data) == len(
            reference_spectrum
        ), "Data and reference spectrum must be of same size"
        scaled_intensities = [d / r for d, r in zip(data, reference_spectrum)]

        return scaled_intensities


class MeasurementManager:
    """A class to manage the measurements taken by the SpectroscopyTool"""

    def __init__(self, metadata, raw_data):
        self.raw_data = raw_data
        self.wavelengths = raw_data["wavelength"]
        self.intensities = raw_data["intensity"]
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

            # Write raw data section
            file.write("---- RAW DATA ----\n")
            for wavelength, intensity in zip(self.wavelengths, self.intensities):
                file.write(f"{wavelength}\t{intensity}\n")

    def read_file(filepath):
        metadata = {}
        measurements = {"Wavelength": [], "Intensity": []}

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
                    measurements["Wavelength"].append(float(wavelength))
                    measurements["Intensity"].append(float(intensity))

        return metadata, measurements
