import datetime
import logging
import os
from dataclasses import dataclass

import numpy as np
import psycopg2
import psycopg2.extensions

logger = logging.getLogger(__name__)


@dataclass
class ObsDHT:
    D: datetime.datetime
    H: float
    T: float


@dataclass(init=False)
class DHTConnection:
    """
    A sort of API that connects to the DHT table in the MySQL server for easy, high-level access.
    """

    __connection_established: bool
    connection: psycopg2.extensions.connection
    cursor: psycopg2.extensions.cursor

    def __init__(self):
        # Start connection

        connection_config = {
            "host": os.environ.get("POSTGRES_HOST"),
            "port": os.environ.get("POSTGRES_PORT"),
            "dbname": os.environ.get("POSTGRES_DB"),
            "user": os.environ.get("POSTGRES_USER"),
            "password": os.environ.get("POSTGRES_PASSWORD"),
        }

        self.__connection_established = True
        # Connect to server and database
        try:
            self.connection = psycopg2.connect(**connection_config)
        except psycopg2.OperationalError:
            # Create database if it doesn't exist
            connection_config["dbname"] = "postgres"
            self.connection = psycopg2.connect(**connection_config)
            pg_db = os.environ.get("POSTGRES_DB")
            self.cursor.execute(f"SELECT 'CREATE DATABASE {pg_db}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{pg_db}')\\gexec")
            self.connection.close()

            # Reconnect to the server and correct database
            connection_config["dbname"] = pg_db
            self.connection = psycopg2.connect(**connection_config)
            
        # Connect a cursor to the server
        self.cursor = self.connection.cursor()

        self.cursor.execute("SELECT version();")
        record = self.cursor.fetchall()
        print("Connected to database: ", record[0][0])
        print("=" * 100)

    def __del__(self):
        # Close the server connection when instance is destroyed
        # Only if the connection was successful
        if self.__connection_established:
            # Closing the cursor throws an error for some reason. This SO answer perhaps shows why, but after
            # following the answer, things are still broken
            # https://stackoverflow.com/a/1482477
            # self.cursor.close()
            self.connection.close()
            print("_" * 100)
            print(f"Connection closed ({datetime.datetime.now()})")

    def getObservations(
        self,
        table_name: str,
        start_dtime: datetime.datetime,
        end_dtime: datetime.datetime,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Query the database for DHT observations between two times
        # Return D, H and T separately as arrays
        query = f"""
            SELECT dtime, humidity, temperature 
                FROM {table_name}
                WHERE dtime BETWEEN %s AND %s
                ORDER BY dtime DESC;
            """

        try:
            # Reconnect to the server to ensure we get the latest data
            # self.connection.reconnect()
            self.cursor.execute(query, (start_dtime, end_dtime))
            observations = self.cursor.fetchall()

            if len(observations) > 0:
                # Convert the list of sequential observations into arrays D, H and T
                z = zip(*observations)
                D = np.array(next(z))
                H = np.array(next(z))
                T = np.array(next(z))
                # Replace None values with nan so they can be handled more easily
                H[H == np.array(None)] = np.nan
                T[T == np.array(None)] = np.nan
            else:
                D = np.array([])
                H = np.array([])
                T = np.array([])

            return D, H, T

        except psycopg2.Error as err:
            print(err)
            return np.array([]), np.array([]), np.array([])

    def createSchema(self, schema_name: str):
        # Function to create a schema if it doesn't already exist
        self.beginTransaction()
        self.cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        self.commit()

    def createTable(self, table_name: str):
        # Function to create a table in DHT format if it doesn't already exist
        self.beginTransaction()
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (dtime timestamp NOT NULL UNIQUE PRIMARY KEY, \
                humidity float8, temperature float8);"
        )
        self.cursor.execute(
            f"SELECT create_hypertable('{table_name}', 'dtime', if_not_exists => TRUE)"
        )
        self.commit()

    def beginTransaction(self):
        self.cursor.execute("BEGIN TRANSACTION;")

    def commit(self):
        self.cursor.execute("COMMIT;")

    def sendObservation(
        self, table_name: str, DHT: ObsDHT, *, ignore_insert_error: bool = False
    ):
        # Send a DHT observation to the table in the database
        if ignore_insert_error:
            # Ignore insertion errors if specified
            ignore = "IGNORE"
        else:
            ignore = ""

        if DHT.H is not None:
            H = f"{DHT.H:0.1f}"
        else:
            H = "NULL"
        if DHT.T is not None:
            T = f"{DHT.T:0.1f}"
        else:
            T = "NULL"

        try:
            self.beginTransaction()
            self.cursor.execute(
                f"INSERT {ignore} INTO {table_name} (dtime, humidity, temperature)\
                    VALUES ('{DHT.D}', {H}, {T});"
            )
            self.commit()
        except psycopg2.Error as err:
            print(err)
            self.commit()


if __name__ == "__main__":
    dht_connection = DHTConnection()

    random_dht = ObsDHT(
        datetime.datetime.now(), np.random.normal(1), np.random.normal(1)
    )

    dht_connection.createTable("test")
    dht_connection.sendObservation("test", random_dht)
