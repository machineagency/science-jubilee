"""
Connects to an XIAO ESP32S3 over USB serial,
discovers all registered hardware via JSON-RPC get_capabilities, and loads
host-side driver files that attach typed methods for every available sensor
and actuator — mirroring the firmware's own driver-registration pattern.

Typical usage::

    available = SensorModule.scan()
    # {0: '/dev/cu.usbmodem1101'}

    sensor = SensorModule(index=0, name="sensor_0")
    sensor.connect()
    # After connect(), typed methods are available:
    #   sensor.blink(), sensor.set_led(), sensor.set_motor(), sensor.pump(),
    #   sensor.stop_motor(), sensor.read(), sensor.read_as7341(), ...

    m = Machine(address="192.168.1.2")
    m.load_tool(sensor)
    m.pickup_tool(sensor)

    readings = sensor.read_as7341(duty_cycle=50)
    sensor.disconnect()
"""

import importlib
import json
import logging
import time
import warnings
from typing import Any, Dict, List, Optional

import serial
from serial.tools import list_ports

from science_jubilee.tools.Tool import Tool, ToolStateError

logger = logging.getLogger(__name__)

# Seconds to wait after opening port before draining boot messages
_BOOT_WAIT = 2.0
# Seconds between polling in_waiting in the timeout loop
_POLL_INTERVAL = 0.01

# Ordered list of host-side driver modules — mirrors firmware/boot.py DRIVERS
DRIVERS = [
    "onboard_led",
    "blue_led",
    "dc_motors",
    "i2c_sensors",
]


class SensorModule(Tool):
    """Interface to a bioreactor firmware module (XIAO ESP32S3) as a Jubilee Tool.

    Connects over USB serial, discovers all registered hardware via
    get_capabilities, and loads host-side driver files that attach typed
    methods for every available sensor and actuator.

    :param Tool: The base science-jubilee Tool class.
    :type Tool: :class:`Tool`
    """

    TIMEOUT = 5.0  # seconds to wait for a JSON-RPC response

    def __init__(self, index: int, name: str) -> None:
        """Initialize SensorModule.

        :param index: Jubilee tool slot index (T0, T1, ...). By convention,
            this should match the firmware MODULE_ID.
        :param name: Human-readable tool name.
        """
        super().__init__(index, name)

        self.baudrate: int = 115200
        self._port: Optional[serial.Serial] = None

        # Populated by _discover() after connect()
        self.module_id: Optional[int] = None
        self.module_name: str = "unknown"
        self.firmware_version: str = "unknown"
        self.hardware_id: str = "unknown"
        self.capabilities: Dict[str, Any] = {}
        self.available_commands: List[str] = []
        self.available_actuators: Dict[str, Dict] = {}
        self.available_sensors: Dict[str, Dict] = {}

    # -------------------------------------------------------------------------
    # Discovery
    # -------------------------------------------------------------------------

    @classmethod
    def scan(cls) -> Dict[int, str]:
        """Find all connected XIAO ESP32S3 modules and return their IDs.

        Opens each compatible serial port briefly, sends get_capabilities,
        reads the firmware module_id, and closes. Safe to call at any time.

        :return: Dict mapping firmware module_id -> serial port path,
            e.g. ``{0: '/dev/cu.usbmodem1101', 1: '/dev/cu.usbmodem1201'}``.
        :rtype: Dict[int, str]
        """
        all_ports = list_ports.comports()
        candidates = [
            p for p in all_ports
            if p.manufacturer and any(
                mfr in str(p.manufacturer)
                for mfr in ("Seeed", "Espressif")
            )
        ]

        if not candidates:
            logger.warning("scan(): no Seeed/Espressif devices found")
            logger.debug("All ports: %s", [p.device for p in all_ports])
            return {}

        found: Dict[int, str] = {}

        for port_info in candidates:
            port_path = port_info.device
            ser = None
            try:
                ser = serial.Serial(port_path, 115200, timeout=2)
                ser.reset_input_buffer()
                ser.reset_output_buffer()

                time.sleep(_BOOT_WAIT)
                while ser.in_waiting > 0:
                    ser.readline()
                    time.sleep(0.05)

                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "get_capabilities",
                    "params": {},
                }
                ser.write((json.dumps(request) + "\n").encode("utf-8"))

                start = time.time()
                module_id = None
                while time.time() - start < cls.TIMEOUT:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode("utf-8", errors="replace").strip()
                        if line.startswith("{"):
                            try:
                                response = json.loads(line)
                                caps = response.get("result", {}).get("capabilities", {})
                                module_id = caps.get("metadata", {}).get("module_id")
                            except json.JSONDecodeError:
                                pass
                            break
                    time.sleep(_POLL_INTERVAL)

                if module_id is not None:
                    found[module_id] = port_path
                    logger.info("scan(): module_id=%d at %s", module_id, port_path)
                else:
                    logger.warning("scan(): %s did not report module_id", port_path)

            except Exception as e:
                logger.warning("scan(): failed to probe %s: %s", port_path, e)
            finally:
                if ser is not None:
                    try:
                        ser.close()
                    except Exception:
                        pass

        return found

    # -------------------------------------------------------------------------
    # Connection management
    # -------------------------------------------------------------------------

    def connect(self, port: Optional[str] = None) -> None:
        """Connect to the XIAO module, discover capabilities, and load drivers.

        If ``port`` is None, calls :meth:`scan` and connects to the device
        whose firmware module_id matches ``self.index``. If ``port`` is given
        explicitly, connects directly without checking module_id alignment
        (useful for development when MODULE_ID has not been set yet).

        :param port: Explicit serial port path, or None to auto-discover.
        :type port: str, optional
        :raises IOError: If no compatible devices are found, or no device with
            a module_id matching ``self.index`` is found during auto-discovery.
        :raises ToolStateError: If capability discovery fails.
        """
        if port is None:
            available = self.__class__.scan()
            if not available:
                raise IOError(
                    "connect(): no XIAO modules found on any serial port. "
                    "Check USB connection and driver installation."
                )
            if self.index not in available:
                raise IOError(
                    f"connect(): no module with module_id={self.index} found. "
                    f"Available module_ids: {list(available.keys())}. "
                    f"Check MODULE_ID in firmware/boot.py."
                )
            port = available[self.index]
            logger.info(
                "connect(): auto-selected %s for index=%d", port, self.index
            )
        else:
            logger.info("connect(): using explicit port %s", port)

        self._port = serial.Serial(port, self.baudrate, timeout=2)
        self._port.reset_input_buffer()
        self._port.reset_output_buffer()

        time.sleep(_BOOT_WAIT)
        while self._port.in_waiting > 0:
            self._port.readline()
            time.sleep(0.05)

        self._discover()

        logger.info(
            "connect(): %s (id=%s, fw=%s) ready",
            self.module_name, self.module_id, self.firmware_version,
        )

    def disconnect(self) -> None:
        """Stop all motors (best-effort) and close the serial port."""
        if self._port is None:
            warnings.warn("disconnect(): no device is connected")
            return

        if "stop_motor" in self.available_commands:
            try:
                self.send_command("stop_motor", {"motor": "all"})
            except Exception:
                pass

        try:
            self._port.close()
        except Exception as e:
            warnings.warn(f"disconnect(): error closing port: {e}")
        finally:
            self._port = None

    def is_connected(self) -> bool:
        """Return True if the serial port is open."""
        return self._port is not None and self._port.is_open

    def post_load(self) -> None:
        """Called by Machine.load_tool() after associating this tool with the machine.

        Logs a reminder if the module is not yet connected, since
        :meth:`connect` must be called before :meth:`pickup_tool`.
        """
        if not self.is_connected():
            logger.warning(
                "post_load(): SensorModule '%s' loaded but not yet connected. "
                "Call sensor.connect() before m.pickup_tool(sensor).",
                self.name,
            )

    # -------------------------------------------------------------------------
    # Capability discovery and driver loading
    # -------------------------------------------------------------------------

    def _discover(self) -> None:
        """Query firmware capabilities and load host-side drivers.

        Populates module_id, module_name, firmware_version, hardware_id,
        available_commands, available_actuators, and available_sensors.
        Then calls _load_drivers().

        :raises ToolStateError: If get_capabilities fails or times out.
        """
        result = self.send_command("get_capabilities")

        if not result.get("success"):
            raise ToolStateError(
                f"_discover(): get_capabilities failed: {result.get('error')}"
            )

        caps = result.get("capabilities", {})
        self.capabilities = caps

        meta = caps.get("metadata", {})
        self.module_id = meta.get("module_id")
        self.module_name = meta.get("module_name", "unknown")
        self.firmware_version = meta.get("firmware_version", "unknown")
        self.hardware_id = meta.get("board_id", "unknown")

        self.available_commands = list(caps.get("commands", {}).keys())
        self.available_actuators = caps.get("actuators", {})
        self.available_sensors = caps.get("sensors", {})

        logger.info("_discover(): commands=%s", self.available_commands)
        logger.info(
            "_discover(): actuators=%s", list(self.available_actuators.keys())
        )
        logger.info(
            "_discover(): sensors=%s", list(self.available_sensors.keys())
        )

        self._load_drivers()

    def _load_drivers(self) -> None:
        """Load host-side driver modules and call register(self) on each.

        Iterates the DRIVERS list and imports each from
        ``science_jubilee.tools.drivers.<name>``. Each driver's
        ``register(module)`` inspects available capabilities and attaches
        only the methods that the firmware actually supports.

        Driver failures are logged as warnings; a broken driver does not
        prevent other drivers from loading.
        """
        for driver_name in DRIVERS:
            module_path = f"science_jubilee.tools.drivers.{driver_name}"
            try:
                driver_module = importlib.import_module(module_path)
                driver_module.register(self)
                logger.debug("_load_drivers(): loaded %s", driver_name)
            except ImportError as e:
                logger.warning(
                    "_load_drivers(): could not import %s: %s", driver_name, e
                )
            except Exception as e:
                logger.warning(
                    "_load_drivers(): %s.register() raised %s: %s",
                    driver_name, type(e).__name__, e,
                )

    # -------------------------------------------------------------------------
    # JSON-RPC transport
    # -------------------------------------------------------------------------

    def send_command(
        self, command: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send a JSON-RPC command and return the result dict.

        Uses a polling timeout loop that skips non-JSON lines (firmware boot
        output, debug prints). Waits up to TIMEOUT seconds for a line that
        starts with ``{``.

        All error paths return a dict with ``success=False`` and an ``error``
        string — this method never raises.

        :param command: JSON-RPC method name (e.g. ``'read_sensor'``).
        :param params: Parameter dict; ``None`` defaults to empty dict.
        :return: Result dict from firmware. On error: ``{'success': False, 'error': '...'}``.
        :rtype: Dict[str, Any]
        """
        if not self.is_connected():
            return {"success": False, "error": "Device not connected"}

        params = params or {}
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": command,
            "params": params,
        }

        self._port.reset_output_buffer()
        self._port.reset_input_buffer()
        self._port.write((json.dumps(request) + "\n").encode("utf-8"))

        start = time.time()
        while time.time() - start < self.TIMEOUT:
            if self._port.in_waiting > 0:
                raw = self._port.readline()
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("{"):
                    logger.debug(
                        "send_command(): skipping non-JSON line: %r", line
                    )
                    continue
                try:
                    response = json.loads(line)
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"JSON decode error: {e}"}

                if "error" in response:
                    err = response["error"]
                    return {
                        "success": False,
                        "error": (
                            err.get("message", "Unknown error")
                            if isinstance(err, dict)
                            else str(err)
                        ),
                    }
                return response.get("result", {"success": True})

            time.sleep(_POLL_INTERVAL)

        return {"success": False, "error": f"Timeout after {self.TIMEOUT}s"}

    # -------------------------------------------------------------------------
    # Dunder
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"SensorModule(index={self.index}, name='{self.name}', "
            f"module_id={self.module_id}, fw='{self.firmware_version}', "
            f"sensors={list(self.available_sensors.keys())}, "
            f"actuators={list(self.available_actuators.keys())}, "
            f"connected={self.is_connected()})"
        )
