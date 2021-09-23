import Adafruit_DHT
import time

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

DHT_READ_TIMEOUT = 2

time.sleep(DHT_READ_TIMEOUT)

while True:
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

    if humidity is not None and temperature is not None:
        print(f"Temp={temperature:0.1f}*C  Humidity={humidity:0.1f}%")
    else:
        print("Failed to retrieve data from humidity sensor")
    
    time.sleep(DHT_READ_TIMEOUT)
