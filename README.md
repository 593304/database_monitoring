# Database Monitor for [Xiaomi Mi Temperature and Humidity Monitor](https://github.com/593304/xiaomi_mitemp_monitor) and [Raspberry Pi System Monitor](https://github.com/593304/rpi_system_monitor)

Python script for regularly checking the status of the database or the values in it. 
After a given timeout or connection error the script will send an e-mail.

Already implemented functionalities:
  - E-mail sending
  - Checking the database connection
    - At 50% of the timeout trying to restart the service
    - After the timeout reached sending an e-mail
  - Checking the sensors connection
    - At 50% of the timeout trying to restart the bluetooth service
    - After the timeout reached sending an e-mail
