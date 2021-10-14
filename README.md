# pi-humidity
Repo containing code for pi humidity monitoring

## To-do
- Tidy up graph, labels, titles, etc.
- Do profiling to see what needs speeding up
  - Why does the data take so long to initially load?
  - is dask the problem
- google drive pi backups

### Other
- Back up an image of the fully configured pi
  - Or docker container?
- Upload the csv file to google drive intermittently
  - rclone or rsync

### Data handling & ingesting
- Store one csv per month, as querying a large csv might be difficult
  - One year of data (2 second rate) is 15,768,000 rows (31 characters per row) -> 488,808,000‬ bytes

### Data processing
- Handle nans given by the sensor
- Do we need a secondary smoothing? rolling mean?

### Codebase
- Do profiling to see what takes most time
- Overload [] operator for the SensorData class to return: 
  - ```SensorData[i] = (grid_centre[i], H[i], T[i])``` ?

### Visualisation
- Plot a dashed line with observation carried forward if the last observation is old (older than 2 mins or 1 hour or ...?)
- Show two lines, one for inside and one for outside, with legend
- Label axes, title, units etc
  - xticks

### Fan
- Maybe control fan using raspberry pi, regulate humidity


