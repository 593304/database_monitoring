#!/usr/bin/env python3

import json
import logging
import os
import socket
from datetime import datetime


class Heartbeat:
    def __init__(self, config, database, send_mail):
        self.config = config
        self.database = database
        self.send_mail = send_mail
        self.logger = logging.getLogger('Heartbeat')
        self.heartbeats = {}

    # If returns false an email will be sent
    def check_last_heartbeat(self):
        self.logger.debug('Checking sensors ...')
        heartbeats = {}
        timeout = float(self.config.get('TIMEOUTS', 'SENSOR_CONNECTION_ERROR'))
        for sensor in json.loads(self.config.get('HEARTBEAT', 'SENSORS')):
            sensor_last_heartbeat = self.database.get_sensor_last_heartbeat(sensor)
            name = sensor_last_heartbeat[0]['name']
            timestamp = sensor_last_heartbeat[0]['timestamp']
            self.logger.debug('  ' + name +
                              '(' + sensor + ') last connection: ' + timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            now = datetime.now()
            difference_in_minutes = int((now - timestamp).total_seconds() / 60.0)
            heartbeats[sensor] = {
                'name': name,
                'half': int(timeout / 2) == difference_in_minutes,
                'full': int(timeout) == difference_in_minutes,
                'working': difference_in_minutes < int(timeout / 2),
                'error': difference_in_minutes > int(timeout)
            }

        self.heartbeats = heartbeats

        restart_needed = True
        sensors_in_error_state = True
        email_needed = []
        error_message = ''
        for sensor in heartbeats:
            restart_needed &= heartbeats[sensor]['half']
            sensors_in_error_state &= heartbeats[sensor]['error']
            if heartbeats[sensor]['full']:
                email_needed.append(sensor)
                error_message += 'Lost connection with ' + heartbeats[sensor]['name'] + '(' + sensor + ')<br />\n'

        if restart_needed:
            self.logger.info('Restarting bluetooth service')
            os.system('sudo systemctl restart bluetooth')
        elif len(email_needed) == len(heartbeats):
            self.logger.error('Lost connection with every sensor')
            self.send_error_mail('Lost connection with every sensor!')
        elif len(email_needed) > 0:
            self.logger.error(error_message)
            self.send_error_mail(error_message)
            return False
        elif sensors_in_error_state:
            self.logger.error('Lost connection with every sensor, e-mail already sent')
            return False

        return True

    def get_mail_subject(self):
        return self.config.get('SUBJECTS', 'SENSOR_CONNECTION_ERROR')

    def get_mail_message(self):
        return '<html>'\
               '  <body>'\
               '    <p>Couldn\'t connect to the sensor(s) on {0} in the last {1} minutes</p>'\
               '    <p>{2}</p>'\
               '    <p>{3}</p>'\
               '  </body>'\
               '</html>'

    def send_error_mail(self, error_message):
        self.logger.info('Sending email')

        message = self.get_mail_message() \
            .replace('{0}', socket.gethostname()) \
            .replace('{1}', self.config.get('TIMEOUTS', 'DB_CONNECTION_ERROR')) \
            .replace('{2}', error_message) \
            .replace('{3}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.send_mail.send(self.get_mail_subject(), message)
