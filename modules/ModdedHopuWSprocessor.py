import logging
from datetime import datetime
from modules.environAPI_client.environClient import APIClass

import os
import json

cliente = APIClass()

logger = logging.getLogger('')



class ModdedHopuWSprocessor:
    def __init__(self, client):
        self.client = client
        self.client.subscribe("WS/+/json")
        #self.client.on_connect = self.on_connect
        #self.client.on_message = self.on_message
        self.client.message_callback_add("WS/+/json", self.on_message)
        self.excluded_vars = ['RainRate', 'WindGust', 'WindGustDirection', 'YearRain', 'MonthRain',
                              'WindSpeed', 'AvgWindSpeed2', 'BatteryStatus', 'BatteryVoltage']

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

    """
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Modded Hopu WS processor connected")
        else:
            logger.error("Failed to connect modded WS processor, return code %d\n", rc)
    """

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
            logger.info(f"############### Procesando moddedHopu {staID} ###############")
            for k, v in data.items():
                if k in self.excluded_vars:
                    continue
                if 'Barometer' == k:
                    logger.debug(f"{staID}: Pressión atmosférica {v}")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PRES', value=v, ts=now))
                elif 'Temperature' == k:
                    logger.debug(f"{staID}: Temperatura {v} C")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='TC', value=round(v,1), ts=now))
                elif 'RH' == k:
                    logger.debug(f"{staID}: RH {v} %")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='HUM', value=v, ts=now))
                elif 'AvgWindSpeed10' == k:
                    logger.debug(f"{staID}: ANE {v} m/s")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='ANE', value=round(float(v), 2), ts=now))
                elif 'WindDirection' == k:
                    logger.debug(f"{staID}: WD {v} º")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='WV', value=v, ts=now))
                elif 'SolarRadiation' == k:
                    logger.debug(f"{staID}: RH {v} W/m2")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='GHI', value=v, ts=now))
                elif 'unsentRain' == k:
                    logger.debug(f"{staID}: Precipitation {v} mm2")
                    if v < 35:
                        datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PLV1', value=v, ts=now))
                        logger.debug(f"{staID}: Precitación(Corregida) {v} mm/m2")
                    else:
                        logger.warning(f"{staID} informa de una precipitación anómala ({v} mm/m2)")
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
            logging.error(e)
