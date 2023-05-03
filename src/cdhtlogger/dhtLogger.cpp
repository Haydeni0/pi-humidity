/*

Compile with
    g++ dhtLogger.cpp -lwiringPi -Wall -o dhtLogger.exe && ./dhtLogger.exe

 Based on:
 http://www.uugear.com/portfolio/read-dht1122-temperature-humidity-sensor-from-raspberry-pi/

 Main changes:
 - Fix undefined behaviour when reading too many bits in the read loop

 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <wiringPi.h>

#include <csignal>
#include <iostream>

#define MAX_TIMINGS 85  // Takes 84 state changes to transmit data
#define BAD_VALUE 999.9f

#define BLACK_TEXT printf("\033[0;30m");
#define DEFAULT_TEXT printf("\033[0m");
#define TEAL_TEXT printf("\033[36;1m");

class DhtSensor
{
   public:
    int m_pin;
    float m_humidity{BAD_VALUE};
    float m_temperature{BAD_VALUE};

   public:
    DhtSensor(int pin) : m_pin{pin} {}

    void read()
    {
        uint8_t lastState = HIGH;
        uint8_t stateDuration = 0;
        uint8_t stateChanges = 0;
        uint8_t bitsRead = 0;
        float humidity = BAD_VALUE;
        float temperature = BAD_VALUE;

        int data[5] = {0, 0, 0, 0, 0};
        data[0] = data[1] = data[2] = data[3] = data[4] = 0;

        /*
        Signal Sensor we're ready to read by pulling pin UP for 10 milliseconds,
        pulling pin down for 18 milliseconds and then back up for 40
        microseconds.
         */
        pinMode(m_pin, OUTPUT);
        digitalWrite(m_pin, HIGH);
        delay(10);
        digitalWrite(m_pin, LOW);
        delay(18);
        digitalWrite(m_pin, HIGH);
        delayMicroseconds(40);

        /* Read data from pin.  Look for a change in state. */
        pinMode(m_pin, INPUT);

        for ((stateChanges = 0), (stateDuration = 0);
             (stateChanges < MAX_TIMINGS) && (stateDuration < 255) && (bitsRead < 40);
             stateChanges++) {
            stateDuration = 0;
            while ((digitalRead(m_pin) == lastState) && (stateDuration < 255)) {
                stateDuration++;
                delayMicroseconds(1);
            };

            lastState = digitalRead(m_pin);

            // First 2 state changes are sensor signaling ready to send, ignore
            // them. Each bit is preceeded by a state change to mark its
            // beginning, ignore it too.
            if ((stateChanges > 2) && (stateChanges % 2 == 0)) {
                data[bitsRead / 8] <<= 1;  // Each array element has 8 bits.  Shift Left 1 bit.
                if (stateDuration > 16)    // A State Change > 16 microseconds is a '1'.
                {
                    data[bitsRead / 8] |= 0x00000001;
                    TEAL_TEXT
                }
                printf("%3d", stateDuration);
                DEFAULT_TEXT
                printf("|");

                bitsRead++;
            }
        }

        /*
        Read 40 bits. (Five elements of 8 bits each)  Last element is a
        checksum.
        */
        if ((bitsRead >= 40) && (data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF))) {
            humidity = (float)((data[0] << 8) + data[1]) / 10.0;
            temperature = (float)((data[2] << 8) + data[3]) / 10.0;
            if (data[2] & 0x80)  // Negative Sign Bit on.
                temperature *= -1;
        }

        // Update members
        // Why is this sometimes 0, but seemingly only when run in a container?
        // Seems to be something to do with the stateDuration
        m_humidity = humidity;
        m_temperature = temperature;
    }
};

std::string debug_msg;

void signalHandler(int signum)
{
    std::cout << "Interrupt signal (" << signum << ") received.\n";
    std::cout << debug_msg << "\n";

    exit(signum);
}

int main(void)
{
    if (wiringPiSetup() == -1) {
        std::cout << "wiringPi setup failed";
        exit(1);
    }
    // register signal SIGINT and signal handler
    signal(SIGINT, signalHandler);

    for (int j{0}; j < 40; j++)
        printf("%3d|", j);
    std::cout << "\n";
    for (int j{0}; j < 40; j++)
        printf("----");
    std::cout << "\n";

    DhtSensor sensor{25};

    int good_count = 0;
    int error_count = 0;
    int zero_count = 0;

    int delay_milliseconds = 1000;
    for (int i = 0; i < 100; i++) {
        sensor.read();
        float humidity = sensor.m_humidity;
        float temperature = sensor.m_temperature;
        printf("%-3.1f *C  Humidity: %-3.1f%%\n", temperature, humidity);

        if (humidity == 0 && temperature == 0)
            zero_count++;
        else if (humidity == BAD_VALUE && temperature == BAD_VALUE)
            error_count++;
        else
            good_count++;

        if (good_count + zero_count > 0) {
            debug_msg =
                "Zero proportion after " + std::to_string(i) + " tries: " +
                std::to_string(static_cast<float>(zero_count * 100) / (good_count + zero_count)) +
                "%";
        }

        delay(delay_milliseconds);  // Wait between readings
    }

    signalHandler(0);
    return (0);
}