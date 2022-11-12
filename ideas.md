# Ideas

## To do

### Run pgadmin in a container, so that the postgres server can be monitored by website
  
### Use python asyncio to do asynchronous logging

- Would be much better than the current logging implementation

### Use timescaledb hypertables

- Try out compression

### Use plotly to do real time plotting

- Outsource timeseries window computations that I wrote by hand before to timescaledb, using commands similar to those [here](https://corpglory.com/s/timescaledb-grafana-plotly-time-series-analysis/)
- Make a demo live-updating plotly graph first
  - Show on a website somehow
    - Use [gunicorn](https://www.devcoons.com/how-to-deploy-your-plotly-dash-dashboard-using-docker/)

### Add [glances](https://hub.docker.com/r/nicolargo/glances)

### Clean up code

- Classes:
  - dataclasses + type hints
- proper type hints for everything
