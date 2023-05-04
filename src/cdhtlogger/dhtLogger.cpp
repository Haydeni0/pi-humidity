
#include "dht22/dht22lib.h"

int main(void)
{
    if (wiringPiSetup() == -1) {
        std::cout << "wiringPi setup failed";
        exit(1);
    }

    DhtSensor sensors[2] = {23, 25};

    int delayMilliseconds = 500;
    for (int i = 0; i < 1000; i++) {
        for (DhtSensor sensor : sensors) {
            sensor.read();
            printf("%-3.1f *C  Humidity: %-3.1f%%\n", sensor.m_temperature, sensor.m_humidity);
        }

        delay(delayMilliseconds);  // Wait between readings
    }

    return (0);
}