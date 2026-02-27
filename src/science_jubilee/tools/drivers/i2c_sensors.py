"""
drivers/i2c_sensors.py - Host-side driver for I2C sensors.

For each sensor found in module.available_sensors, attaches a typed read method.
Also attaches a generic module.read(sensor_name, **params) for any sensor.

Mirrors firmware/drivers/i2c_sensors.py which registers AS7341, SCD4x, VL53L0X.

Methods attached (if 'read_sensor' command and corresponding sensor are available):
  - module.read(sensor_name, **params)    always attached when read_sensor exists
  - module.read_as7341(duty_cycle=100)    if 'as7341' in available_sensors
  - module.read_scd4x()                   if 'scd4x' in available_sensors
  - module.read_vl53l0x()                 if 'vl53l0x' in available_sensors
  - module.read_<name>(**params)          fallback for any unrecognized sensor

To add support for a new sensor, add a @_handler("<firmware_sensor_name>") function.
"""

import logging
from typing import Any, Dict

from science_jubilee.tools.Tool import ToolStateError

logger = logging.getLogger(__name__)

# Registry mapping firmware sensor name -> attach function
# Populated by the @_handler decorator below.
_SENSOR_HANDLERS: Dict[str, Any] = {}


def _handler(sensor_name: str):
    """Decorator to register a typed sensor attach function by firmware name."""
    def decorator(fn):
        _SENSOR_HANDLERS[sensor_name] = fn
        return fn
    return decorator


def register(module) -> None:
    """Attach read methods for all available I2C sensors.

    Always attaches generic read() if 'read_sensor' command is available.
    Then attaches a typed method for each sensor found in available_sensors.

    :param module: SensorModule instance being configured.
    """
    if "read_sensor" not in module.available_commands:
        logger.debug("i2c_sensors: 'read_sensor' not in commands, skipping")
        return

    _attach_generic_read(module)

    for sensor_name, metadata in module.available_sensors.items():
        if sensor_name in _SENSOR_HANDLERS:
            _SENSOR_HANDLERS[sensor_name](module, metadata)
        else:
            _attach_generic_sensor_method(module, sensor_name, metadata)


# -------------------------------------------------------------------------
# Generic read
# -------------------------------------------------------------------------

def _attach_generic_read(module) -> None:
    """Attach module.read(sensor_name, **params) for any available sensor."""

    def read(sensor_name: str, **params) -> Dict[str, Any]:
        """Read from a named sensor.

        :param sensor_name: Firmware sensor name (e.g. ``'as7341'``, ``'scd4x'``).
        :param params: Additional parameters forwarded to the firmware handler
            (e.g. ``led_intensity=0.05`` for the AS7341).
        :return: Dict of readings keyed by measurement name.
        :rtype: Dict[str, Any]
        :raises ToolStateError: If the sensor is unavailable or the read fails.
        """
        if sensor_name not in module.available_sensors:
            raise ToolStateError(
                f"read(): sensor '{sensor_name}' not available. "
                f"Available: {list(module.available_sensors.keys())}"
            )
        result = module.send_command(
            "read_sensor", {"sensor": sensor_name, **params}
        )
        if not result.get("success"):
            raise ToolStateError(
                f"read('{sensor_name}') failed: {result.get('error')}"
            )
        return result.get("readings", {})

    module.read = read
    logger.info("i2c_sensors: attached module.read()")


# -------------------------------------------------------------------------
# Typed per-sensor methods
# -------------------------------------------------------------------------

@_handler("as7341")
def _attach_as7341(module, metadata: Dict) -> None:
    """Attach module.read_as7341(duty_cycle=100)."""

    def read_as7341(duty_cycle: int = 100) -> Dict[str, int]:
        """Read the AS7341 8-channel spectral sensor.

        Converts ``duty_cycle`` (0–100 integer percentage) to
        ``led_intensity`` (0.0–1.0 float) before sending to firmware.

        :param duty_cycle: Illumination LED brightness as a percentage 0–100,
            defaults to 100 (full brightness).
        :type duty_cycle: int
        :return: Spectral readings keyed by wavelength string,
            e.g. ``{'415nm': 120, '445nm': 340, '480nm': 210, ...}``.
        :rtype: Dict[str, int]
        :raises ValueError: If duty_cycle is outside [0, 100].
        :raises ToolStateError: If the sensor read fails.
        """
        if not (0 <= int(duty_cycle) <= 100):
            raise ValueError(
                f"duty_cycle must be between 0 and 100, got {duty_cycle}"
            )
        result = module.send_command(
            "read_sensor",
            {"sensor": "as7341", "led_intensity": int(duty_cycle) / 100.0},
        )
        if not result.get("success"):
            raise ToolStateError(f"read_as7341() failed: {result.get('error')}")
        return result.get("readings", {})

    module.read_as7341 = read_as7341
    logger.info("i2c_sensors: attached module.read_as7341()")


@_handler("scd4x")
def _attach_scd4x(module, metadata: Dict) -> None:
    """Attach module.read_scd4x()."""

    def read_scd4x() -> Dict[str, float]:
        """Read the SCD4x CO2, temperature, and humidity sensor.

        :return: Dict with keys ``'co2_ppm'``, ``'temperature_c'``,
            ``'humidity_percent'``.
        :rtype: Dict[str, float]
        :raises ToolStateError: If the sensor read fails.
        """
        result = module.send_command("read_sensor", {"sensor": "scd4x"})
        if not result.get("success"):
            raise ToolStateError(f"read_scd4x() failed: {result.get('error')}")
        return result.get("readings", {})

    module.read_scd4x = read_scd4x
    logger.info("i2c_sensors: attached module.read_scd4x()")


@_handler("vl53l0x")
def _attach_vl53l0x(module, metadata: Dict) -> None:
    """Attach module.read_vl53l0x()."""

    def read_vl53l0x() -> Dict[str, float]:
        """Read the VL53L0X time-of-flight distance sensor.

        :return: Dict with key ``'distance_mm'``.
        :rtype: Dict[str, float]
        :raises ToolStateError: If the sensor read fails.
        """
        result = module.send_command("read_sensor", {"sensor": "vl53l0x"})
        if not result.get("success"):
            raise ToolStateError(f"read_vl53l0x() failed: {result.get('error')}")
        return result.get("readings", {})

    module.read_vl53l0x = read_vl53l0x
    logger.info("i2c_sensors: attached module.read_vl53l0x()")


# -------------------------------------------------------------------------
# Fallback for unrecognized sensors
# -------------------------------------------------------------------------

def _attach_generic_sensor_method(
    module, sensor_name: str, metadata: Dict
) -> None:
    """Attach read_<sensor_name>(**params) for sensors with no typed handler."""

    def reader(**params) -> Dict[str, Any]:
        result = module.send_command(
            "read_sensor", {"sensor": sensor_name, **params}
        )
        if not result.get("success"):
            raise ToolStateError(
                f"read_{sensor_name}() failed: {result.get('error')}"
            )
        return result.get("readings", {})

    reader.__name__ = f"read_{sensor_name}"
    reader.__doc__ = (
        f"Read sensor '{sensor_name}' (auto-generated fallback).\n\n"
        f"Firmware metadata: {metadata}"
    )
    setattr(module, f"read_{sensor_name}", reader)
    logger.info("i2c_sensors: attached module.read_%s() (generic)", sensor_name)
