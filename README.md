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
  - Store one csv per month, as querying a large csv might be difficult
    - One year of data (2 second rate) is 15,768,000 rows (31 characters per row) -> 488,808,000‬ bytes
    - 
  - Measure room humidity and temp as well


### Display
- Figure out how to append to the line L_humidity rather than set_xdata...
  - Find some way to benchmark how fast it's working currently
  - https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot
- NaN handling
- Plot a dashed line with observation carried forward if the last observation is old (older than 2 mins or 1 hour or ...?)
- Show two lines, one for inside and one for outside, with legend

### Fan
- Solder fan to a usb so it runs on 5v from usb rather than wall plug 5v transformer
- Or maybe control fan using raspberry pi, regulate humidity


