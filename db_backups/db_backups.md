# How to do backups of a TimescaleDB database

## Manual steps

Back up and restore the entire database using ```pg_dump``` and ```pg_restore``` ([TimescaleDB docs](https://docs.timescale.com/self-hosted/latest/backup-and-restore/pg-dump-and-restore/))

Run the ```pg_dump``` command inside the database container:

    docker exec pi-humidity-timescaledb /bin/bash -c 'pg_dump -U postgres -Fc -f /db_backups/${POSTGRES_DB}.bak $> {POSTGRES_DB}'

And restore to a new database using ```pg_restore``` (within psql):

    CREATE DATABASE restored_pi_humidity;
    \c restored_pi_humidity
    SELECT timescaledb_pre_restore();
    \! pg_restore -U postgres -Fc -d restored_pi_humidity /db_backups/${POSTGRES_DB}.bak
    SELECT timescaledb_post_restore();

---

## Use the script

Run the backup script to dump the database to a file

    ./db_backups/dump_db.bash

Or, use the ```rclone``` script (which itself runs ```dump_db.bash```) after doing the setup for ```rclone``` Google Drive backups in the [section below](#rclone-setup)

    ./db_backups/rclone_backup.bash

This script is intended to be run every month using ```cron```:

    0 0 1 * * /absolute/path/to/rclone_backup.bash

---

## rclone setup

Based on [this guide](https://www.howtogeek.com/451262/how-to-use-rclone-to-back-up-to-google-drive-on-linux/), but using a custom Google Drive ```Client ID``` and ```Client secret```:

- Follow [this guide] to get a Google Drive ```Client ID``` and ```Client secret```, required by rclone

Set up ```rclone``` with a Google Drive remote,

    sudo apt update
    sudo apt install rclone
    rclone config

    n/s/q> n
    name> my_gdrive
    Storage> drive

Enter the Google Drive ```Client ID```, e.g. something like:

    client_id> [something].apps.googleusercontent.com

Enter the Google Drive ```Client secret```, e.g. something like:

    client_secret> FHEJFLD-Ac-ocE2jAF229-AjgXRHSdpSJF

Continue, setting the scope and leaving others default

    scope> 1
    root_folder_id> 
    service_account_file>

Don't edit the advanced config

    y/n> n
  
But do use auto config, which will open a browser (or give a link to a webpage) and prompt for a login. Accept all.

    y/n> y

Don't configure as a team drive

    y/n> n

Finish and quit

    y/e/d> y
    e/n/d/r/c/s/q> q
