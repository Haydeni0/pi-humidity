SELECT * FROM dht_inside WHERE dtime >= now() - INTERVAL 2 DAY ORDER BY dtime DESC LIMIT 100;
SELECT * FROM dht_inside WHERE dtime BETWEEN "2021-10-31 01:29:43" AND "2021-10-31 01:29:48" ORDER BY dtime DESC LIMIT 100;
#SELECT * FROM dht_inside ORDER BY dtime ASC LIMIT 50;






SELECT COUNT(humidity) FROM dht_inside;

# Set up replication
FLUSH TABLES WITH READ LOCK;
SHOW MASTER STATUS;
SHOW VARIABLES LIKE "sql_log_bin";

SHOW BINARY LOGS;
SHOW VARIABLES LIKE 'bind_address'; # Should be 0.0.0.0 to allow connections from anywhere

UNLOCK TABLES;