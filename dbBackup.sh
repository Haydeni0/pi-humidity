#!/bin/bash
current_month=`date +"%b"`
filename=~/pi-humidity/pi_humidity_dump_${current_month}.sql
#echo $filename
mysqldump pi_humidity -u haydeni0 -praspizeroWH_SQL > ${filename}
rclone copy ${filename} gdrive:Backups/pi-humidity/mysqldump
rm $filename
