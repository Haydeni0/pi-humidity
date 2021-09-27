import Adafruit_DHT
import time

def read_retry_inout(sensor, pin_inside, pin_outside, retries=10, delay_seconds=1, platform=None):
    """Read DHT sensor of specified sensor type (DHT11, DHT22, or AM2302) on
    specified pin and return a tuple of humidity (as a floating point value
    in percent) and temperature (as a floating point value in Celsius).
    Unlike the read function, this read_retry function will attempt to read
    multiple times (up to the specified max retries) until a good reading can be
    found. If a good reading cannot be found after the amount of retries, a tuple
    of (None, None) is returned. The delay between retries is by default 1
    seconds, but can be overridden.

    This has been modified from Adafruit_DHT source to allow reading of two sensors at 
    once without queueing their retries (which adds latency)
    """
    done_inside = False
    done_outside = False

    for i in range(retries):
        if not done_inside:
            humidity_inside, temperature_inside = Adafruit_DHT.read(sensor, pin_inside, platform)
            if humidity_inside is not None and temperature_inside is not None:
                done_inside = True
        if not done_outside:
            humidity_outside, temperature_outside = Adafruit_DHT.read(sensor, pin_outside, platform)
            if humidity_outside is not None and temperature_outside is not None:
                done_outside = True

        if done_inside and done_outside:
            return (humidity_inside, temperature_inside, humidity_outside, temperature_outside)
        
        if i < retries-1:
            time.sleep(delay_seconds)

    if done_inside and not done_outside:
        return (humidity_inside, temperature_inside, None, None)
    elif not done_inside and done_outside:
        return (None, None, humidity_outside, temperature_outside)
    else:
        return (None, None)