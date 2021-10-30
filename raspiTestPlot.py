import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import datetime
import pandas as pd

matplotlib.use('TkAgg')

fig = plt.figure()

current_time = datetime.datetime.now()
start_dtime = current_time - datetime.timedelta(hours=1)

N = 10

t = np.linspace(
            pd.Timestamp(start_dtime).value, 
            pd.Timestamp(current_time).value, N)
t = pd.to_datetime(t)

ax = fig.add_subplot(1, 1, 1)

x = np.linspace(0, 10, N)

ax.plot(t, x)
plt.show()

