#!/usr/bin/env python3

import json
import logging
from datetime import datetime


class Sensors:
    config_group_battery = 'BATTERY_LEVELS'
    config_group_temperature = 'TEMPERATURE_LEVELS'
    config_group_humidity = 'HUMIDITY_LEVELS'
    config_group_subjects = 'SUBJECTS'
    battery_warning = 'BATTERY_WARNING'
    battery_error = 'BATTERY_ERROR'
    battery_critical = 'BATTERY_CRITICAL'
    temperature_min = 'TEMPERATURE_MIN'
    temperature_min_cooldown = 'TEMPERATURE_MIN_COOLDOWN'
    temperature_max = 'TEMPERATURE_MAX'
    temperature_max_cooldown = 'TEMPERATURE_MAX_COOLDOWN'
    humidity_min = 'HUMIDITY_MIN'
    humidity_min_cooldown = 'HUMIDITY_MIN_COOLDOWN'
    humidity_max = 'HUMIDITY_MAX'
    humidity_max_cooldown = 'HUMIDITY_MAX_COOLDOWN'

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
        level_warning = float(self.config.get(self.config_group_battery, self.battery_warning))
        level_error = float(self.config.get(self.config_group_battery, self.battery_error))
        level_critical = float(self.config.get(self.config_group_battery, self.battery_critical))

        for sensor in self.heartbeats:
            if sensor not in self.heartbeat_errors:
                battery_level = self.database.get_sensor_battery_status(sensor)
                name = self.heartbeats[sensor]['name']
                if level_warning < battery_level:
                    self.handle_normal_battery(sensor, name)
                if level_error < battery_level <= level_warning:
                    self.handle_warning_battery(sensor, name, battery_level, level_warning)
                if level_critical < battery_level <= level_error:
                    self.handle_error_battery(sensor, name, battery_level, level_error)
                if battery_level <= level_critical:
                    self.handle_critical_battery(sensor, name, battery_level, level_critical)

    def handle_normal_battery(self, sensor, name):
        self.logger.debug('{0}({1})s battery level is ok'.format(sensor, name))
        email_notification = self.database.get_email_alert_notification(sensor, self.battery_critical)
        if email_notification:
            self.database.set_email_alert_notification(sensor, self.battery_critical)

    def handle_warning_battery(self, sensor, name, battery_level, level_warning):
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

    def handle_error_battery(self, sensor, name, battery_level, level_error):
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

    def handle_critical_battery(self, sensor, name, battery_level, level_critical):
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

    def check_temperature_status(self):
        self.logger.debug('Checking sensors\' temperature status ...')
        level_min = float(self.config.get(self.config_group_temperature, self.temperature_min))
        level_min_cooldown = float(self.config.get(self.config_group_temperature, self.temperature_min_cooldown))
        level_max = float(self.config.get(self.config_group_temperature, self.temperature_max))
        level_max_cooldown = float(self.config.get(self.config_group_temperature, self.temperature_max_cooldown))

        for sensor in self.heartbeats:
            if sensor not in self.heartbeat_errors:
                temperature = self.database.get_sensor_temperature(sensor)
                name = self.heartbeats[sensor]['name']
                if level_min < temperature < level_max:
                    self.handle_normal_temperature(sensor, name, temperature, level_min_cooldown, level_max_cooldown)
                if temperature <= level_min:
                    self.handle_low_temperature(sensor, name, temperature, level_min)
                if level_max <= temperature:
                    self.handle_high_temperature(sensor, name, temperature, level_max)

    def handle_normal_temperature(self, sensor, name, temperature, level_min_cooldown, level_max_cooldown):
        self.logger.debug('{0}({1})s temperature is ok'.format(sensor, name))
        email_notification = self.database.get_email_alert_notification(sensor, self.temperature_min)
        in_cooldown_zone = temperature <= level_min_cooldown
        if email_notification and not in_cooldown_zone:
            self.database.set_email_alert_notification(sensor, self.temperature_min)
        email_notification = self.database.get_email_alert_notification(sensor, self.temperature_max)
        in_cooldown_zone = temperature >= level_max_cooldown
        if email_notification and not in_cooldown_zone:
            self.database.set_email_alert_notification(sensor, self.temperature_max)

    def handle_low_temperature(self, sensor, name, temperature, level_min):
        self.logger.warning('{0}({1})s temperature is under {2}°C'.format(sensor, name, level_min))
        email_notification = self.database.get_email_alert_notification(sensor, self.temperature_min)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject_temperature(self.temperature_min),
                self.get_mail_message_temperature(sensor, name, temperature)
            )
            self.database.set_email_alert_notification(sensor, self.temperature_min)

    def handle_high_temperature(self, sensor, name, temperature, level_max):
        self.logger.warning('{0}({1})s temperature is above {2}°C'.format(sensor, name, level_max))
        email_notification = self.database.get_email_alert_notification(sensor, self.temperature_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject_temperature(self.temperature_max),
                self.get_mail_message_temperature(sensor, name, temperature)
            )
            self.database.set_email_alert_notification(sensor, self.temperature_max)

    def check_humidity_status(self):
        self.logger.debug('Checking sensors\' humidity status ...')
        level_min = float(self.config.get(self.config_group_humidity, self.humidity_min))
        level_min_cooldown = float(self.config.get(self.config_group_humidity, self.humidity_min_cooldown))
        level_max = float(self.config.get(self.config_group_humidity, self.humidity_max))
        level_max_cooldown = float(self.config.get(self.config_group_humidity, self.humidity_max_cooldown))

        for sensor in self.heartbeats:
            if sensor not in self.heartbeat_errors:
                humidity = self.database.get_sensor_humidity(sensor)
                name = self.heartbeats[sensor]['name']
                if level_min < humidity < level_max:
                    self.handle_normal_humidity(sensor, name, humidity, level_min_cooldown, level_max_cooldown)
                if humidity <= level_min:
                    self.handle_low_humidity(sensor, name, humidity, level_min)
                if level_max <= humidity:
                    self.handle_high_humidity(sensor, name, humidity, level_max)

    def handle_normal_humidity(self, sensor, name, humidity, level_min_cooldown, level_max_cooldown):
        self.logger.debug('{0}({1})s humidity is ok'.format(sensor, name))
        email_notification = self.database.get_email_alert_notification(sensor, self.humidity_min)
        in_cooldown_zone = humidity <= level_min_cooldown
        if email_notification and not in_cooldown_zone:
            self.database.set_email_alert_notification(sensor, self.humidity_min)
        email_notification = self.database.get_email_alert_notification(sensor, self.humidity_max)
        in_cooldown_zone = humidity >= level_max_cooldown
        if email_notification and not in_cooldown_zone:
            self.database.set_email_alert_notification(sensor, self.humidity_max)

    def handle_low_humidity(self, sensor, name, humidity, level_min):
        self.logger.warning('{0}({1})s humidity is under {2}%'.format(sensor, name, level_min))
        email_notification = self.database.get_email_alert_notification(sensor, self.humidity_min)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject_humidity(self.humidity_min),
                self.get_mail_message_humidity(sensor, name, humidity)
            )
            self.database.set_email_alert_notification(sensor, self.humidity_min)

    def handle_high_humidity(self, sensor, name, humidity, level_max):
        self.logger.warning('{0}({1})s humidity is above {2}%'.format(sensor, name, level_max))
        email_notification = self.database.get_email_alert_notification(sensor, self.humidity_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject_humidity(self.humidity_max),
                self.get_mail_message_humidity(sensor, name, humidity)
            )
            self.database.set_email_alert_notification(sensor, self.humidity_max)

    def get_mail_subject_battery(self, level):
        return {
            self.battery_warning: self.config.get(self.config_group_subjects, self.battery_warning),
            self.battery_error: self.config.get(self.config_group_subjects, self.battery_error),
            self.battery_critical: self.config.get(self.config_group_subjects, self.battery_critical)
        }[level]

    def get_mail_subject_temperature(self, level):
        return {
            self.temperature_min: self.config.get(self.config_group_subjects, self.temperature_min),
            self.temperature_max: self.config.get(self.config_group_subjects, self.temperature_max)
        }[level]

    def get_mail_subject_humidity(self, level):
        return {
            self.humidity_min: self.config.get(self.config_group_subjects, self.humidity_min),
            self.humidity_max: self.config.get(self.config_group_subjects, self.humidity_max)
        }[level]

    @staticmethod
    def get_mail_message_battery(sensor, sensor_name, battery_level):
        return \
            '<html>' \
            '  <body>' \
            '    <p>The {0}({1}) sensors battery level is {2}%</p>' \
            '    <p>{3}</p>' \
            '  </body>' \
            '</html>'.format(sensor, sensor_name, battery_level, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    @staticmethod
    def get_mail_message_temperature(sensor, sensor_name, temperature):
        return \
            '<html>' \
            '  <body>' \
            '    <p>The {0}({1}) sensors temperature is {2}°C</p>' \
            '    <p>{3}</p>' \
            '  </body>' \
            '</html>'.format(sensor, sensor_name, temperature, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    @staticmethod
    def get_mail_message_humidity(sensor, sensor_name, humidity):
        return \
            '<html>' \
            '  <body>' \
            '    <p>The {0}({1}) sensors humidity is {2}%</p>' \
            '    <p>{3}</p>' \
            '  </body>' \
            '</html>'.format(sensor, sensor_name, humidity, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
