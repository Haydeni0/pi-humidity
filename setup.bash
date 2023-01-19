#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PASSWORD_FILE=$SCRIPT_DIR/password.env

mkdir -p $SCRIPT_DIR/shared
CONFIG_FILE=$SCRIPT_DIR/shared/config.yaml

if ! test -f "$PASSWORD_FILE"; then
    echo "Enter TimescaleDB password: (default: 'pwd')"
    read -s PASSWORD

    # If no password was given, set it to "pwd"
    if [ -z "$PASSWORD" ]; then 
        PASSWORD="pwd"
    fi
    echo "Saving to '$PASSWORD_FILE'"
    echo POSTGRES_PASSWORD=$PASSWORD > $PASSWORD_FILE
else
    # Display the full filepath of the password env file
    echo "Password file already exists: '$(readlink -f $PASSWORD_FILE)', delete or edit to change password."
fi

re='^[0-9]+$'
namere='^[A-Za-z0-9_]+$'
if ! test -f "$CONFIG_FILE"; then
    echo "Enter number of GPIO pins"
    read NUM_PINS

    # Check it's a valid number with regex
    if ! [[ $NUM_PINS =~ $re ]] ; then
        echo "error: Not a number" >&2
        exit 1
    fi

    echo "SensorGPIO:" >> $CONFIG_FILE
    
    for ((i=1; i<=$NUM_PINS; i++))
    do
        
        

        echo "Enter GPIO pin sensor name $i/$NUM_PINS"
        read NAME
        if ! [[ $NAME =~ $namere ]] ; then
            echo "error: Not a valid name" >&2
            rm -f $CONFIG_FILE
            exit 1
        fi

        echo "Enter GPIO pin number $i/$NUM_PINS"
        read PIN
        if ! [[ $PIN =~ $re ]] ; then
            echo "error: Not a number" >&2
            rm -f $CONFIG_FILE
            exit 1
        fi
        
        echo "  $NAME: $PIN" >> $CONFIG_FILE
    done

    # Save default values
    echo "sensor_retry_seconds: 2" >> $CONFIG_FILE
    echo "figure_update_interval_seconds: 5" >> $CONFIG_FILE
    echo "schema_name:" >> $CONFIG_FILE
    echo "table_name: dht" >> $CONFIG_FILE

    echo "Successfully saved to '$CONFIG_FILE' (including other default parameters)"
else
    # Display the full filepath of the GPIO env file
    echo "GPIO pin file already exists: '$(readlink -f $CONFIG_FILE)'"
fi


# docker compose build
# docker compose up -d