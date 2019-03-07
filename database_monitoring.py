#!/usr/bin/env python3

import configparser
import logging

from database import Database
from heartbeat import Heartbeat
from sendmail import SendMail
from sensors import Sensors

CONFIG_FILE = '/mnt/dev/monitoring/Database_monitoring/database_monitoring.conf'

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

    heartbeat = Heartbeat(CONFIG, DATABASE, SENDMAIL)
    if heartbeat.check_last_heartbeat():
        heartbeats = heartbeat.heartbeats
        # ToDo: check battery, temp, humidity
        sensors = Sensors(CONFIG, DATABASE, SENDMAIL, heartbeats)

    DATABASE.close()


if __name__ == '__main__':
    # time.sleep(45)
    init()

    SENDMAIL = SendMail(CONFIG)
    DATABASE = Database(CONFIG, SENDMAIL)

    main()
