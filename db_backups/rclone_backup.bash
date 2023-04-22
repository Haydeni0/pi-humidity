#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ENV_FILE=$SCRIPT_DIR/../postgres.env
DB_NAME=$(cat $ENV_FILE | grep -Po "(?<=POSTGRES_DB\=)[\w\d]+")

CURRENT_MONTH=`date +"%b"`

# Make a database dump
$SCRIPT_DIR/dump_db.bash # > /dev/null 2>&1

DUMP_PATH=$SCRIPT_DIR/$DB_NAME.bak
NEW_DUMP_PATH=$SCRIPT_DIR/${DB_NAME}_$CURRENT_MONTH.bak

# Rename it temporarily
mv $DUMP_PATH $NEW_DUMP_PATH

echo Copying \"$NEW_DUMP_PATH\" to \"my_gdrive:/backups/pi-humidity/\"
/usr/bin/rclone copy \
    --contimeout 60s --timeout 300s --retries 3 --low-level-retries 10 --stats 1s \
    "$NEW_DUMP_PATH" "my_gdrive:/backups/pi-humidity/"

# Restore the original name
mv $NEW_DUMP_PATH $DUMP_PATH