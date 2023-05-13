/*
Compile and run with
    g++ src/cdhtlogger/dhtLogger.cpp src/cdhtlogger/dht22/dht22lib.cpp -lwiringPi -o dhtLogger.exe
&& ./dhtLogger.exe
*/

#include "dht22/dht22lib.h"
#include <vector>

int main(void)
{
    if (wiringPiSetup() == -1) {
        std::cout << "wiringPi setup failed";
        exit(1);
    }

    std::vector<DhtSensor> sensors = {23, 25};

#ifdef DEBUG
    DhtSensor::printSignalTitle();
#endif

    int delayMilliseconds = 500;
    for (int i = 0; i < 1000; i++) {
        for (DhtSensor sensor : sensors) {
            sensor.read();
#ifdef DEBUG
            sensor.printSignal();
#endif
            sensor.print();
            delay(delayMilliseconds/sensors.size());// Wait between readings
        }
    }

    return (0);
}