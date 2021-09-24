# pi-humidity
Repo containing code for pi humidity monitoring



## To-do

### Other
- Back up an image of the fully configured pi
- Get git working to back up things
- Upload the csv file to google drive intermittently
  - rclone or rsync

### Humidity monitoring
- Do filtering of the data?
  - Maybe not, as it can be done in post
  - Run logger in background at launch
  - Be able to easily access certain times
    - What datastructures do I need... will csv do?
    - Maybe store one csv per week, as querying a large csv might be difficult


### Display
- Pull data from the last two days to display on screen
- Figure out how to do that...

### Fan
- Solder fan to a usb so it runs on 5v from usb rather than buck converter
- Or maybe control fan using raspberry pi, regulate humidity


