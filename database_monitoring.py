#!/usr/bin/env python3

import configparser
import logging
import time

from modules.database import Database
from modules.sendmail import SendMail
from modules.sensor_heartbeat import SensorHeartbeat
from modules.sensors import Sensors
from modules.system_heartbeat import SystemHeartbeat

CONFIG_FILE = '/mnt/dev/monitoring/Database_monitoring/config/database_monitoring.conf'

CONFIG = None
LOGGER = None
SENDMAIL = None
DATABASE = None


def init():
    global CONFIG
    CONFIG = configparser.ConfigParser()
    CONFIG.read(CONFIG_FILE)

    logging.basicConfig(
        filename=CONFIG.get('LOGGER', 'FILE'),
        format=CONFIG.get('LOGGER', 'FORMAT').replace('((', '%('),
        level=logging.DEBUG)
    global LOGGER
    LOGGER = logging.getLogger('database_monitoring')


def main():
    if not DATABASE.check_status_and_connect():
        return

    sensor_heartbeat = SensorHeartbeat(CONFIG, DATABASE, SENDMAIL)
    if sensor_heartbeat.check_last_heartbeat():
        heartbeats = sensor_heartbeat.heartbeats
        sensors = Sensors(CONFIG, DATABASE, SENDMAIL, heartbeats)
        sensors.check_battery_status()
        sensors.check_temperature_status()
        sensors.check_humidity_status()

    system_heartbeat = SystemHeartbeat(CONFIG, DATABASE, SENDMAIL)
    system_heartbeat.check_cpu()
    system_heartbeat.check_memory()
    system_heartbeat.check_sd_card()
    system_heartbeat.check_dev_partition()
    system_heartbeat.check_cloud_partition()
    system_heartbeat.check_nas_partition()

    DATABASE.close()


if __name__ == '__main__':
    time.sleep(45)
    init()

    SENDMAIL = SendMail(CONFIG)
    DATABASE = Database(CONFIG, SENDMAIL)

    main()
