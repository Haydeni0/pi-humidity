/*
Compile and run with
    g++ cdhtlogger/dhtLogger.cpp cdhtlogger/dht22/dht22lib.cpp -lwiringPi -lyaml-cpp -o dhtLogger.exe
&& ./dhtLogger.exe
*/

#include "dht22/dht22lib.h"
#include <yaml-cpp/yaml.h>
#include <vector>

class NamedDhtSensor : public DhtSensor
{
   public:
    std::string m_name;

    NamedDhtSensor(std::string name, int pin) : DhtSensor{pin}, m_name{name} {}
};



std::vector<NamedDhtSensor> loadSensors(std::string config_filepath)
{
    const YAML::Node config = YAML::LoadFile(config_filepath);

    const std::string schema_name = config["schema_name"].as<std::string>();
    const std::string table_name = config["table_name"].as<std::string>();

    const YAML::Node sensor_gpio = config["SensorGPIO"];

    std::vector<NamedDhtSensor> sensors;
    sensors.reserve(sensor_gpio.size());

    int sensor_idx = 0;
    for (YAML::const_iterator pin = sensor_gpio.begin(); pin != sensor_gpio.end(); pin++) {
        std::string name = pin->first.as<std::string>();  // key
        int pin_number = pin->second.as<int>();           // value

        sensors.push_back(NamedDhtSensor(name, pin_number));
    }

    return sensors;
}

int main(void)
{
    if (wiringPiSetupGpio() == -1) {
        std::cout << "wiringPi setup failed";
        exit(1);
    }

    std::vector<NamedDhtSensor> sensors = loadSensors("/shared/config.yaml");

#ifdef DEBUG
    NamedDhtSensor::printSignalTitle();
#endif

    int delayMilliseconds = 500;
    for (int i = 0; i < 1000; i++) {
        for (NamedDhtSensor sensor : sensors) {
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