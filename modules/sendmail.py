#!/usr/bin/env python3

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SendMail:
    config_group_gmail = 'GMAIL'
    server = 'SERVER'
    port = 'PORT'
    password = 'PASSWORD'
    from_address = 'FROM_ADDRESS'
    to_address = 'TO_ADDRESS'

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('SendMail')

    def send(self, subject, message_body):
        server = self.config.get(self.config_group_gmail, self.server)
        port = self.config.get(self.config_group_gmail, self.port)
        password = self.config.get(self.config_group_gmail, self.password)
        from_address = self.config.get(self.config_group_gmail, self.from_address)
        to_address = self.config.get(self.config_group_gmail, self.to_address)

        # Mail settings
        message = MIMEMultipart('html')
        message['Subject'] = subject
        message['From'] = from_address
        message['To'] = to_address
        message.attach(MIMEText(message_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(server, port, context=context) as server:
            server.login(from_address, password)
            server.sendmail(from_address, to_address, message.as_string())
        self.logger.info("E-mail sent")
