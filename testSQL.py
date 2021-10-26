import datetime
from typing import Tuple

import numpy as np

import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "haydeni0",
    "password": "raspizeroWH_SQL",
    'raise_on_warnings': True
}

try:
    connection_established = True
    # Connect to server and database
    connection = mysql.connector.connect(**connection_config)
    db_Info = connection.get_server_info()
    print("Connected to MySQL Server version ", db_Info)

    # Connect a cursor to the server
    cursor = connection.cursor()

    cursor.execute("SELECT DATABASE();")
    record = cursor.fetchone()
    print("Connected to database: ", record[0])
    print("="*100)

except Error as err:
    connection_established = False
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
