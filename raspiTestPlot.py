import matplotlib.pyplot as plt
import matplotlib
import numpy as np

fig = plt.figure()

ax = fig.add_subplot(1, 1, 1)

x = np.arange(0, 10, 0.1)
y = x

ax.plot(x, y)
print(matplotlib.get_backend())
plt.show()

