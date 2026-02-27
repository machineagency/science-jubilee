"""
drivers/blue_led.py - Host-side driver for the PWM illumination LED.

Attaches module.set_led(intensity) if the firmware 'set_led' command is available.
Mirrors firmware/drivers/blue_led.py which registers the PWM LED as an actuator.
"""

import logging
from science_jubilee.tools.Tool import ToolStateError

logger = logging.getLogger(__name__)


def register(module) -> None:
    """Attach set_led() to module if 'set_led' is an available command.

    :param module: SensorModule instance being configured.
    """
    if "set_led" not in module.available_commands:
        logger.debug("blue_led: 'set_led' not in available_commands, skipping")
        return

    def set_led(intensity: float = 0.0) -> None:
        """Set the illumination LED intensity.

        :param intensity: LED brightness as a fraction 0.0 (off) to 1.0 (full),
            defaults to 0.0 (off).
        :type intensity: float
        :raises ValueError: If intensity is outside [0.0, 1.0].
        :raises ToolStateError: If the command fails.
        """
        if not (0.0 <= float(intensity) <= 1.0):
            raise ValueError(
                f"intensity must be between 0.0 and 1.0, got {intensity}"
            )
        result = module.send_command("set_led", {"intensity": float(intensity)})
        if not result.get("success"):
            raise ToolStateError(f"set_led() failed: {result.get('error')}")

    module.set_led = set_led
    logger.info("blue_led: attached module.set_led()")
