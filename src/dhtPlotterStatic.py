import plotly.io as pio
from pathlib import Path
from dhtPlotter import makeFigures, FULL_TABLE_NAME
from sensors import SensorData
from datetime import datetime, timedelta
from time import time, sleep
import logging

logger = logging.getLogger("__name__")

scope = pio.kaleido.scope

FILEPATH_H = Path(__file__).parent.joinpath("assets/fig_humidity.png")
FILEPATH_T = Path(__file__).parent.joinpath("assets/fig_temperature.png")

SLEEP_TIMER_SECONDS = 10 * 60


def saveStaticFigures():
    # Fully regenerate an image of each figure to disk

    t = time()
    temp_sensor_data = SensorData(table_name=FULL_TABLE_NAME)
    temp_sensor_data.history = timedelta(days=2)

    # Make the figures in the exact same way as the webpage does
    temp_fig_H, temp_fig_T = makeFigures(temp_sensor_data)
    temp_fig_H.write_image(FILEPATH_H, width=1000, height=300)
    temp_fig_T.write_image(FILEPATH_T, width=1000, height=300)

    # Manually shutdown kaleido, which is used to write plotly images to file,
    # due to memory leak concerns with chromium and multithreading in dhtPlotter.py (gunicorn/dash)
    # See https://github.com/plotly/Kaleido/issues/49 and https://github.com/plotly/Kaleido/issues/42
    scope._shutdown_kaleido()

    logger.info(f"Sensor data written to static images in {time() - t: .2g} seconds")


if __name__ == "__main__":

    while True:
        saveStaticFigures()
        sleep(SLEEP_TIMER_SECONDS)
