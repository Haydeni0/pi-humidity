# Ideas

## To do
  
- Fix dhtplotter crash when two instances connect at the same time, e.g. opening two tabs with raspidht.webredirect.org
  - Something to do with ssl?
  - Look at ```docker compose logs -f```
- Have the plotter repeatedly check for updates to config files so they can be updated without restarting container

### Use python asyncio to do asynchronous logging

- Would be better than the current logging implementation, but only necessary for high frequency logging with many sensors...

### Plotly Dash

- Add y axis labels to the right side as well
- Add buttons to increase/decrease parameters
- Test parameter limits
- Do some sort of postprocessing?
  - Smoothing on the temperature
- Turn off animations for the moment, mt might be the cause of this issue where the graph stays on old values if left in the background for a while?
- Can the plotting be done clientside? querying is fast, but plotting is slow...

### Optimise plotter

- The current implementation is simple and could be made faster by
  - querying more efficiently (see below section)
  - using double ended queues to push new data as it comes in and pop old data (automatically using python deque's ```maxlen``` option)
- Make things server-side not client side
  - If we have several windows open, we don't want each one independently querying postgres as they'll all just receive the same info...
  - Or maybe just have the initial load client side, but the regular updates server side? Basicallly, just do as few queries as possible

Also, for simplicity, change the bins to time buckets with a time window based on absolute time, e.g. every four minutes starting at the hour.

Example process

- for 2 days of sensor history
- bins are time buckets of 4 minutes, starting cleanly at the hour (the bucket time period must be a factor of 60 minutes)
  - 720 bins in two days
- The datetime is 2023-01-04 13:05:00

1. Use timescaledb to find the timebucket averages of every four minutes, starting at the hour
1. e.g. 12:52:00 -> 12:56:00 -> 13:00:00

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

Test out bash script with cert for pi-humidity.webredirect.org

### Database backups

- What is the best way to do this?
  - Dump database and rclone?
