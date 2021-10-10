# pi-humidity
Repo containing code for pi humidity monitoring

## To-do

### Other
- Back up an image of the fully configured pi
  - Or docker container?
- Upload the csv file to google drive intermittently
  - rclone or rsync

### Data handling & ingesting
- Store one csv per month, as querying a large csv might be difficult
  - One year of data (2 second rate) is 15,768,000 rows (31 characters per row) -> 488,808,000‬ bytes

### Data processing
- NaN handling
- Do smoothing to the data, then take a subset to use less points in the plotting
  - smoothing and interpolating
  - Could do a batch smoothInterp then run a recursive filter?
  - Use the deque's max_length attribute to make sure it doesn't get bloated when adding data?
    - Maybe not, as we still want a certain amount of time history...
  - Do we need a secondary smoothing? rolling mean?

### Codebase
- Do profiling to see what takes most time

### Visualisation
- Plot a dashed line with observation carried forward if the last observation is old (older than 2 mins or 1 hour or ...?)
- Show two lines, one for inside and one for outside, with legend
  - Do this after everything is fully sorted with just one set of lines

### Fan
- Maybe control fan using raspberry pi, regulate humidity


