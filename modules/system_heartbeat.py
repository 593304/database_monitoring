#!/usr/bin/env python3

import logging
import socket
from datetime import datetime


class SystemHeartbeat:
    config_group_system = 'SYSTEM_VALUES'
    config_group_subjects = 'SUBJECTS'
    cpu_temp_max = 'CPU_TEMP_MAX'
    cpu_usage_max = 'CPU_USAGE_MAX'
    mem_usage_max = 'MEM_USAGE_MAX'
    sd_usage_max = 'SD_USAGE_MAX'
    dev_usage_max = 'DEV_USAGE_MAX'
    cloud_usage_max = 'CLOUD_USAGE_MAX'
    nas_usage_max = 'NAS_USAGE_MAX'

    def __init__(self, config, database, send_mail):
        self.config = config
        self.database = database
        self.send_mail = send_mail
        self.logger = logging.getLogger('SystemHeartbeat')
        self.heartbeat = self.database.get_system_last_heartbeat()
        self.hostname = socket.gethostname()

    def check_cpu(self):
        cpu_temp = self.heartbeat['cpu_temp_celsius']
        cpu_max_temp = float(self.config.get(self.config_group_system, self.cpu_temp_max))
        cpu_max_usage = float(self.config.get(self.config_group_system, self.cpu_usage_max))

        if cpu_temp < cpu_max_temp:
            self.handle_normal_cpu_temp()
        else:
            self.handle_high_cpu_temp(cpu_temp, cpu_max_temp)

        cpu0_usage = self.heartbeat['cpu0_usage_percent']
        if cpu0_usage < cpu_max_usage:
            self.handle_normal_cpu_usage('0')
        else:
            self.handle_high_cpu_usage('0', cpu0_usage, cpu_max_usage)

        cpu1_usage = self.heartbeat['cpu1_usage_percent']
        if cpu1_usage < cpu_max_usage:
            self.handle_normal_cpu_usage('1')
        else:
            self.handle_high_cpu_usage('1', cpu1_usage, cpu_max_usage)

        cpu2_usage = self.heartbeat['cpu2_usage_percent']
        if cpu2_usage < cpu_max_usage:
            self.handle_normal_cpu_usage('2')
        else:
            self.handle_high_cpu_usage('2', cpu2_usage, cpu_max_usage)

        cpu3_usage = self.heartbeat['cpu3_usage_percent']
        if cpu3_usage < cpu_max_usage:
            self.handle_normal_cpu_usage('3')
        else:
            self.handle_high_cpu_usage('3', cpu3_usage, cpu_max_usage)

    def handle_normal_cpu_temp(self):
        self.logger.debug('{0}s CPU temperature is ok'.format(self.hostname))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.cpu_temp_max)
        if email_notification:
            self.database.set_email_alert_notification(self.hostname, self.cpu_temp_max)

    def handle_high_cpu_temp(self, cpu_temp, cpu_max_temp):
        self.logger.warning('{0}s CPU temperature is above {1}°C'.format(self.hostname, cpu_max_temp))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.cpu_temp_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject(self.cpu_temp_max),
                self.get_mail_message(self.cpu_temp_max, {'cpu_temp': cpu_temp})
            )
            self.database.set_email_alert_notification(self.hostname, self.cpu_temp_max)

    def handle_normal_cpu_usage(self, core):
        self.logger.debug('{0}s CPU-{1} usage is ok'.format(self.hostname, core))
        email_notification = self.database.get_email_alert_notification(self.hostname + '_' + core, self.cpu_usage_max)
        if email_notification:
            self.database.set_email_alert_notification(self.hostname + '_' + core, self.cpu_usage_max)

    def handle_high_cpu_usage(self, core, cpu_usage, cpu_max_usage):
        self.logger.warning('{0}s CPU-{1} usage is above {2}%'.format(self.hostname, core, cpu_max_usage))
        email_notification = self.database.get_email_alert_notification(self.hostname + '_' + core, self.cpu_usage_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject(self.cpu_usage_max),
                self.get_mail_message(self.cpu_usage_max, {'core': core, 'cpu_usage': cpu_usage})
            )
            self.database.set_email_alert_notification(self.hostname + '_' + core, self.cpu_usage_max)

    def check_memory(self):
        mem_usage = (self.heartbeat['mem_usage_mb'] / self.heartbeat['mem_total_mb']) * 100
        mem_max_usage = float(self.config.get(self.config_group_system, self.mem_usage_max))

        if mem_usage < mem_max_usage:
            self.handle_normal_mem_usage()
        else:
            self.handle_high_mem_usage(mem_usage, mem_max_usage)

    def handle_normal_mem_usage(self):
        self.logger.debug('{0}s memory usage is ok'.format(self.hostname))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.mem_usage_max)
        if email_notification:
            self.database.set_email_alert_notification(self.hostname, self.mem_usage_max)

    def handle_high_mem_usage(self, mem_usage, mem_max_usage):
        self.logger.warning('{0}s memory usage is above {1}%'.format(self.hostname, mem_max_usage))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.mem_usage_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject(self.mem_usage_max),
                self.get_mail_message(self.mem_usage_max, {'mem_usage': mem_usage})
            )
            self.database.set_email_alert_notification(self.hostname, self.mem_usage_max)

    def check_sd_card(self):
        sd_usage = (self.heartbeat['sd_card_usage_gb'] / self.heartbeat['sd_card_total_gb']) * 100
        sd_max_usage = float(self.config.get(self.config_group_system, self.sd_usage_max))

        if sd_usage < sd_max_usage:
            self.handle_normal_sd_usage()
        else:
            self.handle_high_sd_usage(sd_usage, sd_max_usage)

    def handle_normal_sd_usage(self):
        self.logger.debug('{0}s SD card usage is ok'.format(self.hostname))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.sd_usage_max)
        if email_notification:
            self.database.set_email_alert_notification(self.hostname, self.sd_usage_max)

    def handle_high_sd_usage(self, sd_usage, sd_max_usage):
        self.logger.warning('{0}s SD card usage is above {1}%'.format(self.hostname, sd_max_usage))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.sd_usage_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject(self.sd_usage_max),
                self.get_mail_message(self.sd_usage_max, {'sd_usage': sd_usage})
            )
            self.database.set_email_alert_notification(self.hostname, self.sd_usage_max)

    def check_dev_partition(self):
        dev_usage = (self.heartbeat['dev_usage_gb'] / self.heartbeat['dev_total_gb']) * 100
        dev_max_usage = float(self.config.get(self.config_group_system, self.dev_usage_max))

        if dev_usage < dev_max_usage:
            self.handle_normal_dev_usage()
        else:
            self.handle_high_dev_usage(dev_usage, dev_max_usage)

    def handle_normal_dev_usage(self):
        self.logger.debug('{0}s DEV partition usage is ok'.format(self.hostname))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.dev_usage_max)
        if email_notification:
            self.database.set_email_alert_notification(self.hostname, self.dev_usage_max)

    def handle_high_dev_usage(self, dev_usage, dev_max_usage):
        self.logger.warning('{0}s DEV partition usage is above {1}%'.format(self.hostname, dev_max_usage))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.dev_usage_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject(self.dev_usage_max),
                self.get_mail_message(self.dev_usage_max, {'dev_usage': dev_usage})
            )
            self.database.set_email_alert_notification(self.hostname, self.dev_usage_max)

    def check_cloud_partition(self):
        cloud_usage = (self.heartbeat['cloud_usage_gb'] / self.heartbeat['cloud_total_gb']) * 100
        cloud_max_usage = float(self.config.get(self.config_group_system, self.cloud_usage_max))

        if cloud_usage < cloud_max_usage:
            self.handle_normal_cloud_usage()
        else:
            self.handle_high_cloud_usage(cloud_usage, cloud_max_usage)

    def handle_normal_cloud_usage(self):
        self.logger.debug('{0}s Cloud partition usage is ok'.format(self.hostname))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.cloud_usage_max)
        if email_notification:
            self.database.set_email_alert_notification(self.hostname, self.cloud_usage_max)

    def handle_high_cloud_usage(self, cloud_usage, cloud_max_usage):
        self.logger.warning('{0}s Cloud partition usage is above {1}%'.format(self.hostname, cloud_max_usage))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.cloud_usage_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject(self.cloud_usage_max),
                self.get_mail_message(self.cloud_usage_max, {'cloud_usage': cloud_usage})
            )
            self.database.set_email_alert_notification(self.hostname, self.cloud_usage_max)

    def check_nas_partition(self):
        nas_usage = (self.heartbeat['nas_usage_gb'] / self.heartbeat['nas_total_gb']) * 100
        nas_max_usage = float(self.config.get(self.config_group_system, self.nas_usage_max))

        if nas_usage < nas_max_usage:
            self.handle_normal_nas_usage()
        else:
            self.handle_high_nas_usage(nas_usage, nas_max_usage)

    def handle_normal_nas_usage(self):
        self.logger.debug('{0}s NAS partition usage is ok'.format(self.hostname))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.nas_usage_max)
        if email_notification:
            self.database.set_email_alert_notification(self.hostname, self.nas_usage_max)

    def handle_high_nas_usage(self, nas_usage, nas_max_usage):
        self.logger.warning('{0}s NAS partition usage is above {1}%'.format(self.hostname, nas_max_usage))
        email_notification = self.database.get_email_alert_notification(self.hostname, self.nas_usage_max)
        if email_notification:
            self.logger.debug('E-mail notification already sent')
        else:
            self.logger.info('E-mail notification needed')
            self.send_mail.send(
                self.get_mail_subject(self.nas_usage_max),
                self.get_mail_message(self.nas_usage_max, {'nas_usage': nas_usage})
            )
            self.database.set_email_alert_notification(self.hostname, self.nas_usage_max)

    def get_mail_subject(self, subject_type):
        return {
            self.cpu_temp_max: self.config.get(self.config_group_subjects, self.cpu_temp_max),
            self.cpu_usage_max: self.config.get(self.config_group_subjects, self.cpu_usage_max),
            self.mem_usage_max: self.config.get(self.config_group_subjects, self.mem_usage_max),
            self.sd_usage_max: self.config.get(self.config_group_subjects, self.sd_usage_max),
            self.dev_usage_max: self.config.get(self.config_group_subjects, self.dev_usage_max),
            self.cloud_usage_max: self.config.get(self.config_group_subjects, self.cloud_usage_max),
            self.nas_usage_max: self.config.get(self.config_group_subjects, self.nas_usage_max)
        }[subject_type]

    def get_mail_message(self, subject_type, params):
        if subject_type == self.cpu_temp_max:
            params['core'] = ''
            params['cpu_usage'] = ''
            params['mem_usage'] = 0
            params['sd_usage'] = 0
            params['dev_usage'] = 0
            params['cloud_usage'] = 0
            params['nas_usage'] = 0
        elif subject_type == self.cpu_usage_max:
            params['cpu_temp'] = ''
            params['mem_usage'] = 0
            params['sd_usage'] = 0
            params['dev_usage'] = 0
            params['cloud_usage'] = 0
            params['nas_usage'] = 0
        elif subject_type == self.mem_usage_max:
            params['core'] = ''
            params['cpu_usage'] = ''
            params['cpu_temp'] = ''
            params['sd_usage'] = 0
            params['dev_usage'] = 0
            params['cloud_usage'] = 0
            params['nas_usage'] = 0
        elif subject_type == self.sd_usage_max:
            params['core'] = ''
            params['cpu_usage'] = ''
            params['cpu_temp'] = ''
            params['mem_usage'] = 0
            params['dev_usage'] = 0
            params['cloud_usage'] = 0
            params['nas_usage'] = 0
        elif subject_type == self.dev_usage_max:
            params['core'] = ''
            params['cpu_usage'] = ''
            params['cpu_temp'] = ''
            params['mem_usage'] = 0
            params['sd_usage'] = 0
            params['cloud_usage'] = 0
            params['nas_usage'] = 0
        elif subject_type == self.cloud_usage_max:
            params['core'] = ''
            params['cpu_usage'] = ''
            params['cpu_temp'] = ''
            params['mem_usage'] = 0
            params['sd_usage'] = 0
            params['dev_usage'] = 0
            params['nas_usage'] = 0
        elif subject_type == self.nas_usage_max:
            params['core'] = ''
            params['cpu_usage'] = ''
            params['cpu_temp'] = ''
            params['mem_usage'] = 0
            params['sd_usage'] = 0
            params['dev_usage'] = 0
            params['cloud_usage'] = 0

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return {
            self.cpu_temp_max:
                '<html>'
                '  <body>'
                '    <p>The {0}s CPU temperature is {1}°C</p>'
                '    <p>{2}</p>'
                '  </body>'
                '</html>'.format(self.hostname, params['cpu_temp'], now),
            self.cpu_usage_max:
                '<html>'
                '  <body>'
                '    <p>The {0}s CPU-{1} usage is {2}%</p>'
                '    <p>{3}</p>'
                '  </body>'
                '</html>'.format(self.hostname, params['core'], params['cpu_usage'], now),
            self.mem_usage_max:
                '<html>'
                '  <body>'
                '    <p>The {0}s memory usage is {1:.2f}%</p>'
                '    <p>{2}</p>'
                '  </body>'
                '</html>'.format(self.hostname, params['mem_usage'], now),
            self.sd_usage_max:
                '<html>'
                '  <body>'
                '    <p>The {0}s SD card usage is {1:.2f}%</p>'
                '    <p>{2}</p>'
                '  </body>'
                '</html>'.format(self.hostname, params['sd_usage'], now),
            self.dev_usage_max:
                '<html>'
                '  <body>'
                '    <p>The {0}s DEV partition usage is {1:.2f}%</p>'
                '    <p>{2}</p>'
                '  </body>'
                '</html>'.format(self.hostname, params['dev_usage'], now),
            self.cloud_usage_max:
                '<html>'
                '  <body>'
                '    <p>The {0}s Cloud partition usage is {1:.2f}%</p>'
                '    <p>{2}</p>'
                '  </body>'
                '</html>'.format(self.hostname, params['cloud_usage'], now),
            self.nas_usage_max:
                '<html>'
                '  <body>'
                '    <p>The {0}s NAS partition usage is {1:.2f}%</p>'
                '    <p>{2}</p>'
                '  </body>'
                '</html>'.format(self.hostname, params['nas_usage'], now)
        }[subject_type]
