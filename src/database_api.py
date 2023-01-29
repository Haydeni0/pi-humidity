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
from psycopg2 import Error, errors, sql

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
            self.execute(
                f"SELECT 'CREATE DATABASE {pg_db}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{pg_db}')\\gexec"
            )
            self.connection.close()

            # Reconnect to the server and correct database
            self.connection = psycopg2.connect(**self.connection_config._asdict())

        logger.debug(f"Connected to server: {self.version()}")
        dbname = self.execute("SELECT current_database();")[0][0]
        logger.debug(f"Connected to database: {dbname}")

    def __del__(self):
        # Close the server connection when instance is destroyed
        if not self.connection.closed:
            self.connection.close()
            logger.debug(f"Connection closed ({datetime.datetime.now()})")

    # Context manager
    def __enter__(self):
        return DatabaseApi()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def _execute(
        self,
        cursor: psycopg2.extensions.cursor,
        query: str | sql.Composed,
        parameters: tuple[Any, ...] = (),
    ) -> list[tuple[Any, ...]]:
        """Execute and commit a query

        Args:
            cursor (psycopg2.extensions.cursor): Database cursor
            query (str): SQL query
            parameters (tuple[Any, ...], optional): Tuple containing parameters if used in the query. Defaults to ().

        Returns:
            list[tuple[Any, ...]]: List of records returned by the executed statement.
        """

        result = []
        try:
            cursor.execute(query, parameters)
            # How to properly check if results exist and we aren't going to get a "psycopg2.ProgrammingError: no results to fetch" error?
            # results_exist = cursor.rowcount >= 0 and cursor.description is not None
            results_exist = cursor.pgresult_ptr is not None
            if results_exist:
                result = cursor.fetchall()

            self.commit()
        except errors.InFailedSqlTransaction as err:
            logger.error(err)
            logger.debug("Rolling back...")
            self.rollback()
            raise err
        except Error as err:
            logger.error(err)
            logger.debug("Rolling back...")
            self.rollback()
            raise err

        return result

    def execute(
        self,
        query: str | sql.Composed,
        parameters: tuple[Any, ...] = (),
    ) -> list[tuple[Any, ...]]:
        """Execute and commit a query

        Args:
            query (str): SQL query
            parameters (tuple[Any, ...], optional): Tuple containing parameters if used in the query. Defaults to ().

        Returns:
            list[tuple[Any, ...]]: List of records returned by the executed statement.
        """
        with self.connection.cursor() as cursor:
            return self._execute(cursor, query, parameters)

    def executeDf(
        self,
        query: str | sql.Composed,
        parameters: tuple[Any, ...] = (),
    ) -> pd.DataFrame:
        """The same as execute, but returns the results in the form of a pandas DataFrame

        Args:
            query (str): SQL query
            parameters (tuple[Any, ...], optional): Tuple containing parameters if used in the query. Defaults to ().

        Returns:
            pd.DataFrame: Result of the query
        """
        with self.connection.cursor() as cursor:
            result = self._execute(cursor, query, parameters)
            desc = cursor.description

        if desc is not None:
            colnames = [col[0] for col in desc]
        else:
            colnames = []

        df = pd.DataFrame(result, columns=colnames)

        return df

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
        self,
        table_name: str,
        sensor_name: str,
        dht: DhtObservation,
        *,
        ignore_insert_error: bool = False,
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

        query = sql.SQL(
            f"""
            INSERT {ignore} INTO {{table_name}} 
            (dtime, sensor_name, humidity, temperature)
            VALUES (%s, %s, %s, %s);
            """
        ).format(table_name=sql.Identifier(table_name))

        self.execute(query, (dht.dtime, sensor_name, humidity, temperature))

    def size(self, human_readable: bool = True):
        # Get total size of the connected database (in MB)
        try:
            if human_readable:
                query = sql.SQL(
                    "SELECT pg_size_pretty( pg_database_size({dbname}));"
                ).format(dbname=sql.Literal(self.connection.info.dbname))
            else:
                query = sql.SQL("SELECT pg_database_size({dbname});").format(
                    dbname=sql.Literal(self.connection.info.dbname)
                )

            result = self.execute(query)
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

# >>> Development testing >>>

def test1():
    db = DatabaseApi()

    random_dht = DhtObservation(
        datetime.datetime.now(), np.random.normal(1), np.random.normal(1)
    )

    db.createDhtTable("test")
    db.sendObservation("test", sensor_name="testsensor", dht=random_dht)

def test2():
    with DatabaseApi() as db:
        db.connection.close()
    

if __name__ == "__main__":
    test2()
