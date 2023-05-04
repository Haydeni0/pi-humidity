/**

Compile with
    g++ dhtLogger.cpp -lwiringPi -Wall -o dhtLogger.exe && ./dhtLogger.exe
or for debug
    g++ dhtLogger.cpp -lwiringPi -Wall -DDEBUG -o dhtLogger.exe && ./dhtLogger.exe

Based on:
http://www.uugear.com/portfolio/read-dht1122-temperature-humidity-sensor-from-raspberry-pi/

Significant changes:
--------------------
[Robust decoding of data]
In the previous implementation, the data
(5 bytes: 2 each for humidity/temperature and 1 for a checksum)
is decoded by classifying signal states as 1 or 0 depending if the duration held by the state is
longer than 16 microseconds or not.
Sometimes, this classification is inaccurate and we get bad data, which is typically
invalidated by the checksum. To see why, here is realistic example of recorded state durations in
microseconds (1 byte only):

         Signal A: ( 3, 2, 3, 8, 8, 9, 8, 3)
         Signal B: ( 7, 7, 7,32,33,33,32, 6)
         Signal C: (21,22,22,86,84,84,85,23)
True decoded data: ( 0, 0, 0, 1, 1, 1, 1, 0)

It is clear to see that the encoded data is present in all signals, but with the previous
classification technique only signal B will be decoded correctly. I'm not sure exactly why
in some circumstances the state durations are longer/shorter. I've observed consistently
shorter durations when running this in a docker container.

The newer the decoding technique uses k-means (k=2) to cluster the signal into upper and lower
clusters and classify any states assigned to the upper cluster as a '1'. This results in all
signals A, B and C being decoded correctly.

Other changes:
- Fix undefined behaviour when reading too many bits in the read loop

*/

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <wiringPi.h>

#include <algorithm>
#include <csignal>
#include <iostream>

#define PIN \
    25  // wiringPi pin number. Run the command ```gpio readall``` to check the wPi pin (compare to
        // the physical pins).

#define MAX_TIMINGS 85  // Takes 84 state changes to transmit data
#define NBITS 40        // Total number of bits of data
#define BAD_VALUE 999

#define DEFAULT_TEXT printf("\033[0m");
#define BLACK_TEXT printf("\033[0;30m");
#define TEAL_TEXT printf("\033[36;1m");
#define RED_TEXT printf("\033[0;31m");

/**
 * A k-means algorithm for 1 dimensional data, with k equal to 2.
 *
 * The two centroids are initialised at the minimum and maximum of the dataset
 *
 * @param Input data
 * @param Centroid assignments (1 for the upper centroid, 0 for the lower)
 */
void twoMeans(const int (&x)[NBITS], bool (&assignUpper)[NBITS])
{
    // The initial values for the centroids are the minimum and maximum
    float lower = x[0];
    float upper = x[0];
    for (int elem : x) {
        if (elem < lower) lower = elem;
        if (elem > upper) upper = elem;
    }

    // Reset assignments (assign all to the lower centroid)
    for (bool &elem : assignUpper)
        elem = false;

    while (true) {
        // This will always converge, so won't run infinitely

        // Assignment step: assign each observation to the nearest centroid
        bool newAssignUpper[NBITS];
        for (int j = 0; j < NBITS; j++) {
            if ((abs(lower - x[j]) > abs(upper - x[j])))
                newAssignUpper[j] = true;
            else
                newAssignUpper[j] = false;
        }

        // Update step: update the centroid location with the mean of the assigned observations
        float newLower = 0;
        float newUpper = 0;
        int numUpperObservations = 0;
        for (int j = 0; j < NBITS; j++) {
            numUpperObservations += newAssignUpper[j];
            if (newAssignUpper[j])
                newUpper += x[j];
            else
                newLower += x[j];
        }
        newUpper /= numUpperObservations;
        newLower /= NBITS - numUpperObservations;

        // Check convergence: k-means has converged if no assignments have changed
        bool converged = true;
        for (int j = 0; j < NBITS; j++) {
            if (newAssignUpper[j] != assignUpper[j]) {
                converged = false;
                break;
            }
        }
        if (converged) return;

        // Iterate: new values are now old
        upper = newUpper;
        lower = newLower;
        for (int j = 0; j < NBITS; j++)
            assignUpper[j] = newAssignUpper[j];
    }
}

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
        int allStateDurations[NBITS];
        for (int &elem : allStateDurations)
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
             (stateChanges < MAX_TIMINGS) && (stateDuration < 255) && (bitsRead < NBITS);
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
                allStateDurations[bitsRead] = stateDuration;
                bitsRead++;
            }
        }

        for (int elem : allStateDurations) {
            if (elem == BAD_VALUE) {
                m_humidity = BAD_VALUE;
                m_temperature = BAD_VALUE;
                return;
            }
        }
        bool stateData[NBITS];
        twoMeans(allStateDurations, stateData);

        for (int j = 0; j < NBITS; j++) {
            data[j / 8] <<= 1;  // Each array element has 8 bits.  Shift Left 1 bit.
            // if (allStateDurations[j] > 16)  // A State Change > 16 microseconds is a '1'.
            if (stateData[j])  // A state with a duration assigned to an upper cluster is a '1'
                data[j / 8] |= 0x00000001;
        }

#ifdef DEBUG
        // Print state duration
        // Colour state durations longer than 16 microseconds as TEAL
        // Colour upper clustered state durations as RED
        for (int j = 0; j < NBITS; j++) {
            if (allStateDurations[j] > 16)
                TEAL_TEXT
            else if (stateData[j])
                RED_TEXT

            if (allStateDurations[j] == BAD_VALUE) BLACK_TEXT
            printf("%3d", allStateDurations[j]);
            DEFAULT_TEXT

            if ((j != 0) && (j % 8 == 0))
                printf("║");
            else
                printf("|");
        }
#endif

        /*
        Read 40 bits. (Five elements of 8 bits each)  Last element is a
        checksum.
        */
        if ((bitsRead >= NBITS) && (data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF))) {
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
        std::cout << "wiringPi setup failed";
        exit(1);
    }

#ifdef DEBUG
    printf("DEBUG MODE: Displaying microseconds in each state.\n");
    for (int j{0}; j < NBITS; j++) {
        printf("%3d", j);
        if ((j != 0) && (j % 8 == 0))
            printf("║");
        else
            printf("|");
    }
    std::cout << "\n";
    for (int j{0}; j < NBITS; j++)
        printf("----");
    std::cout << "\n";
#endif

    DhtSensor sensor{PIN};

    int delayMilliseconds = 500;
    for (int i = 0; i < 1000; i++) {
        sensor.read();
        printf("%-3.1f *C  Humidity: %-3.1f%%\n", sensor.m_temperature, sensor.m_humidity);

        delay(delayMilliseconds);  // Wait between readings
    }

    return (0);
}