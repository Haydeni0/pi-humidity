FROM gcc:9.5.0-bullseye
WORKDIR /tmp

RUN apt-get update
RUN apt-get install -y cmake

# Get WiringPi to be able to access Raspberry Pi GPIO pins
# WiringPi's build script needs sudo
RUN apt-get install -y sudo
RUN git clone https://github.com/WiringPi/WiringPi.git WiringPi
WORKDIR /tmp/WiringPi
RUN ./build clean
# RUN wget https://project-downloads.drogon.net/wiringpi-latest.deb
# RUN dpkg -i wiringpi-latest.deb