# pi-humidity
Repo containing code for humidity and temperature logging and monitoring on a raspberry pi zero, using two DHT22 sensors.

## To-do

### Other
- Back up an image of the fully configured pi
  - Or docker container?
- Be able to access data from my phone?
  - Maybe instead of something complex, just save an image of the graph every 10 mins or so
  - Host this on a website or something able to be accessed from outside
  - Or just send to google drive

### Data handling & ingesting

### Data processing
- do smoothing on the bins, particularly on temperature, as it looks jagged due to low resolution
  - Be able to easily configure smoothness, maybe have it as a class instance variable for both H and T

### Codebase
- General quality testing, especially with data logging, as that shouldn't fail

### Visualisation
- ~~Change how many minor ticks are shown based on the amount of history~~
- Change how many major ticks are shown based on the amount of history
  - maybe use weeks instead of days when axis gets too long

### Fan
- Maybe control fan using raspberry pi, regulate humidity


