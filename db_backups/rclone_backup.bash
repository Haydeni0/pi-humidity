#!/bin/bash

GDRIVE_PATH=/backups/pi-humidity/

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ENV_FILE=$SCRIPT_DIR/../postgres.env
DB_NAME=$(cat $ENV_FILE | grep -Po "(?<=POSTGRES_DB\=)[\w\d]+")

# Make a database dump
$SCRIPT_DIR/dump_db.bash # > /dev/null 2>&1

# Use the week number to provide a weekly backup solution that overwrites itself after a year
WEEK_NUMBER_ISO=`date +"%V"`
DUMP_PATH=$SCRIPT_DIR/$DB_NAME.bak
NEW_DUMP_PATH=$SCRIPT_DIR/${DB_NAME}_week$WEEK_NUMBER_ISO.bak

# Rename it temporarily
mv $DUMP_PATH $NEW_DUMP_PATH

echo Copying \"$NEW_DUMP_PATH\" to \"my_gdrive:$GDRIVE_PATH\"
/usr/bin/rclone copy \
    --contimeout 60s --timeout 300s --retries 3 --low-level-retries 10 --stats 1s \
    "$NEW_DUMP_PATH" "my_gdrive:$GDRIVE_PATH"

# Restore the original name
mv $NEW_DUMP_PATH $DUMP_PATH