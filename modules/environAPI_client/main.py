from environClient import APIClass, Utils
import json
from random import randint
import inspect


def lineno():
    return inspect.currentframe().f_back.f_back.f_lineno


def wait_msg():
    input(f"Estoy en la línea Nº: {lineno()} Pulsa Enter para continuar")

# Inicialización del objeto/instancia


cliente = APIClass()


utils = Utils()

""" Zona de depuración """




""" Fin de la zona de depuración """


# Documentación de datos
doc = cliente.doc()

lista_datos = {"datos": []}
cliente.send_station_data(lista_datos)
utils.notify("Esta es una magnífica herramienta para informar de errores ;)")
""" Fin de la zona de depuración """






print("\nEjemplo del TIPO/estandar dato:")
print(json.dumps(doc.dato(), indent=2))

print("\nEjemplo del TIPO lista_datos")
print(json.dumps(doc.lista_datos(), indent=2))


## Ejemplos de datos
# Ejemplo de creación de un tipo dato con valores específicos
print("\n\nCreación tipos datos con valores específicos:")
print(cliente.dato(1, 2, 3, '2020-04-04 01:28:27'))
print(cliente.dato(1, 2, 3, '2020-04-04 01:28:27'))



# Ejemplo de creación de listas de datos con valores
lista_datos = {"datos": []}  # Esta seguramente me la vas a cuestionar, pero tiene sus razones. Creo que esta documentación está lo suficientemente cuidada como para cagarla en un detalle así sin querer
for idx in range(1, 10):  # Por generar unos datos aleatorios
    dato = cliente.dato(dev_id=idx, var_name="PRES", value=randint(950, 1060), ts='2020-04-04 01:28:27')
    lista_datos["datos"].append(dato)


print("\n\nEjemplo de lista de datos:")
print(lista_datos)


# Insertar datos en una estación
print("\n\nPara recibir los códigos de las estaciones debes llamar a la funcion 'send_station_data(station_data=lista_datos)'")
respuesta = cliente.send_station_data(station_data=lista_datos)
if respuesta["status_code"] == 201:
    print("\nInserción correcta de los datos salvo por los siguientes:\n")
    print(json.dumps(respuesta["errors"], indent=2))
else:
    print(respuesta.status_code)


# Recibir codigos de las estaciones cliente.get_codigos_estaciones(network_name)
print("\n\nPara recibir los códigos de las estaciones debes llamar a la funcion 'get_codigos_estaciones()'")
print(json.dumps(cliente.get_codigos_estaciones('TIC168'), indent=2))
# print(json.dumps(cliente.get_codigos_estaciones('AEMET'), indent=2))
# print(json.dumps(cliente.get_codigos_estaciones('Rediam'), indent=2))
# print(json.dumps(cliente.get_codigos_estaciones('Puertos'), indent=2))
# print(json.dumps(cliente.get_codigos_estaciones('SAIHHidrosur'), indent=2))



# Recibir informacion de las variables disponibles
respuesta = cliente.get_variables()
if respuesta["status_code"]== 200:
    print(respuesta["variables"])


## Obtener información de las estaciones que se han obtenido recientemente
respuesta = cliente.get_estaciones_recientes()
print(respuesta["recent_devs"])


## Obtener información de datos horarios. Obtiene datos más reciente desde la hora anterior a la indicada hasta la hora indicada (+2 minutos)
r = cliente.get_datos_horarios("2020-03-10 15:00:00")
print(r)


## Obtener los datos más recientes de las estaciones. Los ultimos datos dentro del periodo de 2 dias
r = cliente.get_datos_recientes()
print(r)

