#!/bin/bash
filename=~/pi-humidity/pi_humidity_dump.sql
#echo $filename
mysqldump pi_humidity -u haydeni0 -praspizeroWH_SQL > ${filename}
rclone copy ${filename} gdrive:Backups/pi-humidity/mysqldump
rm $filename
