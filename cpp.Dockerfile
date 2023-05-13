FROM gcc:9.5.0-bullseye

RUN apt-get update
RUN apt-get install -y cmake

# WiringPi's build script uses sudo
RUN apt-get install -y sudo

WORKDIR /tmp
# Get WiringPi to be able to access Raspberry Pi GPIO pins
RUN git clone https://github.com/WiringPi/WiringPi.git WiringPi
# Parse yaml in cpp
RUN git clone https://github.com/jbeder/yaml-cpp.git yaml-cpp

# Install wiringPi
WORKDIR /tmp/WiringPi
RUN ./build

# Install yaml-cpp
WORKDIR /tmp/yaml-cpp-build
RUN cmake -S /tmp/yaml-cpp
RUN make
RUN make install
