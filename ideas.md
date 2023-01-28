# Ideas

## To do

- Have the plotter repeatedly check for updates to config files so they can be updated without restarting container
- Increase update interval
- Be able to change bucket width using the webpage

### Plotly Dash

- Add y axis labels to the right side as well
- Add buttons to increase/decrease parameters
- Test parameter limits
- Do some sort of postprocessing?
  - Smoothing on the temperature
- Turn off animations for the moment, mt might be the cause of this issue where the graph stays on old values if left in the background for a while?

### Optimise plotter

- Figure out how to make the plotting faster, or run clientside?
- ```app.run_server(..., threaded=True)``` threaded?
- dhtplotter at the moment just appends data to the figure. If the program runs for an extended period of time, will this get too big?
  - Reset figure?

### Use timescaledb features

- Try out hypertable compression
- Improve the Sensor class with use of TimescaleDB better querying
  - E.g. with time_bucket and percentile_cont
  - timescaledb has ```locf```
  - Outsource timeseries window computations that I wrote by hand before to timescaledb, using commands similar to those [here](https://corpglory.com/s/timescaledb-grafana-plotly-time-series-analysis/)

### Add [glances](https://hub.docker.com/r/nicolargo/glances)

### Clean up code

- Clean up [raspberrypi_installation.md](raspberrypi_installation.md)
- Add docstrings
- 

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
