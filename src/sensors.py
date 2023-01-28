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

    _last_updated: datetime.datetime

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
        self._bucket_width = history / max_buckets

        # Get a reference origin time so that buckets are aligned relative to this
        current_dtime = datetime.datetime.now()
        self._origin_dtime = current_dtime - history
        self._last_updated = self._origin_dtime

        self._sensors = dict()

        # Update humidity and temperature data for each sensor from the database
        self.update()

    def update(self):
        current_dtime = datetime.datetime.now()
        discard_times_before = current_dtime - self._history

        sensor_names = self.querySensorNames(
            start=self._last_updated, end=current_dtime
        )

        for sensor_name in sensor_names:
            df = self.queryBuckets(
                sensor_name=sensor_name,
                start=self._last_updated,
                end=current_dtime,
                bucket_width=self._bucket_width,
                origin=self._origin_dtime,
            )
            # Just in case of NaN values
            df.set_index("time_bucket", inplace=True)
            df.ffill(inplace=True)
            df.bfill(inplace=True)

            # Use deques for easy popleft for old data, and extend for new data. I'm not sure if this is the best
            # idea (performance-wise) if we convert back to a pd.DataFrame later anyway, but it makes the code simpler?
            # Probably doesn't matter here about performance as the compute time is negligible overall...
            newdata = deque(df.itertuples(index=True, name="SensorDht"))
            if len(newdata) == 0:
                logger.warning(f"[{sensor_name}] No data... continuing")
                continue

            if sensor_name in self._sensors:
                while self._sensors[sensor_name][0][0] < discard_times_before:
                    # Remove old data
                    self._sensors[sensor_name].popleft()

                # If the new time bucket is the same as the old one, just replace it.
                # Stops problems where the latest time bucket is added on every update
                if self._sensors[sensor_name][-1][0] == newdata[0][0]:
                    self._sensors[sensor_name][-1] = newdata.popleft()

                self._sensors[sensor_name].extend(newdata)
            else:
                self._sensors[sensor_name] = newdata

            # Remove sensors with no data
            for key, val in self._sensors.items():
                if len(val) == 0:
                    self._sensors.pop(key)

        self._last_updated = current_dtime

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
        print(pd.DataFrame(sensor_data._sensors["inside"]).iloc[-10:])
        while time.time() - t < 5:
            time.sleep(0.1)
