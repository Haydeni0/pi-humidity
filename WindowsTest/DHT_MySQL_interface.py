import datetime
import os
import time
import math
from typing import Tuple

from collections import deque

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

            # Connect a cursor to the server
            self.cursor = self.connection.cursor()
            
            self.cursor.execute("SELECT DATABASE();")
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
            # Closing the cursor throws an error for some reason. This SO answer perhaps shows why, but after
            # following the answer, things are still broken
            # https://stackoverflow.com/a/1482477
            # self.cursor.close() 
            self.connection.close()
            print("_"*100)
            print("MySQL connection closed")

    def getObservations(self, table_name: str, start_dtime: datetime.datetime,
                        end_dtime: datetime.datetime):

        query = f"SELECT dtime, humidity, temperature FROM {table_name} \
            WHERE dtime BETWEEN %s AND %s"

        try:
            self.connection.reconnect() # Reconnect to the server to ensure we get the latest data
            self.cursor.execute(query, (start_dtime, end_dtime))
            observations = self.cursor.fetchall()

            if len(observations) > 0:
                # Convert the list of sequential observations into arrays D, H and T
                z = zip(*observations)
                D = np.array(next(z))
                H = np.array(next(z))
                T = np.array(next(z))
            else:
                D = np.array([])
                H = np.array([])
                T = np.array([])

            return D, H, T

        except Error as err:
            print(err)

    def createTable(self, table_name: str):
        # Function to create a table in DHT format if it doesn't already exist
        try:
            # Don't bother with START TRANSACTION or COMMIT, as CREATE TABLE does an implicit commit
            self.cursor.execute(
                f"CREATE TABLE {table_name} (dtime DATETIME(1) NOT NULL UNIQUE PRIMARY KEY, \
                    humidity FLOAT, temperature FLOAT);"
            )
        except Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print(f"Table {table_name} exists")
            else:
                print(err)

    def sendObservation(self, table_name: str, DHT: ObsDHT):
        # Send a DHT observation to the table in the database
        try:
            self.cursor.execute("START TRANSACTION;")
            self.cursor.execute(
                f"INSERT INTO {table_name} (dtime, humidity, temperature)\
                    VALUES ('{DHT.D}', {DHT.H:0.1f}, {DHT.T: 0.1f});"
            )
            self.cursor.execute("COMMIT;")
        except Error as err:
            print(err)
