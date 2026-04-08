"""AS7341 spectral sensor tool.

Communicates with an XIAO ESP32S3 running JSON-RPC firmware over USB serial.
Mirrors the CircuitPython ``adafruit_as7341`` API — property access is
transparently proxied to the firmware via JSON-RPC.

Example::

    spec = AS7341(index=0, name="AS7341", config="AS7341")
    spec.connect()
    spec.led_current = 50
    spec.led = True
    print(spec.all_channels)
    spec.led = False
"""

import json
import os
import warnings
from typing import Dict, List, Optional

import serial

from science_jubilee.tools.Tool import (
    Tool,
    ToolConfigurationError,
    ToolStateError,
)
from science_jubilee.utils.SerialDevice import SerialDevice

from science_jubilee.tools import _CONFIGS_DIR, _find_config

# Attributes that belong to the AS7341/Tool instance, NOT the remote sensor.
# These are handled by normal Python attribute access.
_LOCAL_ATTRS = frozenset({
    "device", "sensor_config", "_config_path", "baudrate",
    "_machine", "index", "name", "is_active_tool", "tool_offset",
})


class AS7341(Tool):
    """AS7341 spectral sensor with transparent property proxy.

    After calling :meth:`connect`, any attribute access that isn't a local
    attribute is forwarded to the remote sensor via JSON-RPC ``get_property``
    / ``set_property`` commands.  This mirrors the CircuitPython
    ``adafruit_as7341.AS7341`` API.
    """

    def __init__(self, index, name, config):
        super().__init__(index, name)
        self.baudrate = 115200
        self.sensor_config = None
        self.device = None
        self.load_config(config)

    def load_config(self, config):
        config_path = _find_config(f"{config}.json")
        if not os.path.isfile(config_path):
            raise ToolConfigurationError(
                f"Error: Config file {config_path} does not exist!"
            )
        with open(config_path, "r") as f:
            self.sensor_config = json.load(f)
        self._config_path = config_path

    # -- Property proxy --------------------------------------------------------

    def __getattr__(self, name):
        # __getattr__ is only called when normal lookup fails.
        # If device is connected, proxy to firmware.
        device = object.__getattribute__(self, "__dict__").get("device")
        if device is not None and device.is_connected():
            result = device.send_command(
                "get_property", {"sensor": "as7341", "property": name}
            )
            if result.get("success"):
                return result["value"]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Local attrs, private attrs, and init-time attrs bypass the proxy.
        if (
            name in _LOCAL_ATTRS
            or name.startswith("_")
            or "device" not in self.__dict__
            or self.__dict__.get("device") is None
        ):
            super().__setattr__(name, value)
        else:
            device = self.__dict__["device"]
            if device.is_connected():
                result = device.send_command(
                    "set_property",
                    {"sensor": "as7341", "property": name, "value": value},
                )
                if not result.get("success"):
                    raise AttributeError(
                        f"Failed to set '{name}': {result.get('error')}"
                    )
            else:
                super().__setattr__(name, value)

    # -- Connection ------------------------------------------------------------

    def connect(self, port_index: int = 0) -> SerialDevice:
        """Find and connect to the sensor board.

        :param port_index: Index of the serial port if multiple are found
        :type port_index: int, optional
        :return: The connected SerialDevice
        :rtype: SerialDevice
        """
        ports = SerialDevice.find_ports(["Seeed", "Espressif"])

        if not ports:
            raise IOError("No Seeed/Espressif devices found.")
        if port_index >= len(ports):
            raise IndexError(
                f"Port index {port_index} out of range. "
                f"Only {len(ports)} devices found."
            )
        if len(ports) > 1:
            warnings.warn(
                f"Multiple devices found — connecting to index {port_index}"
            )

        port_name = ports[port_index].device
        ser = serial.Serial(port_name, self.baudrate, timeout=2)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        self.device = SerialDevice(ser)

        # Save port to config
        if self.sensor_config:
            self.sensor_config["port"] = port_name
            save_path = self._config_path
            if os.path.join(_CONFIGS_DIR, "examples") in save_path:
                save_path = os.path.join(
                    _CONFIGS_DIR, "user", os.path.basename(save_path)
                )
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(self.sensor_config, f, indent=2)
            self._config_path = save_path

        print(f"Connected: {self.device}")
        return self.device

    def disconnect(self):
        """Disconnect from the sensor board."""
        if self.device is None:
            warnings.warn("No device connected.")
            return

        self.device.disconnect()
        self.device = None

        if self.sensor_config:
            self.sensor_config["port"] = ""
            with open(self._config_path, "w") as f:
                json.dump(self.sensor_config, f, indent=2)

    @property
    def capabilities(self) -> Dict:
        """Return discovered capabilities from the firmware."""
        if self.device is None:
            return {}
        return self.device.capabilities

    # -- Explicit methods (not part of CircuitPython API) ----------------------

    def blink(self, duration: float = 0.5):
        """Blink the XIAO onboard LED.

        :param duration: Blink duration in seconds, defaults to 0.5
        :type duration: float, optional
        """
        if self.device is None or not self.device.is_connected():
            raise ToolStateError("Not connected. Call connect() first.")
        result = self.device.send_command("blink", {"duration": duration})
        if not result.get("success"):
            raise ToolStateError(f"Blink failed: {result.get('error')}")
