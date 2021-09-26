# %matplotlib notebook
import pandas as pd
import dask.dataframe as dd
from collections import deque
import numpy as np

import time
import datetime
from itertools import count

import utils

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# filepath = "data/DHT22_data.csv"
filepath = "WindowsTest/TestData.csv"

# Use a dask dataframe for managed memory usage
data = dd.read_csv(filepath)
data["Datetime"] = dd.to_datetime(data["Datetime"])

# The amount of time history shown in the graph
history_window = datetime.timedelta(minutes=20)

fig, ax = plt.subplots()
# Temporary plot
(l,) = ax.plot(1, 1)


def updatePlot(data: dd.core.DataFrame) -> None:
    current_time = datetime.datetime.now()
    window_end = current_time
    window_start = window_end - history_window

    window_start_idx = utils.binSearchDatetime(data["Datetime"], window_start)
    window_end_idx = len(data) - 1

    assert window_start_idx < window_end_idx

    l.set_data(data["Datetime"].loc[window_start_idx:window_end_idx].compute(), data["Humidity"].loc[window_start_idx:window_end_idx].compute())

    # Set x and y axes limits
    ax.set_xlim(
        data["Datetime"].loc[window_start_idx].compute()
        , data["Datetime"].loc[window_end_idx].compute())
    ax.set_ylim(
        data["Humidity"].loc[window_start_idx:window_end_idx].min().compute(),
        data["Humidity"].loc[window_start_idx:window_end_idx].max().compute()
    )


# plt.axis([0, 10, 0, 1])

# for i in range(10000):
#     updatePlot(i)
#     plt.pause(0.01)

# plt.show()

updatePlot(data)
plt.show()
