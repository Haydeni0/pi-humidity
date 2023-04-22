#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ENV_FILE=$SCRIPT_DIR/../postgres.env
DB_NAME=$(cat $ENV_FILE | grep -Po "(?<=POSTGRES_DB\=)[\w\d]+")

# Run the pg_dump command inside the timescaledb container
# This backs up the database to a .bak file here
echo Backing up database $DB_NAME...
docker exec pi-humidity-timescaledb /bin/bash -c \
    'pg_dump -U postgres -Fc -f /db_backups/${POSTGRES_DB}.bak ${POSTGRES_DB}' > /dev/null 2>&1
# Reset permissions for outside the container
docker exec pi-humidity-timescaledb /bin/bash -c 'chmod 666 /db_backups/${POSTGRES_DB}.bak'
echo Backup written to $(realpath $SCRIPT_DIR/$DB_NAME.bak)
echo
echo For information on restoring the backup, read $(realpath $SCRIPT_DIR/../notes/db_backups.md) 
echo or the TimescaleDB docs: https://docs.timescale.com/self-hosted/latest/backup-and-restore/pg-dump-and-restore/