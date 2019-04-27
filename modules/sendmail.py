#!/usr/bin/env python3

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SendMail:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('SendMail')

    def send(self, subject, message_body):
        server = self.config.get('GMAIL', 'SERVER')
        port = self.config.get('GMAIL', 'PORT')
        password = self.config.get('GMAIL', 'PASSWORD')
        from_address = self.config.get('GMAIL', 'FROM_ADDRESS')
        to_address = self.config.get('GMAIL', 'TO_ADDRESS')

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
