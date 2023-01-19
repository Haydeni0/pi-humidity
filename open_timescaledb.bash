#!/bin/bash
# Shortcut file to write this command
# Open TimescaleDB database in the container
docker exec -it pi-humidity-timescaledb /bin/bash -c 'psql -U postgres -d ${POSTGRES_DB}'