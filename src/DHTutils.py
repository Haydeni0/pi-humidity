import Adafruit_DHT
import time
import logging

logger = logging.getLogger(__name__)


def read_retry_inout(
    sensor,
    pin_inside: int,
    pin_outside: int,
    retries: int = 10,
    delay_seconds: int = 1,
    platform=None,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Read DHT sensor of specified sensor type (DHT11, DHT22, or AM2302) on
    specified pin and return a tuple of humidity (as a floating point value
    in percent) and temperature (as a floating point value in Celsius).
    Unlike the read function, this read_retry function will attempt to read
    multiple times (up to the specified max retries) until a good reading can be
    found. If a good reading cannot be found after the amount of retries, a tuple
    of (None, None) is returned. The delay between retries is by default 1
    seconds, but can be overridden.

    This has been modified from Adafruit_DHT source to allow reading of two sensors at
    once without queueing their retries (which adds latency)
    """
    done_inside = False
    done_outside = False
    num_retries = 0
    while not (done_inside and done_outside):
        if not done_inside:
            inside_H, inside_T = Adafruit_DHT.read(
                sensor, pin_inside, platform
            )
            if inside_H is not None and inside_T is not None:
                done_inside = True
        if not done_outside:
            outside_H, outside_T = Adafruit_DHT.read(
                sensor, pin_outside, platform
            )
            if outside_H is not None and outside_T is not None:
                done_outside = True

        if done_inside and done_outside:
            return (
                inside_H,
                inside_T,
                outside_H,
                outside_T,
            )

        if num_retries >= retries:
            break
        else:
            num_retries += 1

    if done_inside and not done_outside:
        logger.debug(
            f"Logging inside only: H({inside_H}) T({inside_T})"
        )
        return (inside_H, inside_T, None, None)
    elif not done_inside and done_outside:
        logger.debug(
            f"Logging outside only: H({outside_H}) T({outside_T})"
        )
        return (None, None, outside_H, outside_T)
    else:
        logger.debug(f"Logging none")
        return (None, None, None, None)
