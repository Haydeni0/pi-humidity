import datetime
import time
import warnings
from collections import deque
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from pandas.core import frame

from database_api import DatabaseApi
from utils import timing
import yaml
from psycopg2 import sql
import logging

logger = logging.getLogger("__name__")

@dataclass
class SensorDht:
    name: str
    data: pd.DataFrame = pd.DataFrame()

    # Hash implementation from https://stackoverflow.com/a/2909119
    def __key(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other) -> bool:
        if isinstance(other, SensorDht):
            return self.__key() == other.__key()
        return NotImplemented


@dataclass
class SensorData:
    # Declarations
    db: DatabaseApi
    table_name: str

    sensor_history: datetime.timedelta
    num_bins: int
    grid_frequency: datetime.timedelta

    sensors: list[SensorDht]

    last_updated: datetime.datetime

    def __init__(
        self,
        db: DatabaseApi,
        table_name: str,
        num_bins: int = 800,
        sensor_history: datetime.timedelta = datetime.timedelta(minutes=200),
    ):
        self.db = db
        self.table_name = table_name
        self.num_bins = num_bins
        self.sensor_history = sensor_history

        # Frequency that bins within the grid occur at
        self.grid_frequency = (sensor_history / num_bins)  

        # Update humidity and temperature data for each sensor from the database
        self.update()
        pass

    def update(self):
        current_dtime = datetime.datetime.now()
        start_dtime = current_dtime - self.sensor_history

        self.sensors = self.loadData(start_dtime=start_dtime, end_dtime=current_dtime)
        self.last_updated = current_dtime

    def loadData(
        self, start_dtime: datetime.datetime, end_dtime: datetime.datetime
    ) -> list[SensorDht]:
        sensors = []
        sensor_names = self.getSensorNames(start_dtime, end_dtime)
        for sensor_name in sensor_names:
            # Load from the database
            logger.debug(f"({sensor_name}) Start")
            df = self.getObservations(sensor_name, start_dtime, end_dtime)
            logger.debug(f"({sensor_name}) Queried")

            # Strange error where df is sometimes empty, not sure why atm
            if len(df) == 0:
                logger.error("Dataframe is empty...")
                continue
            if "dtime" not in df.columns:
                logger.error("Dataframe doesn't have dtime...")
                continue

            df.set_index("dtime", inplace=True)

            df.fillna(method="ffill", inplace=True)
            # Group data for each period in time, and aggregate by median
            df_grouped = df.groupby(pd.Grouper(level="dtime", freq=self.grid_frequency))
            df = df_grouped[["humidity", "temperature"]].agg("median")
            logger.debug(f"({sensor_name}) Grouped")

            # Realign the data with regular indices, and a fixed amount of points
            bin_dtimes = pd.date_range(start_dtime, end_dtime, periods=self.num_bins)
            df = df.reindex(bin_dtimes, method="ffill")
            logger.debug(f"({sensor_name}) Reindexed")

            # This reindexing will create NaNs if we are missing data from the beginning
            # Backfill them with real values
            df.fillna(method="bfill", inplace=True)

            # Check, just in case
            assert len(df.index) == self.num_bins

            sensors.append(SensorDht(name=sensor_name, data=df))

        return sensors



    def getObservations(
        self,
        sensor_name: str,
        start_dtime: datetime.datetime,
        end_dtime: datetime.datetime,
    ) -> pd.DataFrame:
        """Query the database for DHT observations between two times

        Args:
            start_dtime (datetime.datetime): Start time to query from
            end_dtime (datetime.datetime): End time to query to

        Returns:
            pd.DataFrame: Query result
        """

        query_data = sql.SQL(
            f"""
            SELECT dtime, humidity, temperature 
                FROM {{table_name}}
                WHERE 
                    dtime BETWEEN %s AND %s 
                    AND sensor_name=%s
                ORDER BY dtime DESC;
            """
        ).format(table_name=sql.Identifier(self.table_name))

        df = self.db.executeDf(query_data, (start_dtime, end_dtime, sensor_name))

        return df

    def getSensorNames(
        self,
        start_dtime: datetime.datetime,
        end_dtime: datetime.datetime,
    ) -> tuple[str, ...]:
        """
        Get unique sensors within the table for a specific timeframe.
        It's probably quicker to do this in SQL than using pandas.

        Args:
            start_dtime (datetime.datetime): Start time to query from
            end_dtime (datetime.datetime): End time to query to

        Returns:
            pd.DataFrame: Query result
        """

        query_names = sql.SQL(
            f"""
            SELECT DISTINCT sensor_name
                FROM {{table_name}}
                WHERE dtime BETWEEN %s AND %s;
        """
        ).format(table_name=sql.Identifier(self.table_name))
        result = self.db.execute(query_names, (start_dtime, end_dtime))


        if result[0]:
            unique_sensors = tuple([_[0] for _ in result])
            return unique_sensors
        else:
            return ()

        


if __name__ == "__main__":
    db = DatabaseApi()

    with open("/shared/config.yaml", "r") as f:
        config: dict = yaml.load(f, yaml.Loader)

    schema_name = config["schema_name"]
    table_name = config["table_name"]
    full_table_name = db.joinNames(schema_name, table_name)

    SensorData(db, full_table_name)
