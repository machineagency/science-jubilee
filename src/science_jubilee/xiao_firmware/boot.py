"""
boot.py - Hardware Initialization & Registry
Runs once on XIAO ESP32S3 startup

To add a new component:
1. Create a file in drivers/ with a register(hw) function
2. Add the driver name to the DRIVERS list below
"""

# Firmware metadata
FIRMWARE_VERSION = "1.0.0"
BOARD_TYPE = "XIAO_ESP32S3"

# Module identity — set these per Xiao before flashing
MODULE_ID = 0
MODULE_NAME = "module_0"

# Drivers to load — add/remove as needed
DRIVERS = [
    'onboard_led',
    'blue_led',
    'dc_motors',
    'i2c_sensors',
    'camera',       # OV2640 — XIAO ESP32S3 Sense only
]

# ============================================================================
# Hardware Registry
# ============================================================================

class HardwareRegistry:
    """Central registry for all hardware components."""

    def __init__(self):
        self.actuators = {}
        self.sensors = {}
        self.metadata = {
            'module_id': MODULE_ID,
            'module_name': MODULE_NAME,
            'firmware_version': FIRMWARE_VERSION,
            'board_type': BOARD_TYPE,
            'board_id': self._get_board_id()
        }

    def _get_board_id(self):
        """Get unique board identifier if available."""
        try:
            import microcontroller
            return ''.join([f'{b:02x}' for b in microcontroller.cpu.uid])
        except:
            return 'unknown'

    def register_actuator(self, name, instance, metadata):
        """Register an actuator (motor, LED, etc)."""
        self.actuators[name] = {
            'instance': instance,
            'metadata': metadata,
            'enabled': True
        }
        print(f"  + {name}")

    def register_sensor(self, name, instance, metadata):
        """Register a sensor."""
        self.sensors[name] = {
            'instance': instance,
            'metadata': metadata,
            'enabled': True
        }
        print(f"  + {name}")

    def get_actuator(self, name):
        """Get actuator instance by name."""
        if name in self.actuators and self.actuators[name]['enabled']:
            return self.actuators[name]['instance']
        return None

    def get_sensor(self, name):
        """Get sensor instance by name."""
        if name in self.sensors and self.sensors[name]['enabled']:
            return self.sensors[name]['instance']
        return None

    def get_capabilities(self):
        """Return complete hardware capabilities."""
        return {
            'metadata': self.metadata,
            'actuators': {
                name: info['metadata']
                for name, info in self.actuators.items()
                if info['enabled']
            },
            'sensors': {
                name: info['metadata']
                for name, info in self.sensors.items()
                if info['enabled']
            }
        }

# ============================================================================
# Main Initialization
# ============================================================================

print(f"\n[{MODULE_NAME}] Initializing (FW v{FIRMWARE_VERSION})")

hardware = HardwareRegistry()

for _driver_name in DRIVERS:
    try:
        _mod = __import__('drivers.' + _driver_name)
        getattr(_mod, _driver_name).register(hardware)
    except Exception as e:
        print(f"  x {_driver_name}: {e}")

print(f"[{MODULE_NAME}] Ready! {len(hardware.actuators)} actuators, {len(hardware.sensors)} sensors")
