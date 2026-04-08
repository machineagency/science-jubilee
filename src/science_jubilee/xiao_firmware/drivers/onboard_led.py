import board
from digitalio import DigitalInOut, Direction


def register(hw):
    """Initialize and register onboard LED (IO21)."""
    try:
        led = DigitalInOut(board.LED)
        led.direction = Direction.OUTPUT
        led.value = True  # LED on = ready

        hw.register_actuator('onboard_led', led, {
            'type': 'digital_output',
            'function': 'indicator',
            'pin': 'LED (GPIO21)'
        })
    except Exception as e:
        print(f"✗ Onboard LED init failed: {e}")
