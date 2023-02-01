# Ideas

## To do

- Resize graphs to better fit the screen on fish tank
  - or maybe zoom in
- Add figure update interval to the webpage as a changeable parameter
- Increase update interval
- Be able to change bucket width using the webpage
- Also output static images of each graph that can be retrieved from the webserver
- Make the interval ticks client-side, so that if I have more than one connection to the dash server they dont activate callbacks all at once
- Try out gunicorn again, to be able to use more than one process
  - Make things thread-safe
  - Try to remove global variables, as they aren't that safe to use with Dash/threading
    - Using a global SensorData is not safe, even with the use of pscyopg2 ThreadedConnectionPools
      - Each worker will have a forked copy of this, so if the history changes for one worker, the others wont be affected
      - This leads to the graph changing history length on an update when the worker changes
      - Need to use some sort of data sharing system between workers, or clientside caching
        - dcc.Store, or flask_caching ?
        - history probably needs to be stored, so that it will apply on every worker
  - Useful [forum discussion](https://github.com/plotly/dash/issues/94)
- Do something about cached variables piling up
  - Run some sort of cleanup regularly on old pickles?
  - Or every time sensordata is overwritten

### Plotly Dash

- Add y axis labels to the right side as well
- Add buttons to increase/decrease parameters
- Test parameter limits
- Do some sort of postprocessing?
- Use plotly-resampler to be able to plot more data?
- use the webgl versions of plotly for faster rendering, e.g. go.Scattergl

### Optimise plotter

- Figure out how to make the plotting faster, or run clientside?
- ```app.run_server(..., threaded=True)``` threaded?
- dhtplotter at the moment just appends data to the figure. If the program runs for an extended period of time, will this get too big?
  - Reset figure?
- Use C for the logger for higher performance, lightweight container
  - Container built just for logging
  - Still keep the python one though as backup

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
- Clean up dhtPlotter, maybe move into multiple files

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
