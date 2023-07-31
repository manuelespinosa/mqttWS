from modules.environAPI_client.environClient import APIClass
import logging
import json
from datetime import datetime
import os

cliente = APIClass()

# Obtener una instancia del logger configurado
logger = logging.getLogger()

class IFAPAMetos:
    def __init__(self, client):
        self.client = client
        self.client.subscribe("IFAPAMetos/+/json")
        self.client.on_connect = self.on_connect
        #self.client.on_message = self.on_message
        self.client.message_callback_add("IFAPAMetos/+/json", self.on_message)
        self.excluded_vars = ['ts', 'Solar Panel', 'Battery', 'HC Serial Number', 'Dew Point', 'VPD',
                              'DeltaT', 'EAG Soil moisture 1',  'EAG Soil moisture 2',  'EAG Soil moisture 3',
                               'EAG Soil moisture 4',  'EAG Soil moisture 5',  'EAG Soil moisture 6',
                              'EAG Soil moisture 7',  'EAG Soil moisture 8',  'EAG Soil moisture 9',
                              'Volumetric Ionic Content 1', 'Volumetric Ionic Content 2', 'Volumetric Ionic Content 3',
                              'Volumetric Ionic Content 4', 'Volumetric Ionic Content 5', 'Volumetric Ionic Content 6',
                              'Volumetric Ionic Content 7', 'Volumetric Ionic Content 8', 'Volumetric Ionic Content 9',
                              'Soil temperature 1', 'Soil temperature 2', 'Soil temperature 3', 'Soil temperature 4',
                              'Soil temperature 5', 'Soil temperature 6', 'Soil temperature 7', 'Soil temperature 8',
                              'Soil temperature 9']

        respuesta = cliente.get_codigos_estaciones("IFAPA")
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
            logger.info("IFAPA Metos WS processor connected")
        else:
            logger.error("Failed to connect IFAPA Metos WS processor, return code %d\n", rc)

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
            now = str(datetime.fromtimestamp(data['ts']))
            logger.info(f"############### Procesando IFAPA Metos {staID} ###############")
            for k, v in data.items():
                if k in self.excluded_vars:
                    continue
                if 'Barometer' == k:
                    logger.debug(f"{staID}: Pressión atmosférica {v}")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PRES', value=v, ts=now))
                elif 'HC Air temperature' == k:
                    logger.debug(f"{staID}: Temperatura {v} C")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='TC', value=round(v,1), ts=now))
                elif 'HC Relative humidity' == k:
                    logger.debug(f"{staID}: RH {v} %")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='HUM', value=v, ts=now))
                elif 'U-sonic wind speed' == k or 'Wind speed' == k:
                    logger.debug(f"{staID}: ANE {v} m/s")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='ANE', value=round(float(v), 2), ts=now))
                elif 'U-sonic wind dir' == k:
                    logger.debug(f"{staID}: WD {v} º")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='WV', value=v, ts=now))
                elif 'Solar radiation' == k:
                    logger.debug(f"{staID}: RH {v} W/m2")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='GHI', value=v, ts=now))
                else:
                    logger.info(f"Variable no procesada {k} con valor {v}")

            if len(datos) > 0:
                lista_datos = {"datos": datos}
                if not 'DEBUG' in os.environ:
                    respuesta = cliente.send_station_data(lista_datos)
                    logger.info(f"{staID}: {respuesta}")
                logger.info("################# FIN DEL PROCESAMIENTO #####################")
        except Exception as e:
            logging.error(e)