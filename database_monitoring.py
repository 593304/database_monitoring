#!/usr/bin/env python3

import configparser
import json
import logging
import os
import psycopg2
import sendmail
import socket
import time
from datetime import datetime

DB_CONNECTION_STRING = 'dbname=adam user=adam'
DB_CONNECTION = None
DB_CURSOR = None
TEMP_FILE = '/mnt/dev/monitoring/Database_monitoring/temp_file'

CONFIG = None

LOGGER = None
LOG_FILE = '/mnt/dev/log/python/database_monitoring.log'
LOGGER_FORMAT = '%(asctime)15s | %(levelname)8s | %(name)s - %(funcName)12s - %(message)s'


def get_mail_subject(error_type):
    return {
        'db_error': CONFIG.get('SUBJECTS', 'DB_CONNECTION_ERROR'),
        'sensor_error': CONFIG.get('SUBJECTS', 'SENSOR_CONNECTION_ERROR')
    }[error_type]


def get_mail_message(error_type):
    return {
        'db_error': '<html>'
                    '  <body>'
                    '    <p>Couldn\'t connect to the database on {0} in the last {1} minutes</p>'
                    '    <p>{2}</p>'
                    '  </body>'
                    '</html>',
        'sensor_error': '<html>'
                    '  <body>'
                    '    <p>Couldn\'t connect to the sensor(s) on {0} in the last {1} minutes</p>'
                    '    <p>{2}</p>'
                    '    <p>{3}</p>'
                    '  </body>'
                    '</html>'
    }[error_type]


def send_mail(error_type, error_message):
    subject = get_mail_subject(error_type)
    message = get_mail_message(error_type)

    if error_type == 'db_error':
        message = message\
            .replace('{0}', socket.gethostname())\
            .replace('{1}', CONFIG.get('TIMEOUTS', 'DB_CONNECTION_ERROR'))\
            .replace('{2}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if error_type == 'sensor_error':
        message = message\
            .replace('{0}', socket.gethostname())\
            .replace('{1}', CONFIG.get('TIMEOUTS', 'DB_CONNECTION_ERROR'))\
            .replace('{2}', error_message)\
            .replace('{3}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    LOGGER.info('Sending email')
    sendmail.send(subject, message)


def check_database():
    # If returns false an email will be sent
    try:
        global DB_CONNECTION
        DB_CONNECTION = psycopg2.connect(DB_CONNECTION_STRING)
        global DB_CURSOR
        DB_CURSOR = DB_CONNECTION.cursor()
        LOGGER.debug('Connected to the database')

        try:
            os.remove(TEMP_FILE)
            LOGGER.debug('Removing temp file')
        except Exception:
            pass

        return True
    except Exception:
        LOGGER.error('Cannot connect to the database')
        number_of_lines = 0
        lines = []

        try:
            r_file = open(TEMP_FILE, 'r')
            lines = r_file.readlines()
            number_of_lines = len(lines)
            r_file.close()
            print(lines)
            LOGGER.info('Found temporary file with {} lines'.format(number_of_lines))
        except FileNotFoundError:
            LOGGER.debug('No temporary file found')

        file = open(TEMP_FILE, 'a+')

        if number_of_lines == 0:
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            file.close()
            return True

        if 'email sent' in lines[number_of_lines - 1]:
            LOGGER.info('Email already sent about database connection error')
            file.close()
            return True

        start_datetime = datetime.strptime(lines[0], '%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.strptime(lines[number_of_lines - 1], '%Y-%m-%d %H:%M:%S')
        difference_in_minutes = int((end_datetime - start_datetime).total_seconds() / 60.0)

        timeout = float(CONFIG.get('TIMEOUTS', 'DB_CONNECTION_ERROR'))
        if int(timeout / 2) == difference_in_minutes:
            LOGGER.info('Restarting postgresql service')
            os.system('sudo systemctl restart postgresql')

        if timeout < difference_in_minutes:
            file.write('\n')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            file.close()
            return True
        else:
            LOGGER.info('Reached database connection error timeout')
            file.write('\n')
            file.write('email sent')
            file.close()
            return False


def check_last_heartbeat():
    LOGGER.debug('Checking sensors ...')
    heartbeat_errors = {}
    timeout = float(CONFIG.get('TIMEOUTS', 'SENSOR_CONNECTION_ERROR'))
    for sensor in json.loads(CONFIG.get('HEARTBEAT', 'SENSORS')):
        DB_CURSOR.execute('SELECT '
                          '  name, '
                          '  timestamp '
                          'FROM '
                          '  monitoring.sensor_data '
                          'WHERE '
                          '  mac_address = %s '
                          'ORDER BY '
                          '  timestamp DESC '
                          'LIMIT 1', [sensor])
        row = DB_CURSOR.fetchone()
        name = row[0]
        timestamp = row[1]
        LOGGER.debug(name + '(' + sensor + ') last connection: ' + timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        now = datetime.now()
        difference_in_minutes = int((now - timestamp).total_seconds() / 60.0)
        heartbeat_errors[sensor] = {
            'name': name,
            'half': int(timeout / 2) == difference_in_minutes,
            'full': int(timeout) == difference_in_minutes
        }

    restart_needed = True
    email_needed = []
    error_message = ''
    for sensor in heartbeat_errors:
        restart_needed &= heartbeat_errors[sensor]['half']
        if heartbeat_errors[sensor]['full']:
            email_needed.append(sensor)
            error_message += 'Lost connection with ' + heartbeat_errors[sensor]['name'] + '(' + sensor + ')<br />\n'

    if restart_needed:
        LOGGER.info('Restarting bluetooth service')
        os.system('sudo systemctl restart bluetooth')
    elif len(email_needed) == len(heartbeat_errors):
        LOGGER.error('Lost connection with every sensor')
        send_mail('sensor_error', 'Lost connection with every sensor!')
    elif len(email_needed) > 0:
        LOGGER.error(error_message)
        send_mail('sensor_error', error_message)


def init():
    logging.basicConfig(filename=LOG_FILE, format=LOGGER_FORMAT, level=logging.DEBUG)
    global LOGGER
    LOGGER = logging.getLogger('database_monitoring')

    global CONFIG
    CONFIG = configparser.ConfigParser()
    CONFIG.read('/mnt/dev/monitoring/Database_monitoring/database_monitoring.conf')


def main():
    if not check_database():
        send_mail('db_error', None)
        return

    check_last_heartbeat()

    DB_CURSOR.close()
    DB_CONNECTION.close()


if __name__ == '__main__':
    # time.sleep(45)
    init()
    main()
