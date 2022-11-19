from DHT_MySQL_interface import DHTConnection
from Sensors import DHTSensorData
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from flask import Flask
import numpy as np
from time import sleep


GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"

conn = DHTConnection()

server = Flask(__name__)
app = Dash(name=__name__)

inside_sensor = DHTSensorData(conn, "test.dht_inside")
outside_sensor = DHTSensorData(conn, "test.dht_outside")

# Update interval in seconds
update_interval = 2

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




