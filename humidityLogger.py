import os
import time
import Adafruit_DHT

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

filepath = '/home/pi/pi-humidity/DHT22_data.csv'

try:
    f = open(filepath, 'a+')
    if os.stat(filepath).st_size == 0:
            f.write('Date,Time,Temperature,Humidity\r\n')
except:
    pass

while True:
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

    if humidity is not None and temperature is not None:
        f.write(f"{time.strftime('%Y-%m-%d')},{time.strftime('%H:%M:%S')},{temperature:0.2f},{humidity:0.2f}\r\n")
    else:
        print("Failed to retrieve data from humidity sensor")

    time.sleep(2)
