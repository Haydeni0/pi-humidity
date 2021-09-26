import time
import datetime
import os
import pandas as pd
import numpy as np

filepath = "WindowsTest/TestData.csv"

humidity = [np.random.normal(66, 2)]
temperature = [np.random.normal(22, 0.5)]

while True:
    # Open csv file (or create)
    with open(filepath, 'a+') as f:
        # If the file is empty, make the colnames
        if os.stat(filepath).st_size == 0:
            f.write('Datetime,Temperature,Humidity\n')
            
        # Simulate an AR(1) process
        humidity.append(0.99*humidity[len(humidity)-1] + np.random.normal(0, 2))
        temperature.append(0.99*temperature[len(temperature)-1] + np.random.normal(0, 0.5))

        chumidity = humidity[len(humidity)-1]
        ctemperature = temperature[len(temperature)-1]

        current_time = datetime.datetime.now()
        # We don't need microsecond accuracy
        current_time = current_time.replace(microsecond=0)

        f.write(f"{current_time},{ctemperature:0.2f},{chumidity:0.2f}\n")

    time.sleep(2)