# pi-humidity
Repo containing code for humidity and temperature logging and monitoring on a raspberry pi zero, using two DHT22 sensors.

## To-do

### Other
- Back up an image of the fully configured pi
  - Or docker container?
- Upload the mysqldump to google drive intermittently
  - rclone or rsync

### Data handling & ingesting

### Data processing
- Handle nans given by the sensor
- do smoothing on the bins, particularly on temperature, as it looks jagged due to low resolution
  - Be able to easily configure smoothness, maybe have it as a class instance variable for both H and T

### Codebase
- General quality testing, especially with data logging, as that shouldn't fail

### Visualisation
- Make linewidths bigger

### Fan
- Maybe control fan using raspberry pi, regulate humidity


