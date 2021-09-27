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

    print(f"(INSIDE) Temp={temperature_inside:0.1f}*C  Humidity={humidity_inside:0.1f}%")
    print(f"(OUTSIDE) Temp={temperature_outside:0.1f}*C  Humidity={humidity_outside:0.1f}%")
    
    # time.sleep(DHT_READ_TIMEOUT)
