# How to do backups of timescale

## Back up and restore the entire database using ```pg_dump```

[TimescaleDB docs](https://docs.timescale.com/self-hosted/latest/backup-and-restore/pg-dump-and-restore/)

Run a command inside the database container:

    docker exec pi-humidity-timescaledb pg_dump -U postgres -Fc -f /db_dump/dumpfile pi_humidity

And restore to a new database:

    CREATE DATABASE restored_pi_humidity;
    \c restored_pi_humidity
    SELECT timescaledb_pre_restore();
    \! pg_restore -U postgres -Fc -d restored_pi_humidity /db_dump/dumpfile

## Convert from the old mysql dump to postgres

[pgloader](https://pgloader.readthedocs.io/en/latest/intro.html)

[pgloader github](https://github.com/dimitri/pgloader)

    apt-get install pgloader

Better to do it inside their docker container probably

    docker run --rm -it ghcr.io/dimitri/pgloader:latest pgloader --version
