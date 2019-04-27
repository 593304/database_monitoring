#!/usr/bin/env python3

import json
import logging
import os
import socket
from datetime import datetime


class SystemHeartbeat:
    def __init__(self, config, database, send_mail):
        self.config = config
        self.database = database
        self.send_mail = send_mail
        self.logger = logging.getLogger('SystemHeartbeat')
        self.heartbeat = self.database.get_system_last_heartbeat()
        print(self.heartbeat)
