import os
import time
import datetime
import Adafruit_DHT

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

filepath = '/home/pi/pi-humidity/data/DHT22_data.csv'

# Open csv file (or create)
with open(filepath, 'a+') as f:
    # If the file is empty, make the colnames
    if os.stat(filepath).st_size == 0:
        f.write('Datetime,Temperature,Humidity\r\n')

    while True:
        # Read from the sensor
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        
        current_time = datetime.datetime.now()
        current_time = current_time.replace(microsecond = 0) # We don't need microsecond accuracy

        if humidity is None and temperature is not None:
            f.write(f"{current_time},{temperature:0.2f},NaN\r\n")
        if humidity is not None and temperature is None:
            f.write(f"{current_time},NaN,{humidity:0.2f}\r\n")
        if humidity is not None and temperature is not None:
            f.write(f"{current_time},{temperature:0.2f},{humidity:0.2f}\r\n")
        else:
            f.write(f"{current_time},NaN,NaN\r\n")

        time.sleep(2)
