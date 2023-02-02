# Ideas

## To do

- Resize graphs to better fit the screen on fish tank
  - or maybe zoom in
- Also output static images of each graph that can be retrieved from the webserver

### Plotly Dash

- Add buttons to increase/decrease parameters
- Do some sort of postprocessing?
- Use plotly-resampler to be able to plot more data?

### Optimise plotter

- Use C for the logger for higher performance, lightweight container
  - Container built just for logging
  - Still keep the python one though as backup

### Use timescaledb features

- Try out hypertable compression

### Add [glances](https://hub.docker.com/r/nicolargo/glances)

### Clean up code

- Try clean up the SensorData.history property

### Database backups

- What is the best way to do this?
  - Dump database and rclone?
