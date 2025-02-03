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
        self.client.subscribe("WS/+/jsonts")
        #self.client.on_connect = self.on_connect
        #self.client.on_message = self.on_message
        self.client.message_callback_add("WS/+/json", self.on_message)
        self.client.message_callback_add("WS/+/jsonts", self.on_message)
        self.excluded_vars = ['RainRate', 'MonthRain', 'WindSpeed', 'AvgWindSpeed2',
                              'BatteryStatus', 'BatteryVoltage', 'unsentRain', 'ts']

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
        try:
            payload = msg.payload.decode()
        except Exception as e:
            logger.error(f"Problema decodificando mensaje: {msg}")
            logger.error(str(e))
        topic = msg.topic
        logger.debug(f"Received `{payload}` from `{topic}` topic")
        try:
            staID = topic.split('/')[1]
            if staID not in self.dict_estaciones.keys():
                logger.info(f"La estación {staID} no está en la base de datos. Ignorando.")
                return -1

            data = json.loads(str(payload))
            datos = []
            if 'ts' in data.keys():
                ts =str(datetime.utcfromtimestamp(data['ts']))
            else:
                ts = str(datetime.utcnow())
            logger.debug(f"Current frame ts: {ts}")
            logger.info(f"############### Procesando moddedHopu {staID} ###############")
            for k, v in data.items():
                if k in self.excluded_vars:
                    continue
                if 'Barometer' == k:
                    logger.debug(f"{staID}: Pressión atmosférica {v}")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PRES', value=v, ts=ts))
                elif 'Temperature' == k:
                    logger.debug(f"{staID}: Temperatura {v} C")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='TC', value=round(v,1), ts=ts))
                elif 'RH' == k:
                    logger.debug(f"{staID}: RH {v} %")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='HUM', value=v, ts=ts))
                elif 'AvgWindSpeed10' == k or 'AvgWindSpeed' == k:
                    logger.debug(f"{staID}: ANE {v} m/s")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='ANE', value=round(float(v), 2), ts=ts))
                elif 'WindDirection' == k:
                    logger.debug(f"{staID}: WD {v} º")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='WV', value=v, ts=ts))
                elif 'SolarRadiation' == k and not 'GHImean' in data.keys():  # or 'GHImean' == k:
                    logger.debug(f"{staID}: GHI {v} W/m2")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='GHI', value=v, ts=ts))
                elif 'GHImean' == k:
                    logger.debug(f"{staID}: GHImean {v} W/m2")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='GHI', value=v, ts=ts))
                elif 'GHImax' == k:
                    logger.debug(f"{staID}: GHImax {v} W/m2")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='GHImax', value=v, ts=ts))
                elif 'GHImin' == k:
                    logger.debug(f"{staID}: GHImin {v} W/m2")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='GHImin', value=v, ts=ts))
                elif 'UV' == k:
                    logger.debug(f"{staID}: UV {v}")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='UV', value=v, ts=ts))
                elif 'WindGust' == k:
                    logger.debug(f"{staID}: WindGust {v} m/s")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='ANEmax', value=round(float(v),2), ts=ts))
                elif 'WindGustDirection' == k:
                    logger.debug(f"{staID}: WindGust Direction {v} º")
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='WVmax', value=v, ts=ts))
                elif 'fogClicks' == k:
                    logger.debug((f"{staID}: Precipitación Horizozntal"))
                    """
                    # Cargar datos desde el archivo JSON
                    try:
                        with open("./moddedHopu.json", "r") as archivo:
                            datos_moddedHopu = json.load(archivo)
                    except Exception as e:
                        logger.exception(e)
                        datos_moddedHopu = dict()

                    if staID in datos_moddedHopu.keys():
                        total_hplv = datos_moddedHopu[staID]['HPLV']
                        if total_hplv > v:
                            if v < 15:
                                hplv_diff = v
                            else:
                                hplv_diff = 0
                        else:
                            hplv_diff = v - total_hplv
                    else:
                        datos_moddedHopu[staID] = {}
                        hplv_diff = 0

                    datos_moddedHopu[staID]['HPLV'] = v
                    with open('./moddedHopu.json', 'w') as archivo:
                        json.dump(datos_moddedHopu, archivo)
                    
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='HPLV', value=hplv_diff*0.075, ts=ts))
                    """
                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='HPLV', value=v/0.28*0.075,
                                     ts=ts))

                elif 'YearRain' == k:
                    logger.debug(f"{staID}: Year Rain {v} mm")
                    # Cargar datos desde el archivo JSON
                    try:
                        with open("./moddedHopu.json", "r") as archivo:
                            datos_moddedHopu = json.load(archivo)
                    except Exception as e:
                        logger.exception(e)
                        datos_moddedHopu = dict()

                    if staID in datos_moddedHopu.keys():
                        year_rain = datos_moddedHopu[staID]['YearRain']

                        if year_rain > v:
                            if v < 15:
                                year_rain_diff = v
                            else:
                                year_rain_diff = 0
                        else:
                            year_rain_diff = v - year_rain

                    else:
                        datos_moddedHopu[staID] = {}
                        year_rain_diff = 0

                    datos_moddedHopu[staID]['YearRain'] = v
                    with open('./moddedHopu.json', 'w') as archivo:
                        json.dump(datos_moddedHopu, archivo)

                    datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PLV1', value=year_rain_diff, ts=ts))

                if 'YearRain' not in data.keys() and 'unsentRain' in data.keys():
                    v = data['unsentRain']
                    logger.debug(f"{staID}: Precipitation no enviada {v} mm2")
                    if v < 35:
                        datos.append(cliente.dato(dev_id=self.dict_estaciones[staID], var_name='PLV1', value=v, ts=ts))
                        logger.debug(f"{staID}: Precitación (no enviada) {v} mm/m2")
                    else:
                        logger.warning(f"{staID} informa de una precipitación anómala ({v} mm/m2)")


                else:
                    if k not in self.unprocessed_vars:
                        self.unprocessed_vars.append(k)
                        logger.info(f"Variables no procesadas: {self.unprocessed_vars}")



            if len(datos) > 0:
                lista_datos = {"datos": datos}
                if not 'DEBUG' in os.environ:
                    respuesta = cliente.send_station_data(lista_datos)
                    logger.info(f"{staID}: {respuesta}")
                logger.info("################# FIN DEL PROCESAMIENTO #####################")
        except Exception as e:
            logging.error(e)
