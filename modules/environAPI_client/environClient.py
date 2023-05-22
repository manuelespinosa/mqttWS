import requests
import json


class APIClass:

    def __init__(self):
        self.server = 'http://150.214.77.211:5000'

    def send_station_data(self, station_data=''):
        post_response = self.__post__(endpoint='/api/v1/estacion/datos', obj=station_data)
        response = self.__parse_response(post_response)
        return response

    def send_historic_station_data(self, station_data=''):
        post_response = self.__post__(endpoint='/api/v1/estacion/datos_historicos', obj=station_data)
        response = self.__parse_response(post_response)
        return response

    def get_codigos_estaciones(self, network_name):
        endpoint = '/api/v1/estacion/'+str(network_name)+'/ids_codigos'
        return self.__get__(endpoint)

    def dato(self, dev_id, var_name, value, ts):
        dato = {"dev_id": dev_id, "var_name": var_name, "value": value, "ts": ts}
        return dato

    def get_variables(self):
        endpoint = '/api/v1/variables'
        return self.__get__(endpoint)

    def get_datos_recientes(self):
        endpoint = '/api/v1/datos/recientes'
        return self.__get__(endpoint)

    def get_datos_horarios(self, time_interval):
        endpoint = '/api/v1/datos/horarios'
        return self.__get__(endpoint, {'time_interval': time_interval})

    def get_estaciones_recientes(self):
        endpoint = '/api/v1/estacion/recientes'
        return self.__get__(endpoint)

    def get_datos_variable_estacion_entre_fechas(self, station_id, var_name, from_utc=None, to_utc=None, delta=None):
        endpoint = '/api/v1/datos/estacion/last'
        params = {'station_id': station_id,
                  'var_name': var_name,
                  'from_utc': from_utc,
                  'to_utc': to_utc,
                  'delta': delta}
        return self.__get__(endpoint, params)

    """
        DOCUMENTACION
    """
    class doc:

        def dato(self):
            dato = {"dev_id": "OBLIGATORIO. STRING O ENTERO: id de la base de datos del dispositivo",
                    "var_name": "OBLIGATORIO. STRING: nombre CORTO de la variable, según base de datos",
                    "value": "OBLIGATORIO. valor de la variable medida, en unidades descritas en la base de datos",
                    "ts": "OBLIGATORIO. Datetime o String entendible por la base de datos: TimeStamp en UTC del dato"}
            return dato

        def lista_datos(self):
            cl = APIClass()
            datos = {"datos":   [
                                    cl.dato("dev_id1", "var_name1", "value1", '2020-04-04 01:28:27'),
                                    cl.dato(163, "TC", "17", '2020-04-04 01:28:27'),
                                    cl.dato(162, "TC", "22.5", "2020-04-04 01:29:05")
                                ]
                    }
            return datos

    """
        FUNCTIONES INTERNAS DEL CLIENTE DE LA API
    """
    def __post__(self, endpoint, obj):
        r = requests.post(self.server+endpoint, data=json.dumps(obj))
        return r

    def __get__(self, endpoint, params={}):
        """
        :param endpoint: URL de la api
        :return: json con el contenido si hay respuesta del servidor, r.status_code del request en caso de error
        """
        r = requests.get(url=self.server + endpoint, params=params)
        """
        if r.status_code == 200:
            return json.loads(r.content)
        else:
            return r.status_code
        """
        respuesta = self.__parse_response(post_response=r)
        return respuesta

    def __parse_response(self, post_response):
        response = json.loads(post_response.content)
        response["status_code"] = post_response.status_code
        return response


class Utils:
    def __init__(self, NOTIFY_ENDPOINT="https://notify.run/LMbwGdYzjXegSZOd"):
        self.NOTIFY_ENDPOINT = NOTIFY_ENDPOINT

    def notify(self, message):
        payload = message
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.request("POST", self.NOTIFY_ENDPOINT, headers=headers, data=payload)
        # print(response.text.encode('utf8'))
