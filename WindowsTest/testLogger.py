import datetime
import os
import time
import math

import numpy as np
import pandas as pd

filepath_inside = "WindowsTest/TestData/inside.csv"
filepath_outside = "WindowsTest/TestData/outside.csv"

humidity_inside = [np.random.normal(0, 2)]
temperature_inside = [np.random.normal(0, 0.5)]
humidity_outside = [np.random.normal(0, 2)]
temperature_outside = [np.random.normal(0, 0.5)]


log_interval = 1
AR_time_constant = 5*60 # Time constant of the AR(1) processes (in seconds)
C = math.exp(-log_interval/AR_time_constant)
sigma_H = 10
sigma_T = 4
mean_H = 66
mean_T = 22
while True:
    # Open csv file (or create)
    with open(filepath_inside, 'a+') as f_inside, open(filepath_outside, 'a+') as f_outside:
        # If the file is empty, make the colnames
        def updateFile(filepath, f, humidity, temperature):
            if os.stat(filepath).st_size == 0:
                f.write('Datetime,Temperature,Humidity\n')
            
            # Simulate an AR(1) process
            humidity.append(C*humidity[len(humidity)-1] + np.random.normal(0, sigma_H*math.sqrt(1-C*C)))
            temperature.append(C*temperature[len(temperature)-1] + np.random.normal(0, sigma_T*math.sqrt(1-C*C)))

            chumidity = humidity[len(humidity)-1] + mean_H
            ctemperature = temperature[len(temperature)-1] + mean_T

            current_time = datetime.datetime.now()
            # We don't need microsecond accuracy
            current_time = current_time.replace(microsecond=0)

            f.write(f"{current_time},{ctemperature:0.2f},{chumidity:0.2f}\n")
        
        updateFile(filepath_inside, f_inside, humidity_inside, temperature_inside)
        updateFile(filepath_outside, f_outside, humidity_outside, temperature_outside)

    time.sleep(log_interval)
