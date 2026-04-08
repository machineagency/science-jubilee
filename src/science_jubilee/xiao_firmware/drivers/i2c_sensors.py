import board
import busio


def register(hw):
    """Initialize and register all I2C sensors."""
    try:
        i2c = busio.I2C(board.D5, board.D4)  # D5=SCL(GPIO6), D4=SDA(GPIO5)
    except Exception as e:
        print(f"✗ I2C init failed: {e}")
        return

    # Try AS7341 Spectrometer
    try:
        from adafruit_as7341 import AS7341
        spec = AS7341(i2c)
        hw.register_sensor('as7341', spec, {
            'type': 'spectrometer',
            'channels': ['415nm', '445nm', '480nm', '515nm',
                       '555nm', '590nm', '630nm', '680nm'],
            'interface': 'i2c'
        })
    except (ImportError, RuntimeError, OSError):
        print("✗ AS7341 not found")

    # Try SCD4x CO2/Temperature/Humidity sensor
    try:
        import adafruit_scd4x
        scd = adafruit_scd4x.SCD4X(i2c)
        scd.start_periodic_measurement()
        hw.register_sensor('scd4x', scd, {
            'type': 'environmental',
            'measurements': ['co2_ppm', 'temperature_c', 'humidity_percent'],
            'interface': 'i2c'
        })
    except (ImportError, RuntimeError, OSError):
        print("✗ SCD4x not found")

    # Try VL53L0X Distance sensor
    try:
        import adafruit_vl53l0x
        vl = adafruit_vl53l0x.VL53L0X(i2c)
        hw.register_sensor('vl53l0x', vl, {
            'type': 'distance',
            'range_mm': [30, 1000],
            'interface': 'i2c'
        })
    except (ImportError, RuntimeError, OSError):
        print("✗ VL53L0X not found")
