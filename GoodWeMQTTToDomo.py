#!/usr/bin/python -tt
from __future__ import absolute_import
from __future__ import print_function

import configparser
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import paho.mqtt.client as mqtt
#import simplejson as json
import json
import time
import os
from Json2Domo import Json2Domo

millis = lambda: int(round(time.time() * 1000))

class GoodweJsonToDomoicz(object):
    def __init__(self):
        self.callbackCount = 0
        self.connectionCount = 0
        self.topicGoodwe = ""
        self.jsonProcessor = None
        self.logging = logging

    def mqtt_connected(self, client, userdata, flags, rc):
        self.connectionCount = self.connectionCount + 1
        self.logging.info("Connected to mqtt server with result code %d", rc)
        client.subscribe(self.topicGoodwe + "/#")

    def goodweMessage(self, client, userdata, message):
        self.callbackCount = self.callbackCount + 1
        self.jsonProcessor.goodWeMessage(message, client)

    def run_process(self, foreground):

        # logging configuration parsing
        # logging must be set up early

        config = configparser.RawConfigParser()
        config.read('/etc/goodwe2domoticz.conf')
        
        logfile = config.get("converter", "logfile", fallback="/var/log/goodwe2domototicz.log")
        loglevel = config.get("converter", "loglevel", fallback="INFO")

        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        
        # Setup logging. If we are running in the foreground we use stderr for logging, if running as forking daemon we use the logfile            
        if (foreground):
            logging.basicConfig(format='%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s', stream=sys.stderr, level=numeric_level)
        else:
            logging.basicConfig(format='%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s', filename=logfile, level=numeric_level)

        self.topicGoodwe = config.get("goodwe", "topic", fallback="goodwe")
        topicDomoticz = config.get("domoticz", "topic", fallback="domoticz")

        self.jsonProcessor = Json2Domo(self.logging, self.topicGoodwe, topicDomoticz) 

        invertersString = config.get("converter", "inverters", fallback=None)

        for inverter in invertersString.split(','):
            inverter = inverter.strip()
            logging.debug("found inverter %s", inverter)
            self.jsonProcessor.addInverter(inverter, config)
        reportingInterval = config.getfloat("converter", "reportinginterval", fallback=60)

        mqttserver = config.get("mqtt", "server", fallback="localhost")
        mqttport = config.getint("mqtt", "port", fallback=1883)
        mqttclientid = config.get("mqtt", "clientid", fallback="goodwe-converter")
        mqttusername = config.get("mqtt", "username", fallback="")
        mqttpasswd = config.get("mqtt", "password", fallback=None) 

        # connect to mqtt
        try:
            client = mqtt.Client(mqttclientid, clean_session=False, userdata = self)

            if mqttusername != "":
                client.username_pw_set(mqttusername, mqttpasswd);
                logging.debug("Using mqtt username: %s, password: %s", mqttusername, mqttpasswd)

            client.enable_logger(logging)
            client.on_message = self.goodweMessage
            client.on_connect = self.mqtt_connected
            client.connect(mqttserver,port=mqttport)
            client.loop_start()
        except Exception as e:
            logging.error("Client: %s:%s: %s",mqttserver, mqttport, e)
            return 3

        logging.info('Connecting to MQTT %s:%s as client %s', mqttserver, mqttport, mqttclientid)

        print("wating for input")
        while True:
            logging.info("(re-)Connected  %d times, received %d datagrams", self.connectionCount, self.callbackCount)
            time.sleep(reportingInterval)

		
if __name__ == "__main__":
    if len(sys.argv) != 1:
        print ("usage: %s"  % sys.argv[0])
        sys.exit(2)

    processor = GoodweJsonToDomoicz()
    retval = processor.run_process(foreground = True)
    sys.exit(retval)
