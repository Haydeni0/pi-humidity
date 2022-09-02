# pi-humidity
Repo containing code for humidity and temperature logging and monitoring on a (very performance limited) Raspberry Pi Zero WH, using two DHT22 sensors.

Plots are displayed on a display connected to the Pi Zero and is done using an easy to run python script, as the Zero can barely open a browser.

Raspberry pi setup installation instructions (for me when the pi/microSD eventually breaks) are given in [this guide](raspberrypi_installation.md).

## Use case
Logging and plotting the inside and outside humidity/temperature of an indoor terrarium that houses environment sensitive Nepenthes plants.

The graph is shown on the raspberry pi desktop, and also on a locally hosted website.
The local website is accessible on the internet through the use of a dynamic DNS update service.

### Setup

![Fish tank terrarium setup](Media/FishTankTerrarium.jpg "Fish tank terrarium setup")

### The graph

![DHT graph example](Media/DHT_graph_example.png "DHT graph example")

---

## Files
### Data logging
Run ```dhtLogger.py``` at boot, configured to the local SQL server and DHT22 sensors.

### Plotting
The file ```dhtPlotting.py``` contains the plotting code.
Run this on secondary PC to debug (as raspizeroWH is very slow), set the config inside here to point at the replica SQL server for fast querying.

Run ```plotRaspiDHT.py``` at desktop startup on the rpi. The SQL server config should point to the local server.

### MySQL server backups
The bash scripts ```dbBackup.sh``` and ```send_mysqldump.sh``` use rclone to backup to google drive.

### Other
```DHTutils.py```
- Utility code for reading sensors

```DHT_MySQL_interface.py```
- Module containing MySQL API

```Sensors.py```
- Module containing class to handle data pulled from the server.

```html/```
- Directory containing basic website

---

## To-do
- Make it all docker integrated so it's really easy and reliable to set up (once I have access to a more powerful pi4)
  - Web app inside docker mapped to port 80
  - set up a mysql or postgreSQL server inside the container
  - How to get it to display onto the attached monitor?
    - Maybe just from a browser on the pi

### Ideas
- Make a detector that detects when the top door is open (high variance in humidity data)
- Model the humidity/temp relationship between inside and outside, most likely with some sort of differential equation, stochastic pde?

### Other
- When the raspberry pi or install breaks, use a docker container next time that can be easily backed up.

### Database
- Better secure SQL server, password shouldn't be written in code (even though its purely local)
  - Use an ini file with an ini reader module in python

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


