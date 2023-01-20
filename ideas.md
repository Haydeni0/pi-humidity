# Ideas

## To do
  
### Use python asyncio to do asynchronous logging

- Would be better than the current logging implementation, but only necessary for high frequency logging with many sensors...

### Plotly Dash

- Add y axis labels to the right side as well
- Add buttons to increase/decrease parameters
- Test parameter limits
- Do some sort of postprocessing?
  - Smoothing on the temperature
- Use animations for smoother graph updating
  - <https://stackoverflow.com/questions/63589249/plotly-dash-display-real-time-data-in-smooth-animation>
  - Can't seem to get this to work...

### Optimise plotter

- The current implementation is simple and could be made faster by
  - querying more efficiently (see below section)
  - using double ended queues to push new data as it comes in and pop old data (automatically using python deque's ```maxlen``` option)

### Use timescaledb features

- Try out hypertable compression
- Improve the Sensor class with use of TimescaleDB better querying
  - E.g. with time_bucket and percentile_cont
  - timescaledb has ```locf```
  - Outsource timeseries window computations that I wrote by hand before to timescaledb, using commands similar to those [here](https://corpglory.com/s/timescaledb-grafana-plotly-time-series-analysis/)

### Add [glances](https://hub.docker.com/r/nicolargo/glances)

### Clean up code

- Clean up [raspberrypi_installation.md](raspberrypi_installation.md)
- Remove test files, other useless things

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

### WAN webpage

- Set up dynamic DNS service with dynu + docker compose somehow?
- Make sure there is an ssl certificate for https
  - certbot docker service?
