"""
drivers/onboard_led.py - Host-side driver for the onboard LED.

Attaches module.blink(duration) if the firmware 'blink' command is available.
Mirrors firmware/drivers/onboard_led.py which registers the LED as an actuator.
"""

import logging
from science_jubilee.tools.Tool import ToolStateError

logger = logging.getLogger(__name__)


def register(module) -> None:
    """Attach blink() to module if 'blink' is an available command.

    :param module: SensorModule instance being configured.
    """
    if "blink" not in module.available_commands:
        logger.debug("onboard_led: 'blink' not in available_commands, skipping")
        return

    def blink(duration: float = 0.5) -> None:
        """Blink the onboard LED.

        :param duration: Blink duration in seconds, defaults to 0.5.
        :type duration: float
        :raises ToolStateError: If the command fails.
        """
        result = module.send_command("blink", {"duration": float(duration)})
        if not result.get("success"):
            raise ToolStateError(f"blink() failed: {result.get('error')}")

    module.blink = blink
    logger.info("onboard_led: attached module.blink()")
