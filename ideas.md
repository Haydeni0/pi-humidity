# Ideas

## To do

### Run pgadmin in a container, so that the postgres server can be monitored by website
  
### Use python asyncio to do asynchronous logging

- Would be much better than the current logging implementation

### Dash

- Use animations for smoother graph updating
  - <https://stackoverflow.com/questions/63589249/plotly-dash-display-real-time-data-in-smooth-animation>

### Use timescaledb features

- Try out hypertable compression
- Improve the Sensor class with use of TimescaleDB better querying
  - E.g. with time_bucket and percentile_cont
  - timescaledb has ```locf```
  - Outsource timeseries window computations that I wrote by hand before to timescaledb, using commands similar to those [here](https://corpglory.com/s/timescaledb-grafana-plotly-time-series-analysis/)

### Add [glances](https://hub.docker.com/r/nicolargo/glances)

### Clean up code

- Classes:
  - dataclasses + type hints
- proper type hints for everything
- Rename functions, classes
- Clean up [raspberrypi_installation.md](raspberrypi_installation.md)

### Improve and generalise install process

- Make a config file that contains a bunch of user configurable settings
  - Make the number of dht sensors variable
    - Specify in the config the sensor GPIO pin and name
    - Set up database tables and plotting dependent on the sensors
  - Number of bins
  - Sensor history
  - ...
- Make an install script that automates the install process
  - which writes the config files to the local directory (including ```password.env```)
    - allowing the user to type in settings or leave things default
  - Sets up the services to start on boot and display the webpage on the local gui
