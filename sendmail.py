#!/usr/bin/env python3

import configparser
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send(subject, message_body):
    # Reading config file
    config = configparser.ConfigParser()
    config.read('database_monitoring.conf')

    # Mail settings
    message = MIMEMultipart('html')
    message['Subject'] = subject
    message['From'] = config.get('GMAIL', 'FROM_ADDRESS')
    message['To'] = config.get('GMAIL', 'TO_ADDRESS')
    message.attach(MIMEText(message_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(config.get('GMAIL', 'SERVER'), config.get('GMAIL', 'PORT'), context=context) as server:
        server.login(config.get('GMAIL', 'FROM_ADDRESS'), config.get('GMAIL', 'PASSWORD'))
        server.sendmail(
            config.get('GMAIL', 'FROM_ADDRESS'), config.get('GMAIL', 'TO_ADDRESS'), message.as_string()
        )
