# Database Monitor for [Xiaomi Mi Temperature and Humidity Monitor](https://github.com/593304/xiaomi_mitemp_monitor) and [Raspberry Pi System Monitor](https://github.com/593304/rpi_system_monitor)

Python script for regularly checking the status of the database or the values in it. 
After a given timeout or connection error the script will send an e-mail.

Already implemented functionality:
  - E-mail sending
  - Checking the database connection
    - At 50% of the timeout trying to restart the service
    - After the timeout reached sending an e-mail
  - Checking the sensors connection
    - At 50% of the timeout trying to restart the bluetooth service
    - After the timeout reached sending an e-mail

## Update 1

Refactored code and added Sensors class for value checking.

Database schema for the script:
```SQL
CREATE TABLE monitoring.email_alert_sent (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128),
    type VARCHAR(128),
    valid BOOL,
    timestamp TIMESTAMP
)
```

Already implemented functionality:
  - E-mail sending
  - Checking the database connection
    - At 50% of the timeout trying to restart the service
    - After the timeout reached sending an e-mail
  - Checking the sensors connection
    - At 50% of the timeout trying to restart the bluetooth service
    - After the timeout reached sending an e-mail
  - Checking the sensors values
    - Battery level

## Update 2

Finished battery status checking and added fully working e-mail notifications

Already implemented functionality:
  - E-mail sending
  - Checking the database connection
    - At 50% of the timeout trying to restart the service
    - After the timeout reached sending an e-mail
  - Checking the sensors connection
    - At 50% of the timeout trying to restart the bluetooth service
    - After the timeout reached sending an e-mail
  - Checking the sensors values
    - Battery level and sending e-mail if necessary

## Update 3

Finished temperature and humidity status checking and added fully working e-mail notifications

Already implemented functionality:
  - E-mail sending
  - Checking the database connection
    - At 50% of the timeout trying to restart the service
    - After the timeout reached sending an e-mail
  - Checking the sensors connection
    - At 50% of the timeout trying to restart the bluetooth service
    - After the timeout reached sending an e-mail
  - Checking the sensors values
    - Battery level and sending e-mail if necessary
    - Temperature level and sending e-mail if necessary
    - Humidity level and sending e-mail if necessary

## Update 4

Added RPI system status checking with fully working e-mail notifications

Already implemented functionality:
  - E-mail sending
  - Checking the database connection
    - At 50% of the timeout trying to restart the service
    - After the timeout reached sending an e-mail
  - Checking the sensors connection
    - At 50% of the timeout trying to restart the bluetooth service
    - After the timeout reached sending an e-mail
  - Checking the sensors values
    - Battery level and sending e-mail if necessary
    - Temperature level and sending e-mail if necessary
    - Humidity level and sending e-mail if necessary
  - Checking RPI system values
    - CPU temperature, usage and sending e-mail if necessary
    - Memory usage and sending e-mail if necessary
    - SD card usage and sending e-mail if necessary
    - External HDDs partitions usage and sending e-mail if necessary

## Update 5

Added cooldown rate for sensor monitoring
