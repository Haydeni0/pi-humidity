# %matplotlib notebook
import pandas as pd
import numpy as np

import time
import datetime
from itertools import count

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# filepath = "data/DHT22_data.csv"
filepath = "WindowsTest/TestData.csv"

data = pd.read_csv(filepath)
data["Datetime"] = pd.to_datetime(data["Datetime"])

# time_history = datetime.datetime.minute(20) # The amount of time history shown in the graph

fig, ax = plt.subplots()
# (l,) = ax.plot([0, 2 * np.pi], [-1, 1])
(l,) = ax.plot(data["Datetime"][:2], data["Humidity"][:2])

# Global scope list passed by reference and changed in animate()
ylim = [np.min(data["Humidity"][:2]) ,np.max(data["Humidity"][:2])]

def updatePlot(i):
    # l.set_data(t[:i], x[:i])
    l.set_data(data["Datetime"][:i], data["Humidity"][:i])

    # Set x and y axes limits
    ax.set_xlim(data["Datetime"][0], data["Datetime"][i])
    if data["Humidity"][i] > ylim[1]:
        ylim[1] = data["Humidity"][i]
    elif data["Humidity"][i] < ylim[0]:
        ylim[0] = data["Humidity"][i]
    ax.set_ylim(ylim)

plt.axis([0, 10, 0, 1])

for i in range(10000):
    updatePlot(i)
    plt.pause(0.01)

plt.show()