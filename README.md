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
- Speed up plotting, currently very very slow
  - blit technique https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot
    - Probably not that useful as we need to draw the changing x ticks as well, pretty much everything
  - Could do smoothing to the data, then take a subset to use less points in the plotting
    - smoothing and interpolating
    - Could do a batch smoothInterp then run a recursive filter?
  - Could try a method that only plots D_end, H_end, T_end, and just shifts the x limits without redrawing the whole thing
- NaN handling
- Plot a dashed line with observation carried forward if the last observation is old (older than 2 mins or 1 hour or ...?)
- Show two lines, one for inside and one for outside, with legend
  - Do this after everything is fully sorted with just one set of lines
- Do profiling to see what takes most time
- Use a list for loading and initialisation, then after interpolating use a deque

### Fan
- Solder fan to a usb so it runs on 5v from usb rather than wall plug 5v transformer
- Or maybe control fan using raspberry pi, regulate humidity


