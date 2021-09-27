import time
import datetime
import os
import pandas as pd
import numpy as np

filepath_inside = "WindowsTest/TestData_inside.csv"
filepath_outside = "WindowsTest/TestData_outside.csv"

humidity_inside = [np.random.normal(0, 2)]
temperature_inside = [np.random.normal(0, 0.5)]
humidity_outside = [np.random.normal(0, 2)]
temperature_outside = [np.random.normal(0, 0.5)]

while True:
    # Open csv file (or create)
    with open(filepath_inside, 'a+') as f_inside, open(filepath_outside, 'a+') as f_outside:
        # If the file is empty, make the colnames
        def updateFile(filepath, f, humidity, temperature):
            if os.stat(filepath).st_size == 0:
                f.write('Datetime,Temperature,Humidity\n')
            
            # Simulate an AR(1) process
            humidity.append(0.92*humidity[len(humidity)-1] + np.random.normal(0, 2))
            temperature.append(0.92*temperature[len(temperature)-1] + np.random.normal(0, 0.5))

            chumidity = humidity[len(humidity)-1] + 66 # Process mean of 66
            ctemperature = temperature[len(temperature)-1] + 22 # Process mean of 22

            current_time = datetime.datetime.now()
            # We don't need microsecond accuracy
            current_time = current_time.replace(microsecond=0)

            f.write(f"{current_time},{ctemperature:0.2f},{chumidity:0.2f}\n")
        
        updateFile(filepath_inside, f_inside, humidity_inside, temperature_inside)
        updateFile(filepath_outside, f_outside, humidity_outside, temperature_outside)

    time.sleep(1)