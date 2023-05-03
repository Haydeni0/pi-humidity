/*

Compile with
    g++ dhtLogger.cpp -lwiringPi -Wall -o dhtLogger.exe && ./dhtLogger.exe
or for debug
    g++ dhtLogger.cpp -lwiringPi -Wall -DDEBUG -o dhtLogger.exe && ./dhtLogger.exe

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
#define BAD_VALUE 999

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
        int state_durations[40];
        for (int &elem : state_durations)
            elem = BAD_VALUE;

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
                state_durations[bitsRead] = stateDuration;
                data[bitsRead / 8] <<= 1;  // Each array element has 8 bits.  Shift Left 1 bit.
                if (stateDuration > 16)    // A State Change > 16 microseconds is a '1'.
                    data[bitsRead / 8] |= 0x00000001;
                bitsRead++;
            }
        }

        /*
        Sometimes, particularly when run in a docker container, the state durations are a lot
        shorter than when run directly on the Pi. Since the state durations encode the
        humidity and temperature values (1 for a state duration > 16 microseconds), this
        "weak signal" due to shortened state durations corrupts this information.
         E.g., (3,2,3,8,3,9,8,3) rather than (7,7,7,32,7,33,32,6)
        */
        /*
        Instead of encoding 1's with state duration > 16 microseconds,
        use k-means clustering (with k=2) to cluster state durations into two groups.
        The group with larger mean state duration are encoded as 1's.
        */

#ifdef DEBUG
        // Print state duration, colouring 1's (state durations longer than 16 microseconds) as TEAL
        for (int elem : state_durations) {
            if (elem > 16) TEAL_TEXT
            if (elem == BAD_VALUE) BLACK_TEXT
            printf("%3d", elem);
            DEFAULT_TEXT
            printf("|");
        }
#endif

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
        // This is sometimes 0, but seemingly only when run in a container? This happens 40-60% of
        // the time a measurement is not flagged as bad This happens when stateDuration has values
        // all below 16 (the cutoff value fo a 1 or a 0), but there still seems to be some signal
        // there. E.g., (3,2,3,8,3,9,8,3) rather than (7,7,7,32,7,33,32,6) Maybe this "weak signal"
        // can be extracted using some sort of clustering algorithm to separate between 1's and 0's.
        m_humidity = humidity;
        m_temperature = temperature;
    }
};

std::string debug_msg = "Default debug message";

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

#ifdef DEBUG
    for (int j{0}; j < 40; j++)
        printf("%3d|", j);
    std::cout << "\n";
    for (int j{0}; j < 40; j++)
        printf("----");
    std::cout << "\n";
#endif

    DhtSensor sensor{25};

    int good_count = 0;
    int zero_count = 0;

    int delay_milliseconds = 100;
    for (int i = 0; i < 1000; i++) {
        sensor.read();
        float humidity = sensor.m_humidity;
        float temperature = sensor.m_temperature;
        printf("%-3.1f *C  Humidity: %-3.1f%%\n", temperature, humidity);

        if (humidity == 0 && temperature == 0)
            zero_count++;
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