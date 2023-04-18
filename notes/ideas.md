# Ideas

## To do

- Add a logging service, perhaps like Papertrail but local, to easily view logs
- Add some security features to stop something like accidental DDOS on the pi from too many active sessions?
- Fix timezones

### Plotly Dash

- Add buttons to increase/decrease parameters
- Do some sort of postprocessing?
- Use plotly-resampler to be able to plot more data?

### Optimise plotter

- Use C for the logger for higher performance, on a lightweight container
  - Container built just for logging
  - Still keep the python one running as backup, but at a much lower rate?

### Use timescaledb features

- Try out hypertable compression

### Add [glances](https://hub.docker.com/r/nicolargo/glances)

### Clean up code

- Try clean up the SensorData.history property

### Database backups

- What is the best way to do this?
  - Dump database and rclone?
