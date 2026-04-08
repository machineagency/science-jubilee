import board
import busio
import pwmio


def register(hw):
    """Initialize and register PWM LED for illumination (IO43)."""
    try:
        # Deinitialize UART first to free up the pin
        try:
            uart = busio.UART(rx=board.D7, tx=board.D6)
            uart.deinit()
        except:
            pass

        blue_led = pwmio.PWMOut(board.D6, frequency=5000, duty_cycle=0)

        hw.register_actuator('blue_led', blue_led, {
            'type': 'pwm_output',
            'function': 'illumination',
            'pin': 'D6 (GPIO43)',
            'frequency_hz': 5000,
            'duty_range': [0, 65535]
        })
    except Exception as e:
        print(f"✗ Blue LED init failed: {e}")
