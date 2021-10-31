USE pi_humidity;
SELECT * FROM dht_inside WHERE dtime >= now() - INTERVAL 2 DAY ORDER BY dtime DESC LIMIT 100;

# How many data points are in the last time period
SELECT COUNT(A.dtime) FROM (SELECT * FROM dht_inside WHERE dtime >= now() - INTERVAL 1 MINUTE) AS A;


SHOW SLAVE STATUS;

STOP REPLICA;
START REPLICA;

# To ignore errors
SET GLOBAL SQL_REPLICA_SKIP_COUNTER = 10;

SHOW VARIABLES LIKE "server_id";
SHOW VARIABLES LIKE "sql_log_bin";

SHOW BINARY LOGS;

CHANGE REPLICATION SOURCE TO
SOURCE_HOST='192.168.1.46',
SOURCE_USER='repl',
SOURCE_PASSWORD='raspizeroWH_REPLICA',
SOURCE_LOG_FILE='mysql-bin.000005',
SOURCE_LOG_POS=648460;


USE test_pi_humidity;
SELECT * FROM dht_inside;
#INSERT IGNORE INTO dht_inside (dtime, humidity, temperature) VALUES ("2021-10-16 13:41:32.8","79.9","20");