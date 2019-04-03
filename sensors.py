#!/usr/bin/env python3

import json
import logging
from datetime import datetime


class Sensors:
    battery_warning = 'BATTERY_WARNING'
    battery_error = 'BATTERY_ERROR'
    battery_critical = 'BATTERY_CRITICAL'

    def __init__(self, config, database, send_mail, heartbeats):
        self.config = config
        self.database = database
        self.send_mail = send_mail
        self.heartbeats = heartbeats
        self.logger = logging.getLogger('Sensors')
        self.logger.debug(json.dumps({'heartbeats': heartbeats}))
        self.heartbeat_errors = []
        for sensor in heartbeats:
            if heartbeats[sensor]['error']:
                self.heartbeat_errors.append(sensor)

    def check_battery_status(self):
        self.logger.debug('Checking sensors\' battery status ...')
        level_warning = float(self.config.get('BATTERY_LEVELS', self.battery_warning))
        level_error = float(self.config.get('BATTERY_LEVELS', self.battery_error))
        level_critical = float(self.config.get('BATTERY_LEVELS', self.battery_critical))

        for sensor in self.heartbeats:
            if sensor not in self.heartbeat_errors:
                battery_level = self.database.get_sensor_battery_status(sensor)
                name = self.heartbeats[sensor]['name']
                if level_warning < battery_level:
                    self.logger.debug('{0}({1})s battery level is ok'.format(sensor, name))
                    email_notification = self.database.get_email_alert_notification(sensor, self.battery_critical)
                    if email_notification:
                        self.database.set_email_alert_notification(sensor, self.battery_critical)
                if level_error < battery_level <= level_warning:
                    self.logger.warning('{0}({1})s battery level is under {2}%'.format(sensor, name, level_warning))
                    email_notification = self.database.get_email_alert_notification(sensor, self.battery_warning)
                    if email_notification:
                        self.logger.debug('E-mail notification already sent')
                    else:
                        self.logger.info('E-mail notification needed')
                        self.send_mail.send(
                            self.get_mail_subject_battery(self.battery_warning),
                            self.get_mail_message_battery(sensor, name, battery_level)
                        )
                        self.database.set_email_alert_notification(sensor, self.battery_warning)
                if level_critical < battery_level <= level_error:
                    self.logger.error('{0}({1})s battery level is under {2}%'.format(sensor, name, level_error))
                    email_notification = self.database.get_email_alert_notification(sensor, self.battery_error)
                    if email_notification:
                        self.logger.debug('E-mail notification already sent')
                    else:
                        self.logger.info('E-mail notification needed')
                        self.send_mail.send(
                            self.get_mail_subject_battery(self.battery_error),
                            self.get_mail_message_battery(sensor, name, battery_level)
                        )
                        self.database.set_email_alert_notification(sensor, self.battery_warning)
                        self.database.set_email_alert_notification(sensor, self.battery_error)
                if battery_level <= level_critical:
                    self.logger.critical('{0}({1})s battery level is under {2}%'.format(sensor, name, level_critical))
                    email_notification = self.database.get_email_alert_notification(sensor, self.battery_critical)
                    if email_notification:
                        self.logger.debug('E-mail notification already sent')
                    else:
                        self.logger.info('E-mail notification needed')
                        self.send_mail.send(
                            self.get_mail_subject_battery(self.battery_critical),
                            self.get_mail_message_battery(sensor, name, battery_level)
                        )
                        self.database.set_email_alert_notification(sensor, self.battery_error)
                        self.database.set_email_alert_notification(sensor, self.battery_critical)

    def get_mail_subject_battery(self, level):
        return {
            self.battery_warning: self.config.get('SUBJECTS', self.battery_warning),
            self.battery_error: self.config.get('SUBJECTS', self.battery_error),
            self.battery_critical: self.config.get('SUBJECTS', self.battery_critical)
        }[level]

    def get_mail_message_battery(self, sensor, sensor_name, battery_level):
        return \
            '<html>' \
            '  <body>' \
            '    <p>The {0}({1}) sensors battery level is {2}%</p>' \
            '    <p>{3}</p>' \
            '  </body>' \
            '</html>'.format(sensor, sensor_name, battery_level, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
