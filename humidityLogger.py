import os
import time
import datetime
import Adafruit_DHT
import DHTutils

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN_INSIDE = 4
DHT_PIN_OUTSIDE = 27

filepath_inside = '/home/pi/pi-humidity/data/DHT22_inside.csv'
filepath_outside = '/home/pi/pi-humidity/data/DHT22_outside.csv'

while True:
    # Open csv file (or create)
    with open(filepath_inside, 'a+') as f_inside, open(filepath_outside, 'a+') as f_outside:
        # If the file is empty, make the colnames
        if os.stat(filepath_inside).st_size == 0:
            f_inside.write('Datetime,Temperature,Humidity\n')
        if os.stat(filepath_outside).st_size == 0:
            f_outside.write('Datetime,Temperature,Humidity\n')

        # Read from the sensor
        humidity_inside, temperature_inside, humidity_outside, temperature_outside = DHTutils.read_retry_inout(DHT_SENSOR, DHT_PIN_INSIDE, DHT_PIN_OUTSIDE)

        current_time = datetime.datetime.now()
        # We don't need microsecond accuracy
        current_time = current_time.replace(microsecond=0)

        if humidity_inside is not None and temperature_inside is not None:
            f_inside.write(f"{current_time},{temperature_inside:0.1f},{humidity_inside:0.1f}\n")
        else:
            f_inside.write(f"{current_time},NaN,NaN\n")
        if humidity_outside is not None and temperature_outside is not None:
            f_outside.write(f"{current_time},{temperature_outside:0.1f},{humidity_outside:0.1f}\n")
        else:
            f_outside.write(f"{current_time},NaN,NaN\n")


    time.sleep(2)
