#!/bin/bash
filename=~/pi-humidity/pi_humidity_dump_temp.sql
#echo $filename
mysqldump pi_humidity -u haydeni0 -praspizeroWH_SQL > ${filename}

