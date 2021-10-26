# pi-humidity
Repo containing code for humidity and temperature logging and monitoring on a raspberry pi zero, using two DHT22 sensors.

## To-do
- Set up mysql server on pi
  - Be able to connect to it and query from it using the PC
- Put the grid_edges into the DHT sensor data class as a static variable rather than instance
- Tidy up graph, labels, titles, etc.
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
- Potentially, the data could be grouped into bins and smoothed by sql before being put into python

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


