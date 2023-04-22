# How to do backups of a TimescaleDB database

## Back up and restore the entire database using ```pg_dump```

[TimescaleDB docs](https://docs.timescale.com/self-hosted/latest/backup-and-restore/pg-dump-and-restore/)

Run the ```pg_dump``` command inside the database container:

    docker exec pi-humidity-timescaledb /bin/bash -c 'pg_dump -U postgres -Fc -f /db_dump/${POSTGRES_DB}.bak ${POSTGRES_DB}'

And restore to a new database using ```pg_restore``` (within psql):

    CREATE DATABASE restored_pi_humidity;
    \c restored_pi_humidity
    SELECT timescaledb_pre_restore();
    \! pg_restore -U postgres -Fc -d restored_pi_humidity /db_dump/${POSTGRES_DB}.bak
    SELECT timescaledb_post_restore();