from datetime import datetime
from modules.environAPI_client.environClient import APIClass
import logging
import os
import json

cliente = APIClass()

logger = logging.getLogger()

class HopuWSprocessor:

    def __init__(self, client):

        self.client = client
        self.client.subscribe("WS/+/attrs")
        self.client.on_connect = self.on_connect
        #self.client.on_message = self.on_message
        self.client.message_callback_add("WS/+/attrs", self.on_message)

        self.excluded_vars = ['thswIndex', 'windChill', 'heatIndex', 'dewPoint', 'precipitation',
                              'windDirectionGustAverage10', 'windSpeed', 'batteryAverageCurrent', 'batteryVoltage',
                              'soilTemperature2', 'soilHumidity2', 'soilConductivity2', 'evapotranspirationDaily']

        self.unprocessed_vars = []

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
            if staID not in self.dict_estaciones.keys():
                logger.info(f"La estación {staID} no está en la base de datos. Ignorando.")
                return -1

            data = json.loads(str(payload))
            datos = []
            now = str(datetime.utcnow())
            logger.info(f"############### Procesando Hopu {staID} ###############")
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
                    logger.debug(f"{staID}: Precipitation15 {v} mm/m2")

                    if v != '0.00':
                        respuesta = cliente.get_datos_variable_estacion_entre_fechas(station_id=self.dict_estaciones[staID], var_name='PLV1', delta='14m')
                        if respuesta['status_code'] == 200:
                            ultimos_datos = respuesta['datos']
                            if len(ultimos_datos) >= 2:
                                nuevo_v = float(v)
                                for ud in ultimos_datos:
                                    nuevo_v = nuevo_v - float(ud['value'])
                                print(f"Nuevo valor {nuevo_v}")
                                if nuevo_v < 0:
                                    logger.error(f"Precipitación PLV1 Calculada de la estación {staID} es <0: {nuevo_v}")
                                    v = 0
                                else:
                                    v = nuevo_v

                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PLV1', value=v, ts=now))
                    logger.debug(f"{staID}: Precitación(Corregida) {v} mm/m2")

                else:
                    if k not in self.unprocessed_vars:
                        self.unprocessed_vars.append(k)
                        print(f"Variables no procesadas: {self.unprocessed_vars}")

            if len(datos) > 0:
                lista_datos = {"datos": datos}
                if not 'DEBUG' in os.environ:
                    respuesta = cliente.send_station_data(lista_datos)
                    logger.info(f"{staID}: {respuesta}")
                logger.info("################# FIN DEL PROCESAMIENTO #####################")
        except Exception as e:
            logger.error(e)
