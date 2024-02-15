import logging
import os
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
from datetime import datetime
import sys
from modules.IFAPAMetos import IFAPAMetos
from modules.HopuWSprocessor import HopuWSprocessor
from modules.ModdedHopuWSprocessor import ModdedHopuWSprocessor

logger = logging.getLogger('')
logger.setLevel(logging.INFO)
format = logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(format)
logger.addHandler(ch)

handler = RotatingFileHandler('log.txt', maxBytes=500*1024, backupCount=2)
handler.setFormatter(format)
logger.addHandler(handler)

logger.info("Arrancado")

mqttBroker ="meteocdg.uca.es"
if 'DEBUG' in os.environ:
    mqttUser = "mqttwsdebug"
else:
    mqttUser = "mqttws"
mqttPass = "ICEI-Lab1"
clientId = f"WSProcessor{str(datetime.now().hour)}{str(datetime.now().minute)}{str(datetime.now().second)}"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT Broker!")
        HopuWSprocessor(client)
        ModdedHopuWSprocessor(client)
        IFAPAMetos(client)
    else:
        logger.error("Failed to connect, return code %d\n", rc)


def connect_mqtt():
    client = mqtt.Client(clientId)
    client.username_pw_set(mqttUser, mqttPass)
    client.on_connect = on_connect
    client.connect(mqttBroker)
    return client


def run():
    try:
        client = connect_mqtt()
        client.loop_forever()
    except Exception as e:
        logger.exception(str(e))


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        logger.exception(str(e))
