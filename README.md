# pi-humidity
Repo containing code for humidity and temperature logging and monitoring on a raspberry pi zero, using two DHT22 sensors.

Further installation instructions (for me when this eventually breaks) are given in [this guide](raspberrypi_installation.md).

## Use case
Logging and plotting the inside and outside humidity/temperature of an indoor terrarium that houses environment sensitive Nepenthes plants.

The graph is shown on the raspberry pi desktop, and also on a locally hosted website.
The local website is accessible on the internet through the use of a dynamic DNS update service.

### Setup

![Fish tank terrarium setup](Media/FishTankTerrarium.jpg "Fish tank terrarium setup")

### The graph produced

![DHT graph example](Media/DHT_graph_example.png "DHT graph example")


## To-do

### Ideas
- Make a detector that detects when the top door is open (high variance in humidity data)
- Model the humidity/temp relationship between inside and outside, most likely with some sort of differential equation, stochastic pde?

### Other
- When the raspberry pi or install breaks, use a docker container next time that can be easily backed up.

### Database
- Better secure SQL server, password shouldn't be written in code (even though its purely local)

### Data processing
- do smoothing on the bins, particularly on temperature, as it looks jagged due to low resolution
  - Be able to easily configure smoothness, maybe have it as a class instance variable for both H and T

### Codebase
- General quality testing, especially with data logging, as that shouldn't fail

### Visualisation
- ~~Change how many minor ticks are shown based on the amount of history~~
- Change how many major ticks are shown based on the amount of history
  - maybe use weeks instead of days when axis gets too long

### Website
- Use javascript or something to make the image refresh by itself, not refresh the whole page. Ideally only when the a new image is made by the python script.
- https://arstechnica.com/civis/viewtopic.php?t=772329

### Fan
- Maybe control fan using raspberry pi, regulate humidity


