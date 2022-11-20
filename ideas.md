# Ideas

## To do

### Run pgadmin in a container, so that the postgres server can be monitored by website
  
### Use python asyncio to do asynchronous logging

- Would be much better than the current logging implementation

### Use timescaledb features

- Try out hypertable compression 
- Improve the Sensor class with use of TimescaleDB better querying
  - E.g. with time_bucket and percentile_cont
  - Outsource timeseries window computations that I wrote by hand before to timescaledb, using commands similar to those [here](https://corpglory.com/s/timescaledb-grafana-plotly-time-series-analysis/)

### Add [glances](https://hub.docker.com/r/nicolargo/glances)

### Clean up code

- Classes:
  - dataclasses + type hints
- proper type hints for everything
