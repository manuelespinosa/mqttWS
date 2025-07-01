# Título del Proyecto (Reemplaza con el título real de tu proyecto)

(Añade aquí una breve descripción de tu proyecto en una o dos frases.)

Este proyecto está configurado para ejecutarse dentro de un contenedor Docker. La contenerización se encarga de clonar el repositorio del proyecto, instalar las dependencias y ejecutar la aplicación.

## Prerrequisitos

Antes de comenzar, asegúrate de cumplir con los siguientes requisitos:
*   **Docker**: Necesitas tener Docker instalado en tu sistema. [Guía de Instalación](https://docs.docker.com/get-docker/)
*   **Docker Compose**: Necesitas Docker Compose. Normalmente se incluye con Docker Desktop para Windows y Mac, pero los usuarios de Linux pueden necesitar instalarlo por separado. [Guía de Instalación](https://docs.docker.com/compose/install/)
*   **Git**: Aunque el contenedor se encarga de la clonación, Git es útil para gestionar los archivos de configuración del proyecto (como este README, Dockerfile, etc.) si estás contribuyendo a la configuración.

## Cómo Empezar

Para poner en marcha el proyecto, sigue estos pasos:

1.  **Clona este repositorio de configuración (si aún no lo has hecho):**
    ```bash
    git clone <url_a_este_repositorio_de_configuracion>
    cd <directorio_del_repositorio_de_configuracion>
    ```

2.  **Crea un archivo `.env`:**
    En el directorio raíz de esta configuración (junto a `docker-compose.yml`), crea un archivo llamado `.env`. Este archivo almacenará tus credenciales sensibles y configuración. Añade el siguiente contenido, reemplazando los valores de ejemplo con tus datos reales:

    ```env
    GITHUB_API_KEY=tu_token_de_acceso_personal_de_github
    REPO_URL=https://github.com/tu_usuario/tu_repositorio_del_proyecto.git
    ```
    *   `GITHUB_API_KEY`: Un Token de Acceso Personal (PAT) de GitHub con permisos para clonar el repositorio de destino. El script `entrypoint.sh` dentro del contenedor Docker lo utiliza para clonar/actualizar el código de tu proyecto privado. [Crear un PAT](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
    *   `REPO_URL`: La URL HTTPS del repositorio Git que contiene el código de tu aplicación. Para este proyecto, será `https://github.com/manuelespinosa/mqttWS.git`.

3.  **Construye y ejecuta la aplicación usando Docker Compose:**
    Abre tu terminal en el directorio que contiene el archivo `docker-compose.yml` y ejecuta:
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: Esta opción le indica a Docker Compose que construya la imagen antes de iniciar el contenedor. Deberías usarla la primera vez o cuando hayas realizado cambios en el `Dockerfile` o `entrypoint.sh`.
    *   `-d`: Esta opción ejecuta los contenedores en modo detached (en segundo plano).

4.  **Accediendo a la aplicación:**
    (Añade aquí instrucciones sobre cómo acceder a tu aplicación. Por ejemplo, si es un servidor web, especifica el puerto, ej.: `Abre tu navegador y navega a http://localhost:8000`). Si es un script que procesa datos, explica cómo verificar su salida o logs.

    Para ver los logs del contenedor en ejecución:
    ```bash
    docker-compose logs -f app
    ```

## Cómo Funciona

*   **`Dockerfile`**: Define el entorno para tu aplicación. Comienza desde una imagen base de Python, instala `git`, y configura un script `entrypoint.sh` para gestionar el código de la aplicación.
*   **`entrypoint.sh`**: Este script se ejecuta cada vez que se inicia el contenedor.
    *   Comprueba si el código de la aplicación desde `REPO_URL` está presente en el directorio `/app`.
    *   Si no está presente, clona el repositorio usando tu `GITHUB_API_KEY`.
    *   Si está presente, intenta obtener los últimos cambios (`git pull`).
    *   Luego instala/actualiza las dependencias de Python desde un archivo `requirements.txt` (se espera que esté en tu repositorio de aplicación clonado).
    *   Finalmente, ejecuta el comando principal de la aplicación (por defecto es `python main.py`).
*   **`docker-compose.yml`**: Orquesta la construcción y ejecución del contenedor Docker.
    *   Construye la imagen usando el `Dockerfile`.
    *   Pasa `GITHUB_API_KEY` y `REPO_URL` del archivo `.env` como variables de entorno al contenedor.
    *   Utiliza un **bind mount** para mapear el directorio `./app` en tu máquina anfitriona al directorio `/app` dentro del contenedor. Esto significa que:
        *   El código clonado por `entrypoint.sh` dentro del contenedor aparecerá en el directorio `./app` en tu anfitrión.
        *   Cualquier cambio que hagas al código en `./app` en tu anfitrión se reflejará dentro del contenedor (aunque para Python, podría ser necesario reiniciar el proceso de la aplicación dentro del contenedor para que los cambios surtan efecto, a menos que tu aplicación se recargue automáticamente).
        *   El código persiste en tu anfitrión incluso si el contenedor se detiene o se elimina.
*   **Directorio `./app`**: Este directorio se crea en tu máquina anfitriona (si no existe) cuando se ejecuta `docker-compose up`. El script `entrypoint.sh` clonará/actualizará el código de tu aplicación en este directorio (a través del bind mount a `/app` en el contenedor).

## Estructura del Proyecto (de esta configuración)

```
.
├── .env                # Almacena tu API key y la URL del repo (tú lo creas)
├── Dockerfile          # Instrucciones para construir la imagen Docker
├── docker-compose.yml  # Define cómo ejecutar el contenedor Docker
├── entrypoint.sh       # Script para clonar/actualizar el repo y ejecutar la app
├── README.md           # Este archivo
└── app/                # Este directorio se creará y poblará con el código
                        # de tu aplicación cuando el contenedor se inicie.
```

## Detener la Aplicación

Para detener la aplicación y eliminar los contenedores, ejecuta:
```bash
docker-compose down
```
Si también deseas eliminar el volumen (que en esta configuración significa principalmente el código en `./app` si no quieres conservarlo, aunque el bind mount significa que está en tu sistema anfitrión de todos modos), puedes añadir la opción `-v`:
```bash
docker-compose down -v
```
Sin embargo, dado que `./app` es un bind mount desde tu anfitrión, `docker-compose down -v` no eliminará el directorio `./app` en tu anfitrión. Deberías eliminarlo manualmente si lo deseas.

## Personalización Adicional

*   **Comando de la Aplicación**: El comando por defecto para ejecutar tu aplicación es `python main.py` (definido como `CMD` en el `Dockerfile`). Si tu aplicación necesita un comando diferente, puedes:
    *   Modificar la línea `CMD` en el `Dockerfile` y reconstruir la imagen (`docker-compose up --build -d`).
    *   Sobrescribir el comando en `docker-compose.yml` añadiendo/descomentando una directiva `command:` bajo el servicio `app`.
*   **Puertos**: Si tu aplicación escucha en un puerto de red (por ejemplo, un servidor web), descomenta y ajusta la sección `ports` en `docker-compose.yml`.
*   **Versión de Python**: Para cambiar la versión de Python, modifica la línea `FROM` en el `Dockerfile` para usar una etiqueta de imagen de Python diferente (por ejemplo, `python:3.8-slim`, `python:3.10`) y reconstruye.
*   **Dependencias del Sistema**: Si tu aplicación requiere bibliotecas de sistema adicionales, añade su instalación a la línea `RUN apt-get update && apt-get install -y ...` en el `Dockerfile` y reconstruye.

(Añade cualquier otra sección relevante, ej.: Contribuciones, Licencia, Solución de Problemas)
```
