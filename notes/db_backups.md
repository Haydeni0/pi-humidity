# How to do backups of timescale

## Back up and restore the entire database using ```pg_dump```

[TimescaleDB docs](https://docs.timescale.com/self-hosted/latest/backup-and-restore/pg-dump-and-restore/)

Run a command inside the database container:

    docker exec pi-humidity-timescaledb pg_dump -U postgres -Fc -f /db_dump/pi_humidity.bak pi_humidity

And restore to a new database:

    CREATE DATABASE restored_pi_humidity;
    \c restored_pi_humidity
    SELECT timescaledb_pre_restore();
    \! pg_restore -U postgres -Fc -d restored_pi_humidity /db_dump/pi_humidity.bak

