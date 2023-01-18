import datetime
import logging
import os
from dataclasses import dataclass
from typing import Any

from collections import namedtuple

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extensions
from psycopg2 import Error, errors

logger = logging.getLogger(__name__)


@dataclass
class DhtObservation:
    dtime: datetime.datetime
    humidity: int | float | None
    temperature: int | float | None


# Create a class to hold the connection config to be passed to psycopg2.connect
# Use its _asdict method to be able to use the **mapping operator on it.
ConnectionConfig = namedtuple(
    "ConnectionConfig", ["host", "port", "dbname", "user", "password"]
)


@dataclass(init=False)
class DatabaseApi:
    """
    A sort of API that connects to the DHT table in the MySQL server for easy, high-level access.
    """

    __connection_established: bool
    connection: psycopg2.extensions.connection
    cursor: psycopg2.extensions.cursor
    connection_config: ConnectionConfig

    def __init__(self):
        # Start connection

        self.connection_config = ConnectionConfig(
            host=os.environ.get("POSTGRES_HOST"),
            port=os.environ.get("POSTGRES_PORT"),
            dbname=os.environ.get("POSTGRES_DB"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
        )

        self.__connection_established = True
        # Connect to server and database
        try:
            self.connection = psycopg2.connect(**self.connection_config._asdict())
        except psycopg2.OperationalError:
            # Create database if it doesn't exist
            temp_connection_config = self.connection_config._asdict()
            temp_connection_config["dbname"] = "postgres"
            self.connection = psycopg2.connect(**temp_connection_config)
            pg_db = os.environ.get("POSTGRES_DB")
            self.cursor.execute(
                f"SELECT 'CREATE DATABASE {pg_db}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{pg_db}')\\gexec"
            )
            self.connection.close()

            # Reconnect to the server and correct database
            self.connection = psycopg2.connect(**self.connection_config._asdict())

        # Connect a cursor to the server
        self.cursor = self.connection.cursor()

        logger.debug(f"Connected to database: {self.version()}")
        dbname = self.execute("SELECT current_database();")[0][0]
        logger.debug(f"Connected to database: {dbname}")

    def __del__(self):
        # Close the server connection when instance is destroyed
        # Only if the connection was successful
        if self.__connection_established:
            self.cursor.close()
            self.connection.close()
            logger.debug(f"Connection closed ({datetime.datetime.now()})")

    def execute(
        self, query: str, parameters: tuple[Any, ...] = (), raise_errors: bool = True
    ) -> list[tuple[Any, ...]]:
        """Execute and commit a query

        Args:
            query (str): SQL query
            parameters (tuple[Any, ...], optional): Tuple containing parameters if used in the query. Defaults to ().
            raise_errors (bool, optional): Set False to ignore errors. Defaults to True.

        Returns:
            list[tuple[Any, ...]]: List of records returned by the executed statement.
        """

        result = [()]
        try:
            self.beginTransaction()

            self.cursor.execute(query, parameters)
            if self.cursor.description is not None:
                result = self.cursor.fetchall()

            self.commit()
        except errors.InFailedSqlTransaction as err:
            logger.error(err)
            raise err
        except Error as err:
            logger.error(err)
            if raise_errors:
                raise err

        return result

    def executeDf(self, *args, **kwargs) -> pd.DataFrame:
        """The same as execute, but returns the results in the form of a pandas DataFrame

        Returns:
            pd.DataFrame: Result of the query
        """
        result = self.execute(*args, **kwargs)
        desc = self.cursor.description
        if desc is not None:
            colnames = [col[0] for col in desc]
        else:
            colnames = []

        df = pd.DataFrame(result, columns=colnames)

        return df

    def beginTransaction(self):
        try:
            self.cursor.execute("BEGIN TRANSACTION;")
        except Error as err:
            logger.error(err)

    def commit(self):
        try:
            self.connection.commit()
        except Error as err:
            logger.error(err)

    def rollback(self):
        try:
            self.connection.rollback()
        except Error as err:
            logger.error(err)

    def version(self):
        return self.execute("SELECT version();")[0][0]

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

    def createSchema(
        self,
        schema_name: str,
        force_replace: bool = False,
        user_authorization: str | None = None,
    ):
        """Create a database schema

        Args:
            schema_name (str): Name of the schema to create
            force_replace (bool, optional): If this is True, then if a schema of the same name exists it
                will be deleted and replaced. Otherwise, nothing happens. Defaults to False.
            user_authorization (str | None, optional): If a user is given, assign the schema to them.
        """

        if user_authorization is not None:
            suffix = f" AUTHORIZATION {user_authorization}"
        else:
            suffix = ""

        if not force_replace:
            self.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}{suffix};")
        else:
            self.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            self.execute(f"CREATE SCHEMA {schema_name}{suffix};")

    def createDhtTable(self, table_name: str):
        # Function to create a table in the correct format if it doesn't already exist
        self.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                dtime timestamp NOT NULL,
                sensor_name varchar(32) NOT NULL,
                humidity float8, 
                temperature float8,

                PRIMARY KEY (dtime, sensor_name)
            );
            """
        )
        self.execute(
            f"""
            SELECT create_hypertable(
                '{table_name}', 'dtime', if_not_exists => TRUE
            );
            """
        )

    def sendObservation(
        self, table_name: str, sensor_name: str, dht: DhtObservation, *, ignore_insert_error: bool = False
    ):
        # Send a DHT observation to the table in the database
        if ignore_insert_error:
            # Ignore insertion errors if specified
            ignore = "IGNORE"
        else:
            ignore = ""

        if dht.humidity is not None:
            humidity = f"{dht.humidity:0.1f}"
        else:
            humidity = "NULL"
        if dht.temperature is not None:
            temperature = f"{dht.temperature:0.1f}"
        else:
            temperature = "NULL"

        self.execute(
            f"""
            INSERT {ignore} INTO {table_name} 
            (dtime, sensor_name, humidity, temperature)
            VALUES ('{dht.dtime}', '{sensor_name}', {humidity}, {temperature});
            """
        )

    def size(self, human_readable: bool = True):
        # Get total size of the connected database (in MB)
        try:
            if human_readable:
                result = self.execute(
                    f"SELECT pg_size_pretty( pg_database_size('{self.connection.info.dbname}'));"
                )
            else:
                result = self.execute(
                    f"SELECT pg_database_size('{self.connection.info.dbname}');"
                )
            return result[0][0]
        except Error as err:
            logger.error(err)

    @staticmethod
    def joinNames(schema_name: str | None, table_name: str):
        assert table_name, f"Cannot join table name '{table_name}'"
        if schema_name:
            return f"{schema_name}.{table_name}"
        else:
            return table_name


if __name__ == "__main__":
    dht_connection = DatabaseApi()

    random_dht = DhtObservation(
        datetime.datetime.now(), np.random.normal(1), np.random.normal(1)
    )

    dht_connection.createDhtTable("test")
    dht_connection.sendObservation("test", sensor_name="testsensor", dht=random_dht)
