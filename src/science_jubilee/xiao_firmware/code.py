"""
code.py - Main Loop & Command Handling
Runs continuously on XIAO ESP32S3

This file:
1. Sets up JSON-RPC communication protocol
2. Registers all available commands
3. Executes commands and returns structured responses
"""

import time
import json
import usb_cdc
from boot import hardware

# USB CDC setup
serial = usb_cdc.console
serial.timeout = 1

# ============================================================================
# Command Registry
# ============================================================================

class CommandRegistry:
    """Registry for all available commands."""
    
    def __init__(self, hw):
        self.hw = hw
        self.commands = {}
    
    def register(self, name, handler, params_schema=None, description=""):
        """Register a command handler."""
        self.commands[name] = {
            'handler': handler,
            'params': params_schema or {},
            'description': description
        }
    
    def execute(self, method, params):
        """Execute a command and return result."""
        if method not in self.commands:
            return {
                'success': False,
                'error': f'Unknown command: {method}',
                'available': list(self.commands.keys())
            }
        
        try:
            result = self.commands[method]['handler'](params)
            if not isinstance(result, dict):
                result = {'value': result}
            result.setdefault('success', True)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def get_commands_info(self):
        """Get information about all commands."""
        return {
            name: {
                'params': cmd['params'],
                'description': cmd['description']
            }
            for name, cmd in self.commands.items()
        }

# ============================================================================
# Command Handlers
# ============================================================================

def cmd_get_capabilities(params):
    """Return complete system capabilities."""
    caps = hardware.get_capabilities()
    caps['commands'] = commands.get_commands_info()
    return {'success': True, 'capabilities': caps}

def cmd_blink(params):
    """Blink onboard LED."""
    duration = float(params.get('duration', 0.5))
    led = hardware.get_actuator('onboard_led')
    
    if not led:
        return {'success': False, 'error': 'LED not available'}
    
    led.value = False
    time.sleep(duration)
    led.value = True
    
    return {'success': True, 'duration': duration}

def cmd_set_motor(params):
    """Set DC motor throttle."""
    motor_name = params.get('motor')
    throttle = int(params.get('throttle', 0))
    
    if not motor_name:
        return {'success': False, 'error': 'motor parameter required'}
    
    motor = hardware.get_actuator(motor_name)
    if not motor:
        return {
            'success': False,
            'error': f'Motor {motor_name} not available',
            'available': [n for n in hardware.actuators.keys() if 'motor' in n]
        }
    
    if not -100 <= throttle <= 100:
        return {'success': False, 'error': 'throttle must be -100 to 100'}
    
    motor.throttle = throttle / 100.0
    return {'success': True, 'motor': motor_name, 'throttle': throttle}

def cmd_pump(params):
    """Run pump for specified duration."""
    motor_name = params.get('motor')
    duration = params.get('duration')
    throttle = int(params.get('throttle', 100))
    
    if not motor_name or duration is None:
        return {'success': False, 'error': 'motor and duration required'}
    
    motor = hardware.get_actuator(motor_name)
    if not motor:
        return {'success': False, 'error': f'Motor {motor_name} not available'}
    
    # Run pump
    motor.throttle = throttle / 100.0
    time.sleep(float(duration))
    motor.throttle = 0
    
    return {
        'success': True,
        'motor': motor_name,
        'duration': float(duration),
        'throttle': throttle
    }

def cmd_stop_motor(params):
    """Stop one or all motors."""
    motor_name = params.get('motor', 'all')
    
    if motor_name == 'all':
        stopped = []
        for name, info in hardware.actuators.items():
            if 'motor' in name and hasattr(info['instance'], 'throttle'):
                info['instance'].throttle = 0
                stopped.append(name)
        return {'success': True, 'stopped': stopped}
    else:
        motor = hardware.get_actuator(motor_name)
        if not motor:
            return {'success': False, 'error': f'{motor_name} not found'}
        if hasattr(motor, 'throttle'):
            motor.throttle = 0
            return {'success': True, 'motor': motor_name}
        return {'success': False, 'error': f'{motor_name} is not a motor'}

def cmd_read_sensor(params):
    """Read from a sensor."""
    sensor_name = params.get('sensor')
    
    if not sensor_name:
        return {
            'success': False,
            'error': 'sensor parameter required',
            'available': list(hardware.sensors.keys())
        }
    
    sensor = hardware.get_sensor(sensor_name)
    if not sensor:
        return {
            'success': False,
            'error': f'Sensor {sensor_name} not available',
            'available': list(hardware.sensors.keys())
        }
    
    # Route to appropriate reader
    if sensor_name == 'as7341':
        return read_spectrometer(sensor, params)
    elif sensor_name == 'scd4x':
        return read_scd4x(sensor, params)
    elif sensor_name == 'vl53l0x':
        return read_distance(sensor, params)
    else:
        return {'success': False, 'error': f'No handler for {sensor_name}'}

def read_spectrometer(sensor, params):
    """Read AS7341 spectrometer."""
    led_current = int(params.get('led_current', 10))

    # Turn on AS7341's onboard white LED
    sensor.led_current = led_current  # mA (4-258)
    sensor.led = True
    time.sleep(0.1)

    # Read all channels
    readings = {
        '415nm': sensor.channel_415nm,
        '445nm': sensor.channel_445nm,
        '480nm': sensor.channel_480nm,
        '515nm': sensor.channel_515nm,
        '555nm': sensor.channel_555nm,
        '590nm': sensor.channel_590nm,
        '630nm': sensor.channel_630nm,
        '680nm': sensor.channel_680nm
    }

    # Turn off LED
    sensor.led = False

    return {
        'success': True,
        'sensor': 'as7341',
        'led_current': led_current,
        'readings': readings
    }

def read_scd4x(sensor, params):
    """Read SCD4x environmental sensor."""
    if not sensor.data_ready:
        sensor.measure_single_shot()
        time.sleep(5)
    
    if sensor.data_ready:
        return {
            'success': True,
            'sensor': 'scd4x',
            'readings': {
                'co2_ppm': sensor.CO2,
                'temperature_c': sensor.temperature,
                'humidity_percent': sensor.relative_humidity
            }
        }
    return {'success': False, 'error': 'Sensor data not ready'}

def read_distance(sensor, params):
    """Read VL53L0X distance sensor."""
    return {
        'success': True,
        'sensor': 'vl53l0x',
        'readings': {
            'distance_mm': sensor.range
        }
    }

def cmd_capture_image(params):
    """Capture a JPEG image from the OV2640 camera.

    Returns the image as a base64-encoded string inside the JSON response.
    For QQVGA (160x120) this is typically 3–12 KB of base64 and transfers
    in under 2 seconds at 115200 baud. Increase module.timeout for larger
    resolutions on the host side.
    """
    import binascii

    cam = hardware.get_sensor('camera')
    if not cam:
        return {'success': False, 'error': 'Camera not available'}

    # frame_size is set at init time in the camera driver (drivers/camera.py).
    # Resolution is fixed until the firmware is reflashed.
    frame = cam.take(1)
    if frame is None:
        return {'success': False, 'error': 'Failed to capture frame'}

    encoded = binascii.b2a_base64(bytes(frame)).decode('ascii').strip()

    return {
        'success': True,
        'format': 'jpeg',
        'encoding': 'base64',
        'width': cam.width,
        'height': cam.height,
        'size_bytes': len(frame),
        'data': encoded,
    }


def cmd_set_led(params):
    """Set external blue LED intensity."""
    intensity = float(params.get('intensity', 0))

    blue_led = hardware.get_actuator('blue_led')
    if not blue_led:
        return {'success': False, 'error': 'LED not available'}

    if not 0 <= intensity <= 1:
        return {'success': False, 'error': 'intensity must be 0-1'}

    blue_led.duty_cycle = int(intensity * 65535)
    return {'success': True, 'intensity': intensity}

def cmd_set_sensor_led(params):
    """Set AS7341 onboard white LED."""
    current = int(params.get('current', 0))

    sensor = hardware.get_sensor('as7341')
    if not sensor:
        return {'success': False, 'error': 'AS7341 not available'}

    if current == 0:
        sensor.led = False
        return {'success': True, 'led': False, 'current': 0}

    if not 4 <= current <= 258:
        return {'success': False, 'error': 'current must be 0 (off) or 4-258 mA'}

    sensor.led_current = current
    sensor.led = True
    return {'success': True, 'led': True, 'current': current}

def cmd_get_property(params):
    """Get any property from a registered sensor."""
    sensor_name = params.get('sensor')
    prop = params.get('property')

    if not sensor_name or not prop:
        return {'success': False, 'error': 'sensor and property required'}

    sensor = hardware.get_sensor(sensor_name)
    if not sensor:
        return {'success': False, 'error': f'Sensor {sensor_name} not available'}

    try:
        value = getattr(sensor, prop)
        if isinstance(value, tuple):
            value = list(value)
        elif not isinstance(value, (int, float, bool, str, list, type(None))):
            return {'success': False, 'error': f'{prop} returned non-serializable type: {type(value).__name__}'}
        return {'success': True, 'property': prop, 'value': value}
    except AttributeError:
        return {'success': False, 'error': f'{prop} not found on {sensor_name}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def cmd_set_property(params):
    """Set any property on a registered sensor."""
    sensor_name = params.get('sensor')
    prop = params.get('property')
    value = params.get('value')

    if not sensor_name or not prop:
        return {'success': False, 'error': 'sensor, property, and value required'}

    sensor = hardware.get_sensor(sensor_name)
    if not sensor:
        return {'success': False, 'error': f'Sensor {sensor_name} not available'}

    try:
        setattr(sensor, prop, value)
        return {'success': True, 'property': prop, 'value': value}
    except AttributeError:
        return {'success': False, 'error': f'{prop} is read-only on {sensor_name}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ============================================================================
# Register All Commands
# ============================================================================

commands = CommandRegistry(hardware)

commands.register('get_capabilities', cmd_get_capabilities,
                 params_schema={},
                 description='Get system capabilities and available commands')

commands.register('blink', cmd_blink,
                 params_schema={'duration': 'float (seconds)'},
                 description='Blink onboard LED')

commands.register('set_motor', cmd_set_motor,
                 params_schema={
                     'motor': 'string (motor name)',
                     'throttle': 'int (-100 to 100)'
                 },
                 description='Set DC motor throttle')

commands.register('pump', cmd_pump,
                 params_schema={
                     'motor': 'string (motor name)',
                     'duration': 'float (seconds)',
                     'throttle': 'int (0-100, default 100)'
                 },
                 description='Run pump for duration')

commands.register('stop_motor', cmd_stop_motor,
                 params_schema={'motor': 'string (name or "all")'},
                 description='Stop motor(s)')

commands.register('read_sensor', cmd_read_sensor,
                 params_schema={
                     'sensor': 'string (sensor name)',
                     'led_intensity': 'float (0-1, for spectrometer)'
                 },
                 description='Read from sensor')

commands.register('set_led', cmd_set_led,
                 params_schema={'intensity': 'float (0-1)'},
                 description='Set external blue LED intensity')

commands.register('set_sensor_led', cmd_set_sensor_led,
                 params_schema={'current': 'int (0=off, 4-258 mA)'},
                 description='Set AS7341 onboard white LED')

commands.register('capture_image', cmd_capture_image,
                 params_schema={},
                 description='Capture a JPEG image from the OV2640 camera, returned as base64')

commands.register('get_property', cmd_get_property,
                 params_schema={'sensor': 'string', 'property': 'string'},
                 description='Get any property from a sensor')

commands.register('set_property', cmd_set_property,
                 params_schema={'sensor': 'string', 'property': 'string', 'value': 'any'},
                 description='Set any property on a sensor')

# ============================================================================
# Protocol Handler
# ============================================================================

def parse_request(line_str):
    """Parse incoming request (JSON-RPC only)."""
    try:
        request = json.loads(line_str)
        return (
            request.get('method'),
            request.get('params', {}),
            request.get('id')
        )
    except:
        return None, None, None

def send_response(result, request_id=None):
    """Send JSON-RPC response."""
    response = {
        'jsonrpc': '2.0',
        'id': request_id
    }
    
    if result.get('success', True):
        response['result'] = result
    else:
        response['error'] = {
            'message': result.get('error', 'Unknown error'),
            'data': result
        }
    
    print(json.dumps(response))

# ============================================================================
# Main Loop
# ============================================================================

print("Bioreactor firmware ready!")
print(f"Available commands: {list(commands.commands.keys())}\n")

while True:
    if serial.in_waiting > 0:
        try:
            line = serial.readline()
            if not line or line in (b'\r', b'\n'):
                continue
            
            line_str = line.decode('utf-8').strip()
            if not line_str:
                continue
            
            # Parse request
            method, params, request_id = parse_request(line_str)
            
            if method is None:
                send_response({
                    'success': False,
                    'error': 'Invalid JSON-RPC request'
                }, request_id)
                continue
            
            # Execute command
            result = commands.execute(method, params)
            
            # Send response
            send_response(result, request_id)
            
        except Exception as e:
            send_response({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })
