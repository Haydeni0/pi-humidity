from dhtPlotting import plotDHT

# Call this module from the raspberry pi
# Plot DHT, connect to the local server
connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "haydeni0",
    "password": "raspizeroWH_SQL",
    'raise_on_warnings': True
}

plotDHT(connection_config, fig_save_path="/home/pi/pi-humidity/DHT_graph.png")