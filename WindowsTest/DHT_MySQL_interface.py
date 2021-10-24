import datetime
import os
import time
import math
from typing import Tuple

import numpy as np
import pandas as pd

import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

class ObsDHT:
    def __init__(self, D: datetime.datetime, H: float, T: float):
        self.D = D
        self.H = H
        self.T = T


class ConnectDHTSQL:
    def __init__(self, connection_config, raise_connection_errors=False):
        # Example connection config
        """
        connection_config = {
        "host": 'localhost',
        "database": "pi_humidity",
        "user": "Haydeni0",
        "password": "OSzP34,@H0.I2m$sZpI<",
        'raise_on_warnings': True
        }
        """
        # Start connection
        try:
            self.__connection_established = True
            # Connect to server and database
            self.connection = mysql.connector.connect(**connection_config)

            db_Info = self.connection.get_server_info()
            print("Connected to MySQL Server version ", db_Info)
            self.cursor = self.connection.cursor()
            self.cursor.execute("select database();")
            record = self.cursor.fetchone()
            print("Connected to database: ", record[0])
            print("="*100)

        except Error as err:
            self.__connection_established = False
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
            
            if raise_connection_errors:
                raise(err)

    def __del__(self):
        # Close the server connection when instance is destroyed
        # Only if the connection was successful
        if self.__connection_established:
            self.connection.close()
            print("_"*100)
            print("MySQL connection closed")
    
    def createTable(self, TABLE_NAME):
        # Function to create a table in DHT format if it doesn't already exist
        try:
            # Don't bother with START TRANSACTION or COMMIT, as CREATE TABLE does an implicit commit
            self.cursor.execute(
                f"CREATE TABLE {TABLE_NAME} (dtime DATETIME(1) NOT NULL UNIQUE PRIMARY KEY, \
                    humidity FLOAT, temperature FLOAT);"
            )
        except Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print(f"Table {TABLE_NAME} exists")
            else:
                print(err)
    
    def sendObservation(self, TABLE_NAME, DHT: ObsDHT):
        try:
            self.cursor.execute("START TRANSACTION;")
            self.cursor.execute(
                f"INSERT INTO {TABLE_NAME} (dtime, humidity, temperature)\
                    VALUES ('{DHT.D}', {DHT.H:0.1f}, {DHT.T: 0.1f});"
            )
            self.cursor.execute("COMMIT;")
        except Error as err:
            print(err)
            



