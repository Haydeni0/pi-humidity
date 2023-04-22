# How to do backups of a TimescaleDB database

## Back up and restore the entire database using ```pg_dump``` and ```pg_restore```

### Manual steps

> [TimescaleDB docs](https://docs.timescale.com/self-hosted/latest/backup-and-restore/pg-dump-and-restore/)
>
> Run the ```pg_dump``` command inside the database container:
>
>     docker exec pi-humidity-timescaledb /bin/bash -c 'pg_dump -U postgres -Fc -f /db_backups/${POSTGRES_DB}.bak $> {POSTGRES_DB}'
>
> And restore to a new database using ```pg_restore``` (within psql):
>
>     CREATE DATABASE restored_pi_humidity;
>     \c restored_pi_humidity
>     SELECT timescaledb_pre_restore();
>     \! pg_restore -U postgres -Fc -d restored_pi_humidity /db_backups/${POSTGRES_DB}.bak
>     SELECT timescaledb_post_restore();

### Use the script

Run the backup script to dump the database to a file

    ./db_backups/backup_db.bash

Maybe set up a cronjob to do this, and then back up the dump to somewhere safe (e.g., to Google Drive using ```rclone```)
