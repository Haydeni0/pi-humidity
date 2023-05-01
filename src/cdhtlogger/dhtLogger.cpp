/*

Compile with 
    g++ dhtLogger.cpp -lwiringPi -Wall -o dhtLogger.exe && ./dhtLogger.exe

 Based on:
 http://www.uugear.com/portfolio/read-dht1122-temperature-humidity-sensor-from-raspberry-pi/
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <wiringPi.h>

#include <iostream>

#define MAX_TIMINGS 85  // Takes 84 state changes to transmit data
#define BAD_VALUE 999.9f

int data[5] = {0, 0, 0, 0, 0};

class DhtSensor
{
   public:
    int m_pin;
    float m_humidity{555};
    float m_temperature{666};

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
             (stateChanges < MAX_TIMINGS) && (stateDuration < 255);
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
                data[bitsRead / 8] <<=
                    1;  // Each array element has 8 bits.  Shift Left 1 bit.
                if (stateDuration >
                    16)  // A State Change > 16 microseconds is a '1'.
                    data[bitsRead / 8] |= 0x00000001;
                bitsRead++;
            }
        }

        /*
        Read 40 bits. (Five elements of 8 bits each)  Last element is a
        checksum.
        */
        if ((bitsRead >= 40) &&
            (data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF))) {
            humidity = (float)((data[0] << 8) + data[1]) / 10.0;
            temperature = (float)((data[2] << 8) + data[3]) / 10.0;
            if (data[2] & 0x80)  // Negative Sign Bit on.
                temperature *= -1;
        }

        // Update members
        m_humidity = humidity;
        m_temperature = temperature;
    }
};

int main(void)
{
    if (wiringPiSetup() == -1) {
        std::cout << "asd"
                  << "\n";
        exit(1);
    }

    DhtSensor sensor{25};

    for (int i = 0; i < 5000; i++) {
        sensor.read();
        printf("%-3.1f *C  Humidity: %-3.1f%%\n", sensor.m_temperature,
               sensor.m_humidity);
        delay(1000); /* Wait 10 seconds between readings. */
    }

    return (0);
}