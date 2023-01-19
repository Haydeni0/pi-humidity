from database_api import DatabaseApi
from sensors import SensorOld
import numpy as np
from time import sleep
from datetime import timedelta

GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"

conn = DatabaseApi()

# Update interval in seconds
update_interval = 2

sensor_history = timedelta(minutes=2)

# There are still some major problems with 
# stability when num_grid is too big or small...
num_grid = 8000
# Define num_grid by the desired update interval
# num_grid = int(sensor_history / timedelta(seconds=update_interval))
# print(num_grid)
# sys.exit()

inside_sensor = SensorOld(conn, "test.dht_inside", sensor_history=sensor_history, num_grid=num_grid)
outside_sensor = SensorOld(conn, "test.dht_outside", sensor_history=sensor_history, num_grid=num_grid)

while True:

    for sensor, name, colour in zip(
        [inside_sensor, outside_sensor], ["Inside", "Outside"], [GREEN_HEX, RED_HEX]
    ):
        inside_sensor.update()
        outside_sensor.update()

        D = np.array(sensor.D_grid_centres)
        H = np.array(sensor.H)
        T = np.array(sensor.T)
        print(D)
        print(H)
        print(T)

    sleep(update_interval)
