import datetime
import time
import warnings
from collections import deque
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pandas.core import frame

from database_api import DatabaseApi
import yaml
from psycopg2 import sql
import logging
import math

logger = logging.getLogger("__name__")


@dataclass
class SensorData:
    # Declarations
    db: DatabaseApi
    table_name: str

    _history: datetime.timedelta
    _max_buckets: int
    _bucket_width: datetime.timedelta
    _origin_dtime: datetime.datetime

    _sensors: dict[str, deque]

    _last_bucket: datetime.datetime

    @property
    def history(self):
        return self._history

    @history.setter
    def history(self, new_history: datetime.timedelta):
        # Try to merge this somehow with update() or updateExtend()
        if new_history < self._history:
            # If the history is smaller, we don't need to do anything
            # Values now considered old will be removed with an update
            self._history = new_history
            self.update()
            return
        elif new_history == self._history:
            return

        current_dtime = datetime.datetime.now()
        start = current_dtime - new_history
        end = current_dtime - self._history
        # Leave bucket width the same, but change the max number of buckets
        self._max_buckets = math.ceil(new_history / self._bucket_width)
        self._history = new_history

        sensor_names = self.querySensorNames(start=start, end=end)
        for sensor_name in sensor_names:
            # Just in case an update hasn't already removed old values for the previous history,
            # remove them so the don't overlap with the newly queried data
            while self._sensors[sensor_name][0][0] < end:
                self._sensors[sensor_name].popleft()

            df = self.queryBuckets(
                sensor_name=sensor_name,
                start=start,
                end=end,
                bucket_width=self._bucket_width,
                origin=self._origin_dtime,
            )

            if len(df.index) == 0:
                logger.warning(f"[{sensor_name}] No data...")
                continue

            df.set_index("time_bucket", inplace=True)
            # Just in case of NaN values forward and backward fill NaNs
            df.ffill(inplace=True)
            df.bfill(inplace=True)

            newdata = deque(df.itertuples(index=True, name="SensorDht"))

            if sensor_name not in self._sensors:
                self._sensors[sensor_name] = newdata
                continue

            # Add new data to the right side of the deque
            if self._sensors[sensor_name][0][0] == newdata[-1][0]:
                # If the new time bucket is the same as the old one, just replace it.
                # Stops problems where an extra time bucket is added
                self._sensors[sensor_name][0] = newdata.pop()

            self._sensors[sensor_name].extendleft(newdata)

    def __init__(
        self,
        db: DatabaseApi,
        table_name: str,
        max_buckets: int = 800,
        history: datetime.timedelta = datetime.timedelta(days=2),
    ):
        self.db = db
        self.table_name = table_name

        self._max_buckets = max_buckets
        self._history = history

        # Width of the buckets such that the number of buckets within the history time window is less than the maximum
        self._bucket_width = self._history / self._max_buckets

        # Get a reference origin time so that buckets are aligned relative to this
        current_dtime = datetime.datetime.now()
        self._origin_dtime = current_dtime - self._history
        self._last_bucket = self._origin_dtime

        self._sensors = dict()

        # Update humidity and temperature data for each sensor from the database
        self.update()

    def updateExtend(self, sensor_name: str, current_dtime: datetime.datetime):

        df = self.queryBuckets(
            sensor_name=sensor_name,
            start=self._last_bucket,
            end=current_dtime,
            bucket_width=self._bucket_width,
            origin=self._origin_dtime,
        )

        if len(df.index) == 0:
            logger.warning(f"[{sensor_name}] No data...")
            return

        df.set_index("time_bucket", inplace=True)
        # Just in case of NaN values forward and backward fill NaNs
        df.ffill(inplace=True)
        df.bfill(inplace=True)

        newdata = deque(df.itertuples(index=True, name="SensorDht"))

        if sensor_name not in self._sensors:
            self._sensors[sensor_name] = newdata
            return

        # Add new data to the right side of the deque
        if self._sensors[sensor_name][-1][0] == newdata[0][0]:
            # If the new time bucket is the same as the old one, just replace it.
            # Stops problems where the latest time bucket is added on every update
            self._sensors[sensor_name][-1] = newdata.popleft()

        self._sensors[sensor_name].extend(newdata)

    def update(self):
        current_dtime = datetime.datetime.now()

        sensor_names = self.querySensorNames(start=self._last_bucket, end=current_dtime)

        for sensor_name in sensor_names:
            self.updateExtend(sensor_name=sensor_name, current_dtime=current_dtime)
            # Remove old data
            discard_times_before = current_dtime - self._history
            while self._sensors[sensor_name][0][0] < discard_times_before:
                self._sensors[sensor_name].popleft()

        # Remove sensors with no data
        for key, val in self._sensors.items():
            if len(val) == 0:
                self._sensors.pop(key)

        self._last_bucket = current_dtime

    def queryBuckets(
        self,
        sensor_name: str,
        start: datetime.datetime,
        end: datetime.datetime,
        bucket_width: datetime.timedelta,
        origin: datetime.datetime,
    ) -> pd.DataFrame:

        # Use percentile_cont to get the median within each time bucket
        query = sql.SQL(
            f"""
            SELECT 
                time_bucket(%s, dtime, %s) as time_bucket, 
                percentile_cont(0.5) WITHIN GROUP (ORDER BY humidity) as humidity, 
                percentile_cont(0.5) WITHIN GROUP (ORDER BY temperature) as temperature
            FROM {{table_name}}
            WHERE 
                dtime BETWEEN %s AND %s 
                AND sensor_name=%s
            GROUP BY time_bucket
            ORDER BY time_bucket ASC;
            """
        ).format(table_name=sql.Identifier(self.table_name))

        df = self.db.executeDf(
            query,
            (
                bucket_width,
                origin,
                start,
                end,
                sensor_name,
            ),
        )

        return df

    def querySensorNames(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> tuple[str, ...]:
        """
        Get unique sensors within the table for a specific timeframe.

        Args:
            start (datetime.datetime): Start time to query from
            end (datetime.datetime): End time to query to

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
        result = self.db.execute(query_names, (start, end))

        if result and result[0]:
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

    sensor_data = SensorData(db, full_table_name)

    while True:
        t = time.time()
        sensor_data.update()
        df = pd.DataFrame(sensor_data._sensors["inside"])
        print(df.iloc[:10])
        print(df.iloc[-10:])
        while time.time() - t < 5:
            time.sleep(0.1)
