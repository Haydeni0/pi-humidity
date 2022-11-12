# Ideas

##

- Run pgadmin in a container, so that the postgres server can be monitored by website
- If the logger fails (or anything else) is there a way to automatically restart the container?
  - The logger script will stop running, then the container stops also
  - Put the ```restart: always``` field in compose.yml
  - Maybe have the logger in a separate container to the plotting
- Use python asyncio to do asynchronous logging
  - Would be much better than the current logging implementation
- Use timescaledb hypertables
- Use plotly to do real time plotting
  - Outsource timeseries computations that I wrote by hand before to timescaledb, using commands similar to those [here](https://corpglory.com/s/timescaledb-grafana-plotly-time-series-analysis/)
- Add [glances](https://hub.docker.com/r/nicolargo/glances)
