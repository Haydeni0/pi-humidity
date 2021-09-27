import Adafruit_DHT
import DHTutils
import time

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN_INSIDE = 4
DHT_PIN_OUTSIDE = 27

DHT_READ_TIMEOUT = 2

# time.sleep(DHT_READ_TIMEOUT)

while True:
    humidity_inside, temperature_inside, humidity_outside, temperature_outside = DHTutils.read_retry_inout(DHT_SENSOR, DHT_PIN_INSIDE, DHT_PIN_OUTSIDE)

    if humidity_inside is not None and temperature_inside is not None:
        print(f"(INSIDE) Temp={temperature_inside:0.1f}*C  Humidity={humidity_inside:0.1f}%")
    else:
        print(f"(INSIDE) Temp=NaN*C  Humidity=NaN%")
    if humidity_outside is not None and temperature_outside is not None:
        print(f"(OUTSIDE) Temp={temperature_outside:0.1f}*C  Humidity={humidity_outside:0.1f}%")
    else:
        print(f"(OUTSIDE) Temp=NaN*C  Humidity=NaN%")
    
    # time.sleep(DHT_READ_TIMEOUT)
