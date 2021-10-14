# pi-humidity
Repo containing code for pi humidity monitoring

## To-do
- Add datetime grid feature
  - Colour previously missing observations red

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
- Instead of keeping all the data dependent on the date D, make a regular 1-D grid of datetime with a set length (e.g. 1000 elements) spanning from current_time - history_timedelta to current_time
  - Should the grid length be reduced if there are too few datapoints? E.g. if num_grid == 1000 but len(D_bulk == 400 ish)
  - Do we need a secondary smoothing? rolling mean?

### Codebase
- Do profiling to see what takes most time
- Make class methods private that shouldnt be called outside of the class
- Overload [] operator for the SensorData class to return: 
  - ```SensorData[i] = (grid_centre[i], H[i], T[i])``` ?

### Visualisation
- Plot a dashed line with observation carried forward if the last observation is old (older than 2 mins or 1 hour or ...?)
- Show two lines, one for inside and one for outside, with legend
  - Do this after everything is fully sorted with just one set of lines

### Fan
- Maybe control fan using raspberry pi, regulate humidity


