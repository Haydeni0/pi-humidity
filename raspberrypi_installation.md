
# A sort of guide to how the raspberry pi had been set up
I can't really remember, this is written after I fully set up everything. I'll write down what I think I did in the correct ish order, along with some links to the tutorials if possible.

### Useful tools on secondary computer
- Git
  - Sourcetree
- Filezilla
- VS Code
- PuTTY
  - Pageant, puttygen for ssh keys

### Ordered guide

1. Install raspberry pi OS
2. Add SSH capabilities (to login remotely)
   1. Use an [ssh key](https://pimylifeup.com/raspberry-pi-ssh-keys/) to log in automatically
   2. Configure that with PuTTY
3. ```sudo apt-get update``` and ```sudo apt-get upgrade```
4. Install python3 and packages, update the required ones to the latest versions
5. Install [git](https://projects.raspberrypi.org/en/projects/getting-started-with-git)
   1. Also use an ssh key, as my account requires one
6. Install python and required modules
   1. Includeing the [DHT22](https://pimylifeup.com/raspberry-pi-humidity-sensor-dht22/) humidity sensor stuff
7. Install [MySQL](https://pimylifeup.com/raspberry-pi-mysql/)
   1. Set options in the config file to allow [external connections](https://howtoraspberrypi.com/enable-mysql-remote-connection-raspberry-pi/) and database replication: 

            [mysqld]
            server-id=21 # Two servers can't have the same server id, default is 1
            log_bin = /var/log/mysql/mysql-bin.log # Enable binary logging for replication
            bind_address = 0.0.0.0 # Allow the server to check for external connections (using the default port 3306)
    1. Set up [replication](https://www.digitalocean.com/community/tutorials/how-to-set-up-replication-in-mysql) to a different pc
    2. Set up monthly mysqldump database backups to google drive using rclone (contained in dbBackup.sh, and put on a monthly cronjob)
        

8. Use a cronjob at reboot to start the data logging python script
   1. Optionally, get it to forward the output to a file just in case an error is raised
9.  Use the [autostart](https://learn.sparkfun.com/tutorials/how-to-run-a-raspberry-pi-program-on-startup/method-2-autostart) folder ```/home/pi/.config/autostart``` with a ```dhtPlotting.desktop``` file to start the python script once the desktop has loaded.
10. Install package ```unclutter``` to get rid of idle mouse cursor, run on desktop load in the same manner as the python plotter
