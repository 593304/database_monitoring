#!/usr/bin/env python3

import logging
import os
import psycopg2
import socket
from datetime import datetime


class Database:
    config_group_db = 'DATABASE'
    config_group_timeouts = 'TIMEOUTS'
    config_group_subjects = 'SUBJECTS'
    connection_string = 'CONNECTION_STRING'
    temp_file = 'TEMP_FILE'
    db_connection_error = "DB_CONNECTION_ERROR"

    def __init__(self, config, send_mail):
        self.config = config
        self.send_mail = send_mail
        self.logger = logging.getLogger('Database')
        self.connection_string = config.get(self.config_group_db, self.connection_string)
        self.temp_file = config.get(self.config_group_db, self.temp_file)
        self.connection = None
        self.cursor = None

    # If returns false an email will be sent
    def check_status_and_connect(self):
        self.logger.debug('Checking database, with connection settings: ' + self.connection_string)
        try:
            self.connection = psycopg2.connect(self.connection_string)
            self.cursor = self.connection.cursor()
            self.logger.debug('Connected to the database')

            try:
                os.remove(self.temp_file)
                self.logger.debug('Removing temp file')
            except OSError:
                pass

            return True
        except psycopg2.Error:
            self.logger.error('Cannot connect to the database')
            number_of_lines = 0
            lines = []

            try:
                r_file = open(self.temp_file, 'r')
                lines = r_file.readlines()
                number_of_lines = len(lines)
                r_file.close()
                print(lines)
                self.logger.info('Found temporary file with {} lines'.format(number_of_lines))
            except FileNotFoundError:
                self.logger.debug('No temporary file found')

            file = open(self.temp_file, 'a+')

            if number_of_lines == 0:
                file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                file.close()
                return True

            if 'email sent' in lines[number_of_lines - 1]:
                self.logger.info('Email already sent about database connection error')
                file.close()
                return True

            start_datetime = datetime.strptime(lines[0], '%Y-%m-%d %H:%M:%S')
            end_datetime = datetime.strptime(lines[number_of_lines - 1], '%Y-%m-%d %H:%M:%S')
            difference_in_minutes = int((end_datetime - start_datetime).total_seconds() / 60.0)

            timeout = float(self.config.get(self.config_group_timeouts, self.db_connection_error))
            if int(timeout / 2) == difference_in_minutes:
                self.logger.info('Restarting postgresql service')
                os.system('sudo systemctl restart postgresql')

            if timeout < difference_in_minutes:
                file.write('\n')
                file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                file.close()
                return True
            else:
                self.logger.info('Reached database connection error timeout')
                file.write('\n')
                file.write('email sent')
                file.close()
                self.send_error_mail()
                return False

    def get_sensor_last_heartbeat(self, sensor):
        command = 'SELECT ' \
                  '  * ' \
                  'FROM ' \
                  '  monitoring.sensor_data ' \
                  'WHERE ' \
                  '  mac_address = %s ' \
                  'ORDER BY ' \
                  '  timestamp DESC ' \
                  'LIMIT 1'
        self.cursor.execute(command, [sensor])
        result = self.cursor.fetchall()

        return [dict(zip([key[0] for key in self.cursor.description], result[0]))]

    def get_system_last_heartbeat(self):
        command = 'SELECT ' \
                  '  * ' \
                  'FROM ' \
                  '  monitoring.rpi_data ' \
                  'ORDER BY ' \
                  '  timestamp DESC ' \
                  'LIMIT 1'
        self.cursor.execute(command)
        result = self.cursor.fetchall()

        return dict(zip([key[0] for key in self.cursor.description], result[0]))

    def get_sensor_battery_status(self, sensor):
        command = 'SELECT ' \
                  '  battery_percent ' \
                  'FROM ' \
                  '  monitoring.sensor_data ' \
                  'WHERE ' \
                  '  mac_address = %s ' \
                  'ORDER BY ' \
                  '  timestamp DESC ' \
                  'LIMIT 1'
        self.cursor.execute(command, [sensor])
        result = self.cursor.fetchone()

        return result[0]

    def get_sensor_temperature(self, sensor):
        command = 'SELECT ' \
                  '  room_temp_celsius ' \
                  'FROM ' \
                  '  monitoring.sensor_data ' \
                  'WHERE ' \
                  '  mac_address = %s ' \
                  'ORDER BY ' \
                  '  timestamp DESC ' \
                  'LIMIT 1'
        self.cursor.execute(command, [sensor])
        result = self.cursor.fetchone()

        return result[0]

    def get_sensor_humidity(self, sensor):
        command = 'SELECT ' \
                  '  room_humdity_percent ' \
                  'FROM ' \
                  '  monitoring.sensor_data ' \
                  'WHERE ' \
                  '  mac_address = %s ' \
                  'ORDER BY ' \
                  '  timestamp DESC ' \
                  'LIMIT 1'
        self.cursor.execute(command, [sensor])
        result = self.cursor.fetchone()

        return result[0]

    def get_email_alert_notification(self, name, alert_type):
        command = 'SELECT ' \
                  '  * ' \
                  'FROM ' \
                  '  monitoring.email_alert_sent ' \
                  'WHERE ' \
                  '  name = %s AND ' \
                  '  type = %s AND ' \
                  '  valid = TRUE'
        self.cursor.execute(command, [name, alert_type])
        result = self.cursor.fetchall()

        if len(result) == 0:
            return None
        else:
            return [dict(zip([key[0] for key in self.cursor.description], result[0]))]

    def set_email_alert_notification(self, name, alert_type):
        is_exists = self.get_email_alert_notification(name, alert_type)
        if is_exists:
            command = 'UPDATE ' \
                      '  monitoring.email_alert_sent ' \
                      'SET ' \
                      '  valid = FALSE ' \
                      'WHERE ' \
                      '  name = %s AND ' \
                      '  type = %s'
        else:
            command = 'INSERT INTO ' \
                      '  monitoring.email_alert_sent(name,type,valid,timestamp) ' \
                      'VALUES(%s,%s,True,now())'
        self.cursor.execute(command, [name, alert_type])
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def get_mail_subject(self):
        self.config.get(self.config_group_subjects, self.db_connection_error)

    @staticmethod
    def get_mail_message():
        return \
            '<html>' \
            '  <body>' \
            '    <p>Couldn\'t connect to the database on {0} in the last {1} minutes</p>' \
            '    <p>{2}</p>' \
            '  </body>' \
            '</html>'

    def send_error_mail(self):
        self.logger.info('Sending email')

        message = self.get_mail_message() \
            .replace('{0}', socket.gethostname()) \
            .replace('{1}', self.config.get(self.config_group_timeouts, self.db_connection_error)) \
            .replace('{2}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.send_mail.send(self.get_mail_subject(), message)
