# pi-humidity
Repo containing code for pi humidity monitoring

## To-do
- Tidy up graph, labels, titles, etc.
- Do profiling to see what needs speeding up
  - Why does the data take so long to initially load?
  - is dask the problem
- google drive pi backups
- Use a database, MySQL, instead of a csv.
  - Maybe this will have faster loading times and better modularity of storage
  - Build a python module (file) that handles the communication with the MySQL server and DHT tables (an API)
    - This should handle the input of DHT data and the querying of DHT data
      - Make a DHT class that holds a single observation of DHT (datetime, humidity, temperature) which can be used as an input to the SQL_DHT API
    - This should be built to automatically work on the raspi as well, given different inputs to classes/functions

### Other
- Back up an image of the fully configured pi
  - Or docker container?
- Upload the csv file to google drive intermittently
  - rclone or rsync

### Data handling & ingesting
- get MySQL to deal with everything

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


