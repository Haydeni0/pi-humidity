


import board
import adafruit_dht
import time
import yaml
import dataclasses
import logging
from database_api import DatabaseDHT, ObsDHT

# Set up logging
logging.basicConfig(
    filename="/shared/logs/dhtLogger.log",
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
    with open("/shared/gpio.yaml", "r") as f:
        gpio_config: dict = yaml.load(f, yaml.Loader)
    
    sensors: list[DhtSensor] = []
    for sensor_name, gpio_pin in gpio_config["SensorGPIO"].items():
        sensors.append(DhtSensor(name=sensor_name, pin=gpio_pin, use_pulseio=False))
    
    while (True):
        for sensor in sensors:
            print(sensor.name)
            print(f"    Temperature: {sensor.temperature: 2.2f}C, Humidity: {sensor.humidity: 2.2f}")
            time.sleep(1)



if __name__ == "__main__":
    main()