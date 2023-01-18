import board
import adafruit_dht
import time
import yaml
import dataclasses
import logging
from database_api import DatabaseApi, DhtObservation
from datetime import datetime

from pathlib import Path

Path("/shared/logs").mkdir(parents=True, exist_ok=True)

# Set up logging
start_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
# Worry about this potentially clogging up the device storage
# if the container keeps restarting or too many things are logged...
logging.basicConfig(
    filename=f"/shared/logs/dhtLogger_{start_time}.log",
    filemode="w",
    format="[%(asctime)s - %(levelname)s] %(funcName)20s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


class DhtSensor(adafruit_dht.DHT22):
    """Subclass of DHT22 to add a name member

    Args:
        name (str): Name of the sensor
        pin (int): GPIO pin number on the raspberry pi that the data line of the sensor is connected to
        use_pulsio (bool): False to force bitbang when pulseio available (only with Blinka)
    """

    name: str

    def __init__(self, name, pin: int, use_pulseio: bool = adafruit_dht._USE_PULSEIO):
        super().__init__(adafruit_dht.Pin(pin), use_pulseio)
        self.name = name


def main():
    with open("/shared/config.yaml", "r") as f:
        config: dict = yaml.load(f, yaml.Loader)

    sensor_retry_seconds = config["sensor_retry_seconds"]
    schema_name = config["schema_name"]
    table_name = config["table_name"]

    # Try to connect to the server, and retry if fail
    for _ in range(3):
        try:
            db = DatabaseApi()
            break
        except:
            time.sleep(5)
            continue
    else:
        logger.error("Could not connect to server")
        raise

    full_table_name = db.joinNames(schema_name, table_name)
    db.createDhtTable(full_table_name)

    sensors: list[DhtSensor] = []
    for sensor_name, gpio_pin in config["SensorGPIO"].items():
        sensors.append(DhtSensor(name=sensor_name, pin=gpio_pin, use_pulseio=False))

    while True:
        for sensor in sensors:
            try:
                dht = DhtObservation(
                    dtime=datetime.now(),
                    temperature=sensor.temperature,
                    humidity=sensor.humidity,
                )

                pass
            except RuntimeError as error:
                if error.args[0] == "DHT sensor not found, check wiring":
                    logger.error(
                        f"[{sensor.name}] DHT sensor not found, check wiring"
                    )
                # If it's a regular runtime error, this is normal behaviour
                # for a DHT22 device so continue
                continue
            except Exception as error:
                logger.error(error)
                raise error

            db.sendObservation(
                table_name=full_table_name, sensor_name=sensor.name, dht=dht
            )

        time.sleep(sensor_retry_seconds)


if __name__ == "__main__":
    main()
