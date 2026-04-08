"""JSON-RPC serial communication for microcontroller-based tools.

Adapted from the bioreactor project's Module class. Provides a reusable
interface for any tool that communicates with firmware over USB serial
using the JSON-RPC 2.0 protocol.
"""

import json
import time
from typing import Any, Dict, List, Optional

import serial
from serial.tools import list_ports


class SerialDevice:
    """Represents a serial device running JSON-RPC firmware.

    Handles connection, capability discovery, and command dispatch.
    """

    def __init__(self, port: serial.Serial, timeout: float = 5.0):
        """Initialize with an already-opened serial port.

        Waits for firmware to boot, then auto-discovers capabilities.

        :param port: An open serial.Serial object
        :type port: serial.Serial
        :param timeout: Seconds to wait for command responses, defaults to 5.0
        :type timeout: float, optional
        """
        self.port = port
        self.timeout = timeout

        # Discovered from firmware
        self.module_name = "unknown"
        self.firmware_version = "unknown"
        self.capabilities = {}
        self.available_commands = []
        self.available_actuators = []
        self.available_sensors = []

        # Wait for firmware to finish booting, then discover
        self._wait_for_ready()
        self._discover()

    def _wait_for_ready(self):
        """Wait for firmware to finish booting by draining startup output."""
        time.sleep(2)
        while self.port.in_waiting > 0:
            self.port.readline()
            time.sleep(0.1)

    def _discover(self):
        """Query firmware for capabilities and store them."""
        result = self.send_command("get_capabilities")

        if result.get("success"):
            caps = result.get("capabilities", {})
            self.capabilities = caps

            meta = caps.get("metadata", {})
            self.module_name = meta.get("module_name", "unknown")
            self.firmware_version = meta.get("firmware_version", "unknown")

            self.available_commands = list(caps.get("commands", {}).keys())
            self.available_actuators = list(caps.get("actuators", {}).keys())
            self.available_sensors = list(caps.get("sensors", {}).keys())

    def send_command(self, command: str, params: Dict = None) -> Dict[str, Any]:
        """Send a JSON-RPC command and return the result.

        :param command: Command name (e.g. ``"read_sensor"``, ``"blink"``)
        :type command: str
        :param params: Command parameters, defaults to None
        :type params: Dict, optional
        :return: Result dict from firmware (always contains ``"success"`` key)
        :rtype: Dict[str, Any]
        """
        if not self.port or not self.port.is_open:
            return {"success": False, "error": "Device not connected"}

        params = params or {}

        try:
            request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": command,
                "params": params,
            }

            cmd_bytes = (json.dumps(request) + "\n").encode("utf-8")
            self.port.reset_output_buffer()
            self.port.reset_input_buffer()
            self.port.write(cmd_bytes)

            # Read response, skipping any non-JSON lines (boot output)
            start = time.time()
            while time.time() - start < self.timeout:
                if self.port.in_waiting > 0:
                    line = self.port.readline().decode("utf-8").strip()
                    if line.startswith("{"):
                        response = json.loads(line)

                        if "error" in response:
                            return {
                                "success": False,
                                "error": response["error"].get(
                                    "message", "Unknown error"
                                ),
                            }

                        return response.get("result", {})
                time.sleep(0.01)

            return {"success": False, "error": f"Timeout after {self.timeout}s"}

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def is_connected(self) -> bool:
        """Check if the device is connected."""
        return self.port is not None and self.port.is_open

    def disconnect(self):
        """Close the serial connection."""
        if self.port:
            self.port.close()
            self.port = None

    @staticmethod
    def find_ports(manufacturers: List[str] = None) -> List:
        """Find serial ports matching the given manufacturer names.

        :param manufacturers: Manufacturer strings to match (e.g. ``["Seeed", "Espressif"]``).
            Defaults to ``["Seeed", "Espressif"]``.
        :type manufacturers: List[str], optional
        :return: List of matching serial port info objects
        :rtype: List
        """
        if manufacturers is None:
            manufacturers = ["Seeed", "Espressif"]

        all_ports = list_ports.comports()
        return [
            p
            for p in all_ports
            if p.manufacturer
            and any(mfr in str(p.manufacturer) for mfr in manufacturers)
        ]

    def __repr__(self):
        port_name = self.port.port if self.port else "disconnected"
        return (
            f"SerialDevice(name='{self.module_name}', "
            f"fw='{self.firmware_version}', port='{port_name}')"
        )
