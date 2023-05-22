import os

import paho.mqtt.client as mqtt
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from modules.environAPI_client.environClient import APIClass
import sys


logger = logging.getLogger('mqttWS')
logger.setLevel(logging.DEBUG)
format = logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')
handler = RotatingFileHandler('log.txt', maxBytes=500*1024, backupCount=2)
handler.setFormatter(format)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.addHandler(ch)


mqttBroker ="meteocdg.uca.es"
mqttUser = "mqttws"
mqttPass = "ICEI-Lab1"
clientId = f"WSProcessor{str(datetime.now().hour)}{str(datetime.now().minute)}"


############################
if 'DEBUG' in os.environ:
    mqttUser = "hopu1"
    mqttPass = "hopu1"
############################

cliente = APIClass()

unprocessed_vars = []


class hopuWSprocessor():

    def __init__(self, client):

        self.client = client
        self.client.subscribe("WS/+/attrs")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.excluded_vars = ['thswIndex', 'windChill', 'heatIndex', 'dewPoint', 'precipitation',
                              'windDirectionGustAverage10', 'windSpeed', 'batteryAverageCurrent', 'batteryVoltage',
                              'soilTemperature2', 'soilHumidity2', 'soilConductivity2', 'evapotranspirationDaily']

        respuesta = cliente.get_codigos_estaciones("TIC168")
        if respuesta['status_code'] == 200:
            dict_estaciones = {}
            for estacion in respuesta['estaciones']:
                dict_estaciones[estacion['codigo_estacion']]=estacion['dev_id']
            self.dict_estaciones = dict_estaciones
        else:
            logger.error(f"Respuesta incorrecta del servidor: {respuesta['status_code']}")
            self.dict_estaciones = None

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Hopu WS processor connected")
        else:
            logger.error("Failed to connect WS processor, return code %d\n", rc)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        topic = msg.topic
        logger.debug(f"Received `{payload}` from `{topic}` topic")
        try:
            staID = topic.split('/')[1]
            data = json.loads(str(payload))
            datos = []
            now = str(datetime.utcnow())
            for k, v in data.items():
                if 'crowd_' in k or k in self.excluded_vars:
                    continue
                if 'atmosphericPressure' == k:
                    logger.debug(f"{staID}: Pressión atmosférica {v}")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PRES', value=v, ts=now))
                elif 'temperature' == k:
                    logger.debug(f"{staID}: Temperatura {v} C")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='TC', value=v, ts=now))
                elif 'relativeHumidity' == k:
                    logger.debug(f"{staID}: RH {v} %")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='HUM', value=v, ts=now))
                elif 'windSpeedAverage10' == k:
                    logger.debug(f"{staID}: ANE {v} m/s")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='ANE', value=round(float(v)/3.6, 2), ts=now))
                elif 'windDirection' == k:
                    logger.debug(f"{staID}: WD {v} º")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='WV', value=v, ts=now))
                elif 'solarRadiation' == k:
                    logger.debug(f"{staID}: RH {v} W/m2")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='GHI', value=v, ts=now))
                elif 'ultravioletIndex' == k:
                    logger.debug(f"{staID}: UVI {v}")
                elif 'precipitationLast15' == k:
                    respuesta = cliente.get_datos_variable_estacion_entre_fechas(station_id=self.dict_estaciones[staID], var_name='PLV1', delta='16m')
                    if respuesta['status_code'] == 200:
                        ultimos_datos = respuesta['datos']
                        if len(ultimos_datos) > 2:
                            print('Do something')
                    
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PLV1', value=v, ts=now))
                    logger.debug(f"{staID}: Lluvia {v} mm")


                else:
                    if k not in unprocessed_vars:
                        unprocessed_vars.append(k)
                        print(f"Variables no procesadas: {unprocessed_vars}")

            if len(datos) > 0:
                lista_datos = {"datos": datos}
                respuesta = cliente.send_station_data(lista_datos)
                logger.info(f"{staID}: {respuesta}")
        except Exception as e:
            print(e)



def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
        else:
            logger.error("Failed to connect, return code %d\n", rc)

    client = mqtt.Client(clientId)
    client.username_pw_set(mqttUser, mqttPass)
    client.on_connect = on_connect
    client.connect(mqttBroker)
    return client


def run():
    client = connect_mqtt()
    hopuWSprocessor(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
